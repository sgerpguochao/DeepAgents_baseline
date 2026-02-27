"""
E2BBackend - E2B 沙箱后端实现

该模块提供了 E2B 沙箱后端的实现，用于 DeepAgents 项目。
E2B (Environment To Be) 是一个专为 AI 智能体设计的云端安全执行环境。

参考: DeepAgents_baseline.ipynb 中的 E2BBackend 实现
"""

import os
import sys
from typing import Any, Optional, Union, Dict, List, Tuple

# 尝试从 deepagents 导入所需的协议类
try:
    from deepagents.backends.protocol import (
        ExecuteResponse,
        FileDownloadResponse,
        FileUploadResponse,
    )
    from deepagents.backends.sandbox import BaseSandbox
    DEPENDENCY_AVAILABLE = True
except ImportError:
    DEPENDENCY_AVAILABLE = False
    # 定义本地响应类（备用）

    class ExecuteResponse:
        """命令执行响应"""
        def __init__(self, output: str, exit_code: int = 0, truncated: bool = False):
            self.output = output
            self.exit_code = exit_code
            self.truncated = truncated

    class FileDownloadResponse:
        """文件下载响应"""
        def __init__(self, path: str, content: Optional[bytes] = None, error: Optional[str] = None):
            self.path = path
            self.content = content
            self.error = error

    class FileUploadResponse:
        """文件上传响应"""
        def __init__(self, path: str, error: Optional[str] = None):
            self.path = path
            self.error = error

    class BaseSandbox:
        """基础沙箱类（备用实现）"""
        pass

# 尝试导入 e2b
try:
    from e2b import Sandbox
except ImportError:
    Sandbox = None


class E2BBackend(BaseSandbox):
    """E2B 沙箱后端实现，用于 DeepAgents。

    该后端使用 E2B（https://e2b.dev）提供安全、隔离的执行环境。
    
    参考 DeepAgents_baseline.ipynb 中的实现:
    - 继承自 BaseSandbox
    - 使用 e2b.Sandbox.create() 创建沙箱
    - 实现 execute, upload_files, download_files 方法

    使用方法:
        from e2b_backend import E2BBackend

        backend = E2BBackend(template="base")
        result = backend.execute("ls -la")
        print(result.output)
        backend.close()
    """

    def __init__(
        self,
        template: str = "base",
        api_key: Optional[str] = None,
        timeout: Optional[int] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        """初始化 E2B 沙箱。

        参数:
            template: E2B 沙箱模板 ID（默认："base"）
                     可选值: "base", "python-3.11", "nodejs-18" 等
            api_key: E2B API 密钥（可选，默认使用 E2B_API_KEY 环境变量）
            timeout: 沙箱超时时间（秒），默认 60 秒
            metadata: 自定义沙箱元数据
        """
        if Sandbox is None:
            raise ImportError(
                "e2b package is not installed. "
                "Please install it with `pip install e2b`."
            )

        # 如果没有提供 api_key，尝试从环境变量获取
        if api_key is None:
            api_key = os.getenv("E2B_API_KEY")

        self.sandbox = Sandbox.create(
            template=template,
            api_key=api_key,
            timeout=timeout,
            metadata=metadata,
        )

    @property
    def id(self) -> str:
        """获取沙箱的唯一标识符"""
        return self.sandbox.sandbox_id

    def execute(self, command: str) -> ExecuteResponse:
        """在沙箱中执行命令

        参数:
            command: 要执行的命令

        返回:
            ExecuteResponse: 包含输出、退出码和截断标志
        """
        try:
            # E2B commands.run 返回 CommandResult，包含 stdout, stderr, exit_code
            result = self.sandbox.commands.run(command)

            # 返回执行结果
            return ExecuteResponse(
                output=result.stdout + result.stderr,
                exit_code=result.exit_code,
                truncated=False,
            )
        except Exception as e:
            return ExecuteResponse(
                output=f"Error executing command: {str(e)}",
                exit_code=1,
                truncated=False,
            )

    def upload_files(self, files: List[Tuple[str, bytes]]) -> List[FileUploadResponse]:
        """上传多个文件到沙箱

        参数:
            files: 文件列表，每个元素为 (路径, 内容) 元组

        返回:
            List[FileUploadResponse]: 上传结果列表
        """
        responses = []
        for path, content in files:
            try:
                # 确保目录存在
                parent_dir = path.rsplit("/", 1)[0]
                if parent_dir:
                    self.sandbox.commands.run(f"mkdir -p {parent_dir}")

                # 写入文件
                if isinstance(content, str):
                    content = content.encode("utf-8")
                self.sandbox.files.write(path, content)
                responses.append(FileUploadResponse(path=path, error=None))
            except Exception as e:
                error_msg = str(e).lower()
                error = "invalid_path"
                if "permission" in error_msg:
                    error = "permission_denied"

                responses.append(FileUploadResponse(path=path, error=error))
        return responses

    def download_files(self, paths: List[str]) -> List[FileDownloadResponse]:
        """从沙箱下载多个文件

        参数:
            paths: 要下载的文件路径列表

        返回:
            List[FileDownloadResponse]: 下载结果列表
        """
        responses = []
        for path in paths:
            try:
                content = self.sandbox.files.read(path)
                # 确保内容是 bytes
                if isinstance(content, str):
                    content = content.encode("utf-8")

                responses.append(FileDownloadResponse(path=path, content=content, error=None))
            except Exception as e:
                error_msg = str(e).lower()
                error = "invalid_path"
                if "not found" in error_msg:
                    error = "file_not_found"
                elif "directory" in error_msg:
                    error = "is_directory"
                elif "permission" in error_msg:
                    error = "permission_denied"

                responses.append(FileDownloadResponse(path=path, content=None, error=error))
        return responses

    def read_file(self, path: str) -> str:
        """读取沙箱中的文件内容

        参数:
            path: 文件路径

        返回:
            str: 文件内容
        """
        content = self.sandbox.files.read(path)
        return content if isinstance(content, str) else content.decode("utf-8")

    def write_file(self, path: str, content: Union[str, bytes]) -> bool:
        """写入文件到沙箱

        参数:
            path: 文件路径
            content: 文件内容

        返回:
            bool: 是否写入成功
        """
        try:
            if isinstance(content, str):
                content = content.encode("utf-8")
            # 确保目录存在
            parent_dir = path.rsplit("/", 1)[0]
            if parent_dir:
                self.sandbox.commands.run(f"mkdir -p {parent_dir}")
            self.sandbox.files.write(path, content)
            return True
        except Exception:
            return False

    def list_files(self, path: str = "/home/user") -> List[str]:
        """列出目录中的文件

        参数:
            path: 目录路径

       返回:
            List[str]: 文件列表
        """
        result = self.execute(f"ls -la {path}")
        if result.exit_code == 0:
            lines = result.output.strip().split("\n")
            return [line.split()[-1] for line in lines[1:] if line]
        return []

    def close(self):
        """关闭沙箱会话"""
        self.sandbox.kill()

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()


# 导出主要类
__all__ = ['E2BBackend', 'ExecuteResponse', 'FileDownloadResponse', 'FileUploadResponse']
