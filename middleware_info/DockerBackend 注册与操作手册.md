# DockerBackend 注册与操作手册

## 一、DockerBackend 简介

### 1.1 什么是 DockerBackend？

**DockerBackend** 是为 AI 智能体提供本地 Docker 容器沙箱环境的后端实现。

如果不使用 Docker，Agent 执行的每一条命令（如 `rm -rf`、`pip install`）都会直接发生在您的宿主机（Mac/Windows/Linux）上，这极其危险且环境不可控。

DockerBackend 通过启动一个隔离的 Docker 容器，将 Agent 的所有操作限制在容器内部，确保宿主机安全。

### 1.2 核心作用与优势

#### 1.2.1 安全隔离 (Security & Isolation)

- **作用**：Agent 的所有操作（文件读写、代码执行、系统命令）都被限制在 Docker 容器内部
- **优势**：即使 Agent 产生幻觉执行了恶意代码（如删除系统文件），也只会破坏容器，**您的宿主机毫发无损**
- **自动清理**：演示代码中的 `auto_remove=True` 确保任务结束后容器自动销毁，不留痕迹

#### 1.2.2 环境一致性 (Reproducibility)

- **作用**：代码指定了镜像 `image="python:3.11-slim"`
- **优势**：无论您的电脑安装的是 Python 3.9 还是 3.12，Agent 永远在一个干净、标准的 Python 3.11 环境中运行
- **解决经典问题**：彻底解决"在我的机器上能跑"的依赖问题

#### 1.2.3 生命周期管理 (Lifecycle Management)

- **作用**：DockerBackend 自动处理容器的 **启动 → 连接 → 执行 → 销毁** 全过程
- **优势**：开发者无需手动编写复杂的 Docker 命令，像使用本地对象一样简单地调用 `backend.execute()` 或 `backend.write_file()`

### 1.3 适用场景

| 场景类型 | 说明 | 典型案例 |
|---------|------|---------|
| **代码执行和测试** | 运行用户提交的代码 | 在线编程评测系统 |
| **依赖安装和环境配置** | 安装 Python 包、系统工具 | 自动化开发环境搭建 |
| **危险操作** | 文件删除、系统命令 | 安全测试、渗透测试 |
| **多租户隔离** | 为不同用户提供独立环境 | SaaS 应用、在线教育平台 |
| **本地开发调试** | 快速测试不同环境 | 跨平台应用测试 |

---

## 二、环境准备与注册

### 2.1 安装 Docker

#### Windows 系统

**步骤 1**：下载 Docker Desktop

访问官网下载：[https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)

**步骤 2**：安装 Docker Desktop

- 双击下载的安装包
- 按照安装向导完成安装
- 安装完成后重启电脑

**步骤 3**：启动 Docker Desktop

- 打开 Docker Desktop 应用
- 首次启动需要接受许可协议
- 等待 Docker 引擎启动完成（底部状态栏显示绿色）

**步骤 4**：验证安装

打开 PowerShell 或命令提示符：

```bash
docker --version
docker run hello-world
```

如果看到欢迎信息，说明 Docker 安装成功。

#### macOS 系统

**步骤 1**：下载 Docker Desktop for Mac

访问官网下载：[https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)

**步骤 2**：安装

- 打开下载的 `.dmg` 文件
- 将 Docker 图标拖拽到 Applications 文件夹
- 在 Applications 中打开 Docker

**步骤 3**：验证安装

打开终端：

```bash
docker --version
docker run hello-world
```

#### Linux 系统 (Ubuntu/Debian)

**步骤 1**：卸载旧版本（如果存在）

```bash
sudo apt-get remove docker docker-engine docker.io containerd runc
```

**步骤 2**：安装依赖

```bash
sudo apt-get update
sudo apt-get install \
    ca-certificates \
    curl \
    gnupg \
    lsb-release
```

**步骤 3**：添加 Docker 官方 GPG 密钥

```bash
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
```

**步骤 4**：设置仓库

```bash
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

**步骤 5**：安装 Docker Engine

```bash
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

**步骤 6**：验证安装

```bash
sudo docker run hello-world
```

**步骤 7**：（可选）将用户添加到 docker 组，避免每次使用 sudo

```bash
sudo usermod -aG docker $USER
newgrp docker
```

### 2.2 配置 Docker 镜像加速（中国大陆用户）

由于 Docker Hub 服务器在海外，中国大陆用户访问较慢，建议配置镜像加速器。

**配置方法**（以阿里云为例）：

**步骤 1**：获取加速器地址

访问阿里云容器镜像服务：[https://cr.console.aliyun.com/](https://cr.console.aliyun.com/)

**步骤 2**：配置 Docker daemon

编辑 `/etc/docker/daemon.json`（Linux）或通过 Docker Desktop 设置（Windows/Mac）：

```json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://registry.docker-cn.com"
  ]
}
```

**步骤 3**：重启 Docker

```bash
# Linux
sudo systemctl daemon-reload
sudo systemctl restart docker

# Windows/Mac: 重启 Docker Desktop
```

### 2.3 验证 Docker 安装

创建测试文件 `test_docker.py`：

```python
import docker

try:
    client = docker.from_env()
    version = client.version()
    print(f"✅ Docker 连接成功")
    print(f"Docker 版本：{version['Version']}")
    
    # 测试运行容器
    result = client.containers.run("hello-world", remove=True)
    print(f"✅ 容器运行成功")
    print(result.decode('utf-8'))
    
except docker.errors.DockerException as e:
    print(f"❌ Docker 未正确安装：{e}")
    print("请确保 Docker Desktop 已启动")
except Exception as e:
    print(f"❌ 错误：{e}")
```

运行测试：

```bash
python test_docker.py
```

---

## 三、安装依赖

### 3.1 安装 Python Docker SDK

```bash
pip install docker
```

### 3.2 验证安装

```python
try:
    import docker
    print(f"✅ docker 包安装成功，版本：{docker.__version__}")
except ImportError:
    print("❌ docker 包未安装，请运行：pip install docker")
```

---

## 四、DockerBackend 实现

### 4.1 完整代码实现

创建文件 `docker_backend.py`：

```python
import io
import tarfile
import time
import uuid
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

class DockerBackend(BaseSandbox):
    """Docker 沙箱后端实现，用于 DeepAgents。

    该后端使用本地 Docker 守护进程提供隔离的执行环境。
    需要安装 `docker` Python 包，并确保 Docker 守护进程正在运行。
    """

    def __init__(
        self,
        image: str = "python:3.11-slim",
        auto_remove: bool = True,
        cpu_quota: int = 50000,  # 50% CPU
        memory_limit: str = "512m",
        network_disabled: bool = False,
        working_dir: str = "/workspace",
        volumes: dict[str, dict[str, str]] | None = None,
    ) -> None:
        """初始化 Docker 沙箱。

        参数:
            image: 使用的 Docker 镜像（默认："python:3.11-slim"）
            auto_remove: 是否在退出时自动移除容器（默认：True）
            cpu_quota: CPU 配额（微秒），默认 50000 表示 50% CPU
            memory_limit: 内存限制（默认："512m"）
            network_disabled: 是否禁用网络（默认：False）
            working_dir: 容器内工作目录（默认："/workspace"）
            volumes: 卷挂载配置（可选）
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
        
        # 卷挂载
        self.volumes = volumes or {}
        
        # 初始化 Docker 客户端
        try:
            self.client = docker.from_env()
        except docker.errors.DockerException as e:
            raise RuntimeError(
                f"无法连接到 Docker 守护进程：{e}\n"
                "请确保 Docker Desktop 已启动"
            )
        
        # 生成唯一容器名
        self.container_name = f"deepagents-{uuid.uuid4().hex[:8]}"
        
        # 启动容器
        self.container = self.client.containers.run(
            image=self.image,
            name=self.container_name,
            command="tail -f /dev/null",  # 保持容器运行
            detach=True,
            auto_remove=auto_remove,
            cpu_quota=cpu_quota,
            mem_limit=memory_limit,
            network_disabled=network_disabled,
            working_dir=working_dir,
            volumes=self.volumes,
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
                
                # 从容器下载文件
                bits, stat = self.container.get_archive(parent_dir)
                
                # 解析 tar 流
                tar_stream = io.BytesIO()
                for chunk in bits:
                    tar_stream.write(chunk)
                tar_stream.seek(0)
                
                # 提取文件
                with tarfile.open(fileobj=tar_stream, mode='r') as tar:
                    # 查找目标文件
                    member = tar.getmember(filename)
                    file_content = tar.extractfile(member).read()
                
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
        """Close the sandbox session."""
        try:
            # 停止容器
            self.container.stop(timeout=5)
            # 容器会在 auto_remove=True 时自动删除
        except Exception:
            pass  # 忽略清理过程中的错误
```

---

## 五、使用示例

### 5.1 基础使用示例

```python
import os
from dotenv import load_dotenv
from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI
from docker_backend import DockerBackend

load_dotenv(override=True)

def run_docker_demo():
    print("\n" + "="*80)
    print("DeepAgents DockerBackend 演示")
    print("="*80)

    # 1. 初始化模型
    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    # 2. 配置 DockerBackend
    print("🐳 正在初始化 Docker 容器 (Image: python:3.11-slim)...")
    try:
        backend = DockerBackend(
            image="python:3.11-slim",
            volumes={"./workspace": {"bind": "/workspace", "mode": "rw"}}
        )
        print(f"✅ 容器已启动 (ID: {backend.id[:12]})")
    except Exception as e:
        print(f"❌ 容器启动失败：{e}")
        return

    try:
        # 3. 创建 Agent
        agent = create_deep_agent(
            model=llm,
            backend=backend,
            system_prompt="""你是一个在 Docker 容器中工作的 Python 开发助手。
            
请按以下步骤工作：
1. 首先使用 write_file 创建 Python 文件
2. 使用 execute 运行 Python 脚本
3. 如果遇到依赖缺失，使用 pip install 安装
4. 将结果保存到 /workspace 目录
"""
        )

        # 4. 执行任务
        config = {"configurable": {"thread_id": "docker_demo"}}

        task = """请完成以下任务：

1. 创建一个 Python 脚本 factorial.py，计算 10 的阶乘
2. 执行该脚本
3. 将结果保存到 /workspace/result.txt
"""

        print("\n📋 执行任务...")
        result = agent.invoke({
            "messages": [("user", task)]
        }, config=config)

        print("\n" + "="*80)
        print("📊 执行结果")
        print("="*80)
        print(result["messages"][-1].content)

        # 5. 检查生成的文件
        print("\n📁 生成的文件:")
        workspace_dir = "./workspace"
        if os.path.exists(workspace_dir):
            for f in os.listdir(workspace_dir):
                print(f"  - {f}")

    except Exception as e:
        print(f"❌ 运行时错误：{e}")
        import traceback
        traceback.print_exc()
    finally:
        # 6. 清理资源
        print("\n🧹 正在关闭并销毁容器...")
        backend.close()
        print("✅ 容器已销毁")
        print("演示结束")

if __name__ == "__main__":
    run_docker_demo()
```

### 5.2 输出示例

```
================================================================================
DeepAgents DockerBackend 演示
================================================================================
🐳 正在初始化 Docker 容器 (Image: python:3.11-slim)...
✅ 容器已启动 (ID: a1b2c3d4e5f6)

📋 执行任务...

[Agent (model)]
----------------------------------------
任务完成！以下是执行步骤：

1. **创建 factorial.py 脚本**：
```python
def factorial(n):
    if n == 0 or n == 1:
        return 1
    return n * factorial(n - 1)

result = factorial(10)
print(f"10 的阶乘是：{result}")

# 保存结果
with open('/workspace/result.txt', 'w') as f:
    f.write(f"10! = {result}\n")
```

2. **执行脚本**：
```bash
python factorial.py
```

3. **结果**：
10 的阶乘是：3628800

结果已保存到 /workspace/result.txt
----------------------------------------

📁 生成的文件:
  - factorial.py
  - result.txt

🧹 正在关闭并销毁容器...
✅ 容器已销毁
演示结束
```

---

## 六、高级配置

### 6.1 自定义 Docker 镜像

```python
# 使用不同的 Python 版本
backend = DockerBackend(image="python:3.9-slim")
backend = DockerBackend(image="python:3.10-slim")
backend = DockerBackend(image="python:3.12-bookworm")

# 使用 Node.js 环境
backend = DockerBackend(image="node:18-alpine")

# 使用自定义镜像
backend = DockerBackend(image="my-custom-image:latest")
```

### 6.2 资源限制

```python
# 限制 CPU 和内存
backend = DockerBackend(
    image="python:3.11-slim",
    cpu_quota=100000,      # 100% CPU（单个核心）
    memory_limit="1g"      # 1GB 内存
)

# 多核 CPU 限制
backend = DockerBackend(
    cpu_quota=200000,      # 200% CPU（两个核心）
    memory_limit="2g"
)
```

### 6.3 网络配置

```python
# 禁用网络（增强安全性）
backend = DockerBackend(
    image="python:3.11-slim",
    network_disabled=True
)

# 使用自定义网络
backend = DockerBackend(
    image="python:3.11-slim",
    network_mode="bridge"
)

# 使用主机网络（不推荐，安全性降低）
backend = DockerBackend(
    image="python:3.11-slim",
    network_mode="host"
)
```

### 6.4 卷挂载

#### 6.4.1 自动挂载（推荐）

默认情况下，DockerBackend 会自动将项目根目录下的 `./workspace` 文件夹挂载到容器的 `/workspace` 目录。这样容器内创建的文件会自动同步到宿主机的 `./workspace` 目录。

```python
# 默认配置，自动挂载 ./workspace -> /workspace
backend = DockerBackend()  # 等价于 mount_workspace=True
```

如果不需要挂载，可以禁用：

```python
# 禁用自动挂载，容器内文件不同步到宿主机
backend = DockerBackend(mount_workspace=False)
```

#### 6.4.2 手动挂载

```python
# 挂载单个目录
backend = DockerBackend(
    image="python:3.12-slim",
    mount_workspace=False,  # 禁用自动挂载
    volumes={"./workspace": {"bind": "/workspace", "mode": "rw"}}
)

# 挂载多个目录
backend = DockerBackend(
    image="python:3.11-slim",
    volumes={
        "./workspace": {"bind": "/workspace", "mode": "rw"},
        "./data": {"bind": "/data", "mode": "ro"},  # 只读
        "./output": {"bind": "/output", "mode": "rw"}
    }
)

# 使用绝对路径
import os
backend = DockerBackend(
    image="python:3.11-slim",
    volumes={
        os.path.abspath("./workspace"): {
            "bind": "/workspace",
            "mode": "rw"
        }
    }
)
```

### 6.5 环境变量

```python
# 在容器中设置环境变量
backend = DockerBackend(
    image="python:3.11-slim",
    environment={
        "API_KEY": "your-api-key",
        "DEBUG": "true",
        "PYTHONUNBUFFERED": "1"
    }
)
```

---

## 七、与 DeepAgents 集成

### 7.1 完整集成示例

```python
import os
from dotenv import load_dotenv
from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from docker_backend import DockerBackend

load_dotenv(override=True)

async def setup_mcp_tools():
    """连接 Context7 MCP 服务器并获取工具"""
    print("正在连接 Context7 MCP 服务器...")
    try:
        client = MultiServerMCPClient({
            "context7": {
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", "@upstash/context7-mcp@latest"],
            }
        })
        tools = await client.get_tools()
        print(f"✅ 成功加载 {len(tools)} 个 MCP 工具")
        return client, tools
    except Exception as e:
        print(f"❌ 连接 MCP 失败：{e}")
        return None, []

async def run_integrated_demo():
    print("\n" + "="*80)
    print("DeepAgents DockerBackend 完整集成演示")
    print("="*80)

    # 1. 初始化 MCP
    mcp_client, mcp_tools = await setup_mcp_tools()

    # 2. 初始化 Docker Backend
    print("🐳 正在初始化 Docker 容器...")
    backend = DockerBackend(
        image="python:3.11-slim",
        volumes={"./workspace": {"bind": "/workspace", "mode": "rw"}},
        cpu_quota=100000,
        memory_limit="1g"
    )
    print(f"✅ 容器已启动 (ID: {backend.id[:12]})")

    try:
        # 3. 创建 DeepAgent
        llm = ChatOpenAI(model="gpt-4o", temperature=0)

        agent = create_deep_agent(
            model=llm,
            tools=mcp_tools,
            backend=backend,
            system_prompt="""你是一个在 Docker 容器中工作的高级技术助手。
            
你可以：
1. 使用 execute 工具执行任何 Linux 命令
2. 使用 write_file 和 read_file 操作文件
3. 使用 MCP 工具查询最新文档
4. 安装依赖包并运行复杂应用
5. 使用 pip install 安装 Python 包

请确保所有操作都在容器中进行，保持环境整洁。
"""
        )

        # 4. 执行复杂任务
        config = {"configurable": {"thread_id": "docker_integrated_demo"}}

        task = """请完成以下数据分析任务：

1. 安装必要的依赖：numpy, pandas, matplotlib
2. 创建一个 Python 脚本 data_analysis.py，要求：
   - 生成 100 个随机数（正态分布，均值=50，标准差=10）
   - 计算统计信息（均值、中位数、标准差）
   - 绘制直方图并保存为 histogram.png
   - 将结果保存为 report.md
3. 执行脚本并返回结果
4. 将所有生成的文件保存到 /workspace 目录
"""

        print("\n📋 执行任务...")
        result = await agent.ainvoke({
            "messages": [("user", task)]
        }, config=config)

        print("\n" + "="*80)
        print("📊 执行结果")
        print("="*80)
        print(result["messages"][-1].content)

        # 5. 检查生成的文件
        print("\n📁 生成的文件:")
        workspace_dir = "./workspace"
        if os.path.exists(workspace_dir):
            for f in os.listdir(workspace_dir):
                file_size = os.path.getsize(f"{workspace_dir}/{f}")
                print(f"  - {f} ({file_size} bytes)")

    except Exception as e:
        print(f"❌ 运行时错误：{e}")
        import traceback
        traceback.print_exc()
    finally:
        # 6. 清理资源
        print("\n🧹 正在关闭并销毁容器...")
        backend.close()
        print("✅ 容器已销毁")
        print("演示结束")

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_integrated_demo())
```

---

## 八、常见问题与故障排除

### 8.1 Docker 未启动

**问题**：`Error: Cannot connect to the Docker daemon`

**解决方案**：

**Windows/Mac**：
- 启动 Docker Desktop 应用
- 等待底部状态栏变为绿色

**Linux**：
```bash
sudo systemctl start docker
sudo systemctl enable docker  # 开机自启
```

### 8.2 权限错误

**问题**：`Permission denied while trying to connect to the Docker daemon socket`

**解决方案**（Linux）：

```bash
# 将用户添加到 docker 组
sudo usermod -aG docker $USER
newgrp docker

# 验证
docker ps
```

### 8.3 镜像拉取失败

**问题**：`Error: failed to connect to registry: ...`

**解决方案**：

1. 配置 Docker 镜像加速器（见 2.2 节）
2. 手动拉取镜像：
```bash
docker pull python:3.11-slim
```

### 8.4 容器启动失败

**问题**：`Container creation failed`

**可能原因**：
1. 镜像不存在
2. 资源不足
3. 端口冲突

**解决方案**：
```python
# 使用更小的镜像
backend = DockerBackend(image="python:3.11-alpine")

# 减少资源限制
backend = DockerBackend(
    cpu_quota=50000,
    memory_limit="256m"
)
```

### 8.5 文件传输失败

**问题**：上传/下载文件时出错

**解决方案**：
```python
# 确保目录存在
result = backend.execute("mkdir -p /workspace/data")

# 检查文件权限
result = backend.execute("ls -la /workspace/")
print(result.output)

# 使用绝对路径
backend.upload_files([
    ("/workspace/script.py", b"print('hello')")
])
```

### 8.6 内存不足

**问题**：容器因内存不足被杀死

**解决方案**：
```python
# 增加内存限制
backend = DockerBackend(memory_limit="2g")

# 或者使用更轻量的镜像
backend = DockerBackend(image="python:3.11-alpine")
```

---

## 九、最佳实践

### 9.1 资源管理

```python
# 始终使用 try-finally 确保资源清理
backend = DockerBackend()
try:
    # 执行操作
    result = backend.execute("python script.py")
finally:
    backend.close()  # 确保容器关闭

# 或使用上下文管理器（如果实现）
with DockerBackend() as backend:
    result = backend.execute("python script.py")
```

### 9.2 镜像选择

| 镜像 | 大小 | 适用场景 |
|------|------|---------|
| `python:3.11-alpine` | ~50MB | 快速测试、简单脚本 |
| `python:3.11-slim` | ~120MB | 通用场景（推荐） |
| `python:3.11-bookworm` | ~900MB | 需要完整系统工具 |
| `node:18-alpine` | ~170MB | Node.js 应用 |

### 9.3 安全建议

```python
# 1. 禁用网络（如果不需要）
backend = DockerBackend(network_disabled=True)

# 2. 限制资源
backend = DockerBackend(
    cpu_quota=50000,
    memory_limit="512m"
)

# 3. 使用只读挂载
backend = DockerBackend(
    volumes={"./data": {"bind": "/data", "mode": "ro"}}
)

# 4. 避免挂载敏感目录
# ❌ 错误示例
backend = DockerBackend(
    volumes={"/": {"bind": "/host", "mode": "ro"}}  # 危险！
)
```

### 9.4 错误处理

```python
from deepagents.backends.protocol import ExecuteResponse

def safe_execute(backend, command: str) -> ExecuteResponse:
    """安全执行命令"""
    try:
        result = backend.execute(command)
        if result.exit_code != 0:
            print(f"⚠️ 命令执行失败：{command}")
            print(f"错误输出：{result.output}")
        return result
    except Exception as e:
        return ExecuteResponse(
            output=f"异常：{str(e)}",
            exit_code=1
        )
```

---

## 十、Docker Compose 集成

### 10.1 Docker Compose 配置

创建 `docker-compose.yml`：

```yaml
version: '3'

services:
  deepagents:
    image: python:3.11-slim
    container_name: deepagents-worker
    volumes:
      - ./workspace:/workspace
      - ./data:/data:ro
    environment:
      - API_KEY=${API_KEY}
      - DEBUG=true
    cpu_quota: 100000
    mem_limit: 1g
    networks:
      - deepagents-net
    command: tail -f /dev/null

networks:
  deepagents-net:
    driver: bridge
```

### 10.2 使用 Docker Compose

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

---

## 十一、性能优化

### 11.1 镜像预拉取

```bash
# 预先拉取常用镜像，避免首次使用等待
docker pull python:3.11-slim
docker pull python:3.11-alpine
docker pull node:18-alpine
```

### 11.2 自定义镜像

创建 `Dockerfile`：

```dockerfile
FROM python:3.11-slim

# 预装常用依赖
RUN pip install --no-cache-dir \
    numpy \
    pandas \
    matplotlib \
    requests

# 设置工作目录
WORKDIR /workspace

# 创建非 root 用户
RUN useradd -m -u 1000 agent
USER agent

CMD ["tail", "-f", "/dev/null"]
```

构建镜像：

```bash
docker build -t deepagents-custom:latest .
```

使用自定义镜像：

```python
backend = DockerBackend(image="deepagents-custom:latest")
```

---

## 十二、参考资料

- **Docker 官方文档**：[https://docs.docker.com/](https://docs.docker.com/)
- **Docker Python SDK**：[https://docker-py.readthedocs.io/](https://docker-py.readthedocs.io/)
- **DeepAgents 文档**：[https://github.com/langchain-ai/deepagents](https://github.com/langchain-ai/deepagents)
- **Docker Hub**：[https://hub.docker.com/](https://hub.docker.com/)
- **Docker 最佳实践**：[https://docs.docker.com/develop/develop-images/dockerfile_best-practices/](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)

---

## 十三、总结

### 13.1 DockerBackend 核心优势

| 优势 | 说明 |
|------|------|
| **完全隔离** | 容器内操作不影响宿主机 |
| **环境可控** | 指定镜像版本，确保一致性 |
| **支持 execute** | 可执行任意 Shell 命令 |
| **自动清理** | auto_remove 确保无残留 |
| **资源限制** | CPU/内存限制防止资源耗尽 |

### 13.2 使用流程总结

```
1. 安装 Docker → 2. 安装 docker Python 包 → 3. 实现 DockerBackend
       ↓
4. 创建 DeepAgent → 5. 执行任务 → 6. 清理容器
```

### 13.3 与 E2BBackend 对比

| 特性 | DockerBackend | E2BBackend |
|------|---------------|------------|
| **部署位置** | 本地 | 云端 |
| **成本** | 免费 | 按使用量付费 |
| **网络依赖** | 不需要 | 需要 |
| **启动速度** | 快（1-3 秒） | 中等（5-10 秒） |
| **适用场景** | 本地开发、测试 | 生产环境、多租户 |

### 13.4 下一步

- 实践：使用 DockerBackend 构建实际项目
- 深入：自定义 Docker 镜像
- 优化：探索 Docker 高级功能（如网络、卷、编排等）
