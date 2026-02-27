import io
import os
import tarfile
import time
import uuid
from pathlib import Path
from typing import Optional

# 加载 DeepAgents 后端协议
from deepagents.backends.protocol import (
    ExecuteResponse,
    FileDownloadResponse,
    FileUploadResponse,
    SandboxBackendProtocol,
)

# 加载 DeepAgents 基础沙箱类
from deepagents.backends.sandbox import BaseSandbox

try:
    import docker
    from docker.errors import NotFound, APIError
except ImportError:
    docker = None


# 固定的容器名称（用于复用）
CONTAINER_NAME = "deepagents-sandbox"


def _load_image_id_from_env() -> str | None:
    """从 .env 文件加载 PYTHON_IMAGE_ID 配置"""
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        return None

    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("PYTHON_IMAGE_ID="):
                return line.split("=", 1)[1].strip()
    return None


def _check_or_create_image(client, target_image: str = "python:3.12-slim") -> str:
    """检查镜像是否存在，如果不存在则从 .env 中的 IMAGE_ID 创建

    Returns:
        返回实际使用的镜像名称或 ID
    """
    # 从 .env 加载配置的 image ID
    configured_image_id = _load_image_id_from_env()

    try:
        # 尝试用配置的 image ID 查找镜像
        if configured_image_id:
            try:
                image = client.images.get(configured_image_id)
                print(f"✓ 找到已配置的镜像: {configured_image_id[:20]}...")
                return configured_image_id
            except NotFound:
                print(f"⚠ 配置的镜像 {configured_image_id[:20]}... 不存在")

        # 检查 python:3.12-slim 镜像是否存在
        try:
            image = client.images.get(target_image)
            print(f"✓ 找到镜像: {target_image}")
            return target_image
        except NotFound:
            print(f"⚠ 镜像 {target_image} 不存在")

        # 如果配置的 image ID 存在但不在本地，尝试用 ID 创建
        if configured_image_id:
            try:
                # 尝试从配置的 image ID 加载（假设是导出导出的镜像）
                print(f"正在从配置的 IMAGE_ID 导入镜像...")
                # 这里假设 image ID 已经存在，只是需要确认
                return configured_image_id
            except Exception as e:
                print(f"⚠ 无法从 IMAGE_ID 创建镜像: {e}")

        # 返回默认镜像名称，让 Docker 自动拉取
        return target_image

    except Exception as e:
        print(f"⚠ 检查镜像时出错: {e}")
        return target_image


def _find_existing_container(client, container_name: str = CONTAINER_NAME):
    """查找已存在的容器，如果存在且正在运行则返回，否则返回 None

    Args:
        client: Docker 客户端
        container_name: 容器名称

    Returns:
        存在的容器对象或 None
    """
    try:
        container = client.containers.get(container_name)
        if container.status == "running":
            print(f"✓ 复用已有容器: {container_name}")
            return container
        else:
            # 容器存在但未运行，启动它
            print(f"⚠ 容器 {container_name} 存在但未运行，正在启动...")
            container.start()
            time.sleep(1)
            # 重新获取容器状态
            container = client.containers.get(container_name)
            print(f"✓ 容器已启动: {container_name}")
            return container
    except NotFound:
        return None
    except Exception as e:
        print(f"⚠ 查找容器时出错: {e}")
        return None


def _create_new_container(client, actual_image: str, container_name: str, cpu_quota: int,
                          memory_limit: str, network_disabled: bool, working_dir: str,
                          volumes: dict) -> "docker.models.containers.Container":
    """创建新容器

    Args:
        client: Docker 客户端
        actual_image: 使用的镜像
        container_name: 容器名称
        cpu_quota: CPU 配额
        memory_limit: 内存限制
        network_disabled: 是否禁用网络
        working_dir: 工作目录
        volumes: 卷挂载配置

    Returns:
        创建的容器对象
    """
    container = client.containers.run(
        image=actual_image,
        name=container_name,
        command="tail -f /dev/null",  # 保持容器运行
        detach=True,
        auto_remove=False,  # 不自动删除，保留容器
        cpu_quota=cpu_quota,
        mem_limit=memory_limit,
        network_disabled=network_disabled,
        working_dir=working_dir,
        volumes=volumes,
        labels=["deepagents-sandbox"],  # 添加标签便于识别
    )
    print(f"✓ 创建新容器: {container_name}")
    return container


class DockerBackend(BaseSandbox):
    """Docker 沙箱后端实现，用于 DeepAgents。

    该后端使用本地 Docker 守护进程提供隔离的执行环境。
    需要安装 `docker` Python 包，并确保 Docker 守护进程正在运行。
    """

    def __init__(
        self,
        image: str = "python:3.12-slim",
        auto_remove: bool = False,  # 默认不自动删除容器
        cpu_quota: int = 50000,  # 50% CPU
        memory_limit: str = "512m",
        network_disabled: bool = False,
        working_dir: str = "/workspace",
        volumes: dict[str, dict[str, str]] | None = None,
        reuse_container: bool = True,  # 默认复用容器
        mount_workspace: bool = True,  # 默认挂载宿主机 workspace 目录
    ) -> None:
        """初始化 Docker 沙箱。

        参数:
            image: 使用的 Docker 镜像（默认："python:3.12-slim"）
            auto_remove: 是否在退出时自动移除容器（默认：False，保留容器供下次使用）
            cpu_quota: CPU 配额（微秒），默认 50000 表示 50% CPU
            memory_limit: 内存限制（默认："512m"）
            network_disabled: 是否禁用网络（默认：False）
            working_dir: 容器内工作目录（默认："/workspace"）
            volumes: 卷挂载配置（可选）
            reuse_container: 是否复用已有容器（默认：True）
            mount_workspace: 是否挂载宿主机 ./workspace 到容器 /workspace（默认：True）
        """
        if docker is None:
            raise ImportError(
                "docker package is not installed. "
                "Please install it with `pip install docker`."
            )

        self.image = image
        self.auto_remove = auto_remove
        self.working_dir = working_dir

        # 解析内存限制
        self.mem_limit = memory_limit

        # CPU 配额配置
        self.cpu_quota = cpu_quota

        # 网络配置
        self.network_disabled = network_disabled

        # 处理卷挂载
        self.volumes = volumes.copy() if volumes else {}

        # 默认挂载宿主机 workspace 目录
        if mount_workspace:
            project_root = Path(__file__).parent
            host_workspace = str(project_root / "workspace")
            # 确保宿主机目录存在
            os.makedirs(host_workspace, exist_ok=True)
            self.volumes[host_workspace] = {"bind": working_dir, "mode": "rw"}
            print(f"✓ 已挂载宿主机 workspace: {host_workspace} -> {working_dir}")

        # 初始化 Docker 客户端
        try:
            self.client = docker.from_env()
        except docker.errors.DockerException as e:
            raise RuntimeError(
                f"无法连接到 Docker 守护进程：{e}\n"
                "请确保 Docker 已启动"
            )

        # 检查或获取镜像
        actual_image = _check_or_create_image(self.client, image)

        # 容器名称
        self.container_name = CONTAINER_NAME

        # 尝试复用已有容器或创建新容器
        if reuse_container:
            existing_container = _find_existing_container(self.client, self.container_name)
            if existing_container:
                self.container = existing_container
                print(f"✓ 复用容器成功 (ID: {self.container.id[:12]})")
            else:
                # 创建新容器
                self.container = _create_new_container(
                    self.client, actual_image, self.container_name,
                    cpu_quota, memory_limit, network_disabled,
                    working_dir, self.volumes
                )
        else:
            # 不复用，创建新容器（带随机名称）
            self.container_name = f"deepagents-{uuid.uuid4().hex[:8]}"
            self.container = _create_new_container(
                self.client, actual_image, self.container_name,
                cpu_quota, memory_limit, network_disabled,
                working_dir, self.volumes
            )

        # 等待容器完全启动
        time.sleep(0.5)

        # 确保工作目录存在
        self.execute(f"mkdir -p {working_dir}")

    @property
    def id(self) -> str:
        """Unique identifier for the sandbox backend."""
        return self.container.id

    def execute(self, command: str) -> ExecuteResponse:
        """Execute a command in the sandbox."""
        try:
            # 使用 exec_run 执行命令
            result = self.container.exec_run(
                command,
                demux=True,  # 分离 stdout 和 stderr
                workdir=self.working_dir
            )

            # 解析输出
            stdout = result.output[0].decode('utf-8', errors='replace') if result.output[0] else ""
            stderr = result.output[1].decode('utf-8', errors='replace') if result.output[1] else ""

            return ExecuteResponse(
                output=stdout + stderr,
                exit_code=result.exit_code,
                truncated=False,
            )
        except APIError as e:
            return ExecuteResponse(
                output=f"Docker API 错误：{str(e)}",
                exit_code=1,
                truncated=False,
            )
        except Exception as e:
            return ExecuteResponse(
                output=f"执行命令时出错：{str(e)}",
                exit_code=1,
                truncated=False,
            )

    def upload_files(self, files: list[tuple[str, bytes]]) -> list[FileUploadResponse]:
        """Upload multiple files to the sandbox."""
        responses = []

        for path, content in files:
            try:
                # 确保是绝对路径
                if not path.startswith('/'):
                    path = f"{self.working_dir}/{path}"

                # 创建父目录
                parent_dir = path.rsplit('/', 1)[0]
                if parent_dir:
                    self.execute(f"mkdir -p {parent_dir}")

                # 使用 tar 流传输文件
                tar_stream = io.BytesIO()
                with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                    # 创建 TarInfo 对象
                    info = tarfile.TarInfo(name=path.split('/')[-1])
                    info.size = len(content)
                    tar.addfile(info, io.BytesIO(content))

                tar_stream.seek(0)

                # 将文件放入容器
                self.container.put_archive(parent_dir, tar_stream)

                responses.append(FileUploadResponse(path=path, error=None))

            except Exception as e:
                error_msg = str(e).lower()
                error = "invalid_path"
                if "permission" in error_msg:
                    error = "permission_denied"
                elif "no such" in error_msg:
                    error = "file_not_found"

                responses.append(FileUploadResponse(path=path, error=error))

        return responses

    def download_files(self, paths: list[str]) -> list[FileDownloadResponse]:
        """Download multiple files from the sandbox."""
        responses = []

        for path in paths:
            try:
                # 确保是绝对路径
                if not path.startswith('/'):
                    path = f"{self.working_dir}/{path}"

                # 获取文件所在目录和文件名
                parent_dir, filename = path.rsplit('/', 1)

                # 从容器下载文件（get_archive 返回整个目录的 tar 包）
                bits, stat = self.container.get_archive(parent_dir)

                # 解析 tar 流
                tar_stream = io.BytesIO()
                for chunk in bits:
                    tar_stream.write(chunk)
                tar_stream.seek(0)

                # 提取文件
                # Docker get_archive 返回的 tar 包包含 parent_dir 的完整路径（不带前导 /）
                # 例如: parent_dir="/workspace" -> tar 里是 "workspace/filename"
                #       parent_dir="/workspace/testdir" -> tar 里是 "testdir/filename"
                with tarfile.open(fileobj=tar_stream, mode='r') as tar:
                    # tar_path 是 tar 包里的实际路径，从 stat['name'] 获取
                    tar_parent = stat.get('name', '')
                    tar_path = f"{tar_parent}/{filename}"

                    try:
                        member = tar.getmember(tar_path)
                        file_content = tar.extractfile(member).read()
                    except KeyError:
                        # 尝试不带父目录前缀
                        try:
                            member = tar.getmember(filename)
                            file_content = tar.extractfile(member).read()
                        except KeyError:
                            raise FileNotFoundError(f"File not found in tar: {tar_path}")

                responses.append(FileDownloadResponse(
                    path=path,
                    content=file_content,
                    error=None
                ))

            except Exception as e:
                error_msg = str(e).lower()
                error = "invalid_path"
                if "not found" in error_msg or "no such" in error_msg:
                    error = "file_not_found"
                elif "directory" in error_msg:
                    error = "is_directory"
                elif "permission" in error_msg:
                    error = "permission_denied"

                responses.append(FileDownloadResponse(
                    path=path,
                    content=None,
                    error=error
                ))

        return responses

    def close(self):
        """Close the sandbox session.

        注意：此方法不会停止或删除容器，容器会一直保持运行状态。
        容器会在下次创建 DockerBackend 时被复用。
        如果需要停止容器，请使用 docker stop deepagents-sandbox 命令。
        """
        # 不停止容器，保持运行状态
        print(f"✓ 已断开与容器 {self.container_name} 的连接")
        print(f"  容器保持运行状态，文件和数据会被保留")
        pass
