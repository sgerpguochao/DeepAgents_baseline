# E2BBackend 注册与操作手册

## 一、E2B 简介

### 1.1 什么是 E2B？

**E2B (Environment To Be)** 是一个专为 AI 智能体设计的云端安全执行环境。

你可以把它想象成一台**云端电脑**或**远程服务器**，DeepAgents 将其作为"外挂大脑"和"执行手脚"。当 AI 需要写代码、运行脚本或操作文件时，它不会在你的本地机器上操作，而是连接到 E2B 的云端环境中进行。

### 1.2 核心特性

#### 1.2.1 安全性与隔离性 (Security & Isolation)

- **作用**：AI 生成的代码（可能包含错误或恶意逻辑）完全运行在云端沙箱中
- **优势**：绝不会破坏你本地的电脑环境
- **示例**：演示代码中，Agent 即使执行了 `rm -rf /`，也只是删除了云端临时的沙箱，对宿主机毫发无损

#### 1.2.2 持久化会话 (Long-running Sessions)

- **作用**：沙箱可以保持运行状态
- **优势**：Agent 可以先创建一个文件，然后在后续步骤中运行它。环境状态在会话期间是保持的

#### 1.2.3 标准 Linux 环境

- **作用**：提供标准的 Linux Shell
- **优势**：就像在真实的服务器上一样，可执行任何 Linux 命令

### 1.3 适用场景

| 场景类型 | 说明 | 典型案例 |
|---------|------|---------|
| **生产环境部署** | 多租户 SaaS 应用 | 为每个用户提供隔离的执行环境 |
| **代码执行即服务** | 允许用户提交代码并执行 | 在线编程教育平台 |
| **云端弹性计算** | 需要弹性计算资源 | 大规模数据处理 |
| **高风险操作** | 执行不可信的代码 | AI 生成的代码测试 |

---

## 二、注册与 API Key 获取

### 2.1 注册账号

**步骤 1**：访问 E2B 官网

打开浏览器，访问：[https://e2b.dev](https://e2b.dev)

**步骤 2**：注册/登录

- 点击页面右上角的 **"Sign Up"** 或 **"Login"** 按钮
- 支持以下登录方式：
  - GitHub 账号（推荐）
  - Google 账号
  - 邮箱注册

<div align=center><img src="https://typora-photo1220.oss-cn-beijing.aliyuncs.com/DataAnalysis/ZhiJie/20251216190623948.png" width=100%></div>

### 2.2 创建 API Key

**步骤 1**：进入 API Keys 管理页面

- 登录成功后，在左侧导航栏选择 **"API Keys"** 选项

<div align=center><img src="https://typora-photo1220.oss-cn-beijing.aliyuncs.com/DataAnalysis/ZhiJie/20251216190623945.png" width=100%></div>

**步骤 2**：创建新的 API Key

- 点击 **"Create New API Key"** 按钮
- 输入 API Key 的名称（如：`DeepAgents-Production`）
- 点击确认创建

**步骤 3**：保存 API Key

- 创建成功后，**立即复制并保存** API Key
- ⚠️ **重要提示**：API Key 只会显示一次，关闭页面后无法再次查看！

<div align=center><img src="https://typora-photo1220.oss-cn-beijing.aliyuncs.com/DataAnalysis/ZhiJie/20251216190623942.png" width=70%></div>

### 2.3 配置环境变量

**步骤 1**：创建或编辑 `.env` 文件

在项目根目录下创建 `.env` 文件（如果已存在则编辑）：

```bash
# E2B API Key
E2B_API_KEY=your_api_key_here
```

**步骤 2**：验证配置

```python
import os
from dotenv import load_dotenv

load_dotenv(override=True)

api_key = os.getenv("E2B_API_KEY")
if api_key:
    print("✅ E2B_API_KEY 配置成功")
else:
    print("❌ E2B_API_KEY 未配置")
```

---

## 三、安装依赖

### 3.1 安装 Python 包

```bash
pip install e2b
```

### 3.2 验证安装

```python
try:
    from e2b import Sandbox
    print("✅ e2b 包安装成功")
except ImportError:
    print("❌ e2b 包未安装，请运行：pip install e2b")
```

---

## 四、E2BBackend 实现

### 4.1 完整代码实现

创建文件 `e2b_backend.py`：

```python
import base64
from typing import Any, Optional

# 导入 DeepAgents 后端协议，定义了沙箱后端的接口
from deepagents.backends.protocol import (
    ExecuteResponse,
    FileDownloadResponse,
    FileUploadResponse,
    SandboxBackendProtocol,
)
# 导入基础沙箱类，用于实现沙箱后端的基本功能
from deepagents.backends.sandbox import BaseSandbox

try:
    from e2b import Sandbox
except ImportError:
    Sandbox = None

class E2BBackend(BaseSandbox):
    """E2B 沙箱后端实现，用于 DeepAgents。

    该后端使用 E2B（https://e2b.dev）提供安全、隔离的执行环境。
    """

    def __init__(
        self,
        template: str = "base",
        api_key: Optional[str] = None,
        timeout: Optional[int] = None,
        metadata: Optional[dict[str, str]] = None,
    ) -> None:
        """初始化 E2B 沙箱。

        参数:
            template: E2B 沙箱模板 ID（默认："base"）
            api_key: E2B API 密钥（可选，默认使用 E2B_API_KEY 环境变量）
            timeout: 沙箱超时时间（秒）
            metadata: 自定义沙箱元数据
        """
        if Sandbox is None:
            raise ImportError(
                "e2b package is not installed. "
                "Please install it with `pip install e2b`."
            )

        self.sandbox = Sandbox.create(
            template=template,
            api_key=api_key,
            timeout=timeout,
            metadata=metadata,
        )

    @property
    def id(self) -> str:
        """Unique identifier for the sandbox backend."""
        return self.sandbox.sandbox_id

    def execute(self, command: str) -> ExecuteResponse:
        """Execute a command in the sandbox."""
        try:
            # E2B commands.run returns CommandResult with stdout, stderr, exit_code
            result = self.sandbox.commands.run(command)

            # 返回执行结果，包含 stdout 是标准输出，stderr 是标准错误输出，exit_code 是退出码
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

    def upload_files(self, files: list[tuple[str, bytes]]) -> list[FileUploadResponse]:
        """Upload multiple files to the sandbox."""
        responses = []
        for path, content in files:
            try:
                # Ensure directory exists before writing
                # We can use execute to mkdir -p
                parent_dir = path.rsplit("/", 1)[0]
                if parent_dir:
                    self.sandbox.commands.run(f"mkdir -p {parent_dir}")

                # Write file
                self.sandbox.files.write(path, content)
                responses.append(FileUploadResponse(path=path, error=None))
            except Exception as e:
                error_msg = str(e).lower()
                error = "invalid_path"
                if "permission" in error_msg:
                    error = "permission_denied"

                responses.append(FileUploadResponse(path=path, error=error))
        return responses

    def download_files(self, paths: list[str]) -> list[FileDownloadResponse]:
        """Download multiple files from the sandbox."""
        responses = []
        for path in paths:
            try:
                content = self.sandbox.files.read(path)
                # Ensure content is bytes
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

    def close(self):
        """Close the sandbox session."""
        self.sandbox.kill()
```

---

## 五、使用示例

### 5.1 基础使用示例

```python
import asyncio
import os
from dotenv import load_dotenv
from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI
from e2b_backend import E2BBackend

# 加载环境变量
load_dotenv(override=True)

async def run_e2b_demo():
    print("\n" + "="*80)
    print("DeepAgents E2BBackend (Sandbox) 演示")
    print("="*80)

    # 1. 检查 API Key
    if not os.getenv("E2B_API_KEY"):
        print("❌ 错误：未找到 E2B_API_KEY 环境变量。")
        print("请在 .env 文件中设置 E2B_API_KEY")
        return

    # 2. 初始化 E2B Backend
    print("正在初始化 E2B 沙箱 (Template: base)...")
    try:
        backend = E2BBackend(template="base")
        print(f"✅ 沙箱已启动 (ID: {backend.id})")
    except Exception as e:
        print(f"❌ 沙箱启动失败：{e}")
        return

    try:
        # 3. 创建 DeepAgent
        llm = ChatOpenAI(model="gpt-4o", temperature=0)

        agent = create_deep_agent(
            model=llm,
            backend=backend,
            system_prompt="""你是一个拥有云端沙箱环境的高级技术助手。
            你的任务是演示如何在沙箱中进行操作。
            """
        )

        # 4. 执行任务
        task = """请完成以下任务：
        1. 使用 execute 命令运行 'uname -a' 和 'python --version' 来展示环境信息
        2. 创建一个 Python 脚本 '/home/user/hello.py'，内容是打印 'Hello from E2B Sandbox!'
        3. 运行这个 Python 脚本并显示输出
        """

        print(f"\n📋 任务开始")
        result = await agent.ainvoke({"messages": [("user", task)]})
        
        print("\n" + "="*80)
        print("📊 执行结果")
        print("="*80)
        print(result["messages"][-1].content)

    except Exception as e:
        print(f"❌ 运行时错误：{e}")
        import traceback
        traceback.print_exc()
    finally:
        # 5. 清理资源
        print("\n🧹 正在关闭沙箱...")
        backend.close()
        print("✅ 沙箱已关闭")
        print("演示结束")

if __name__ == "__main__":
    asyncio.run(run_e2b_demo())
```

### 5.2 输出示例

```
================================================================================
DeepAgents E2BBackend (Sandbox) 演示
================================================================================
正在初始化 E2B 沙箱 (Template: base)...
✅ 沙箱已启动 (ID: ifbjxvlc69x9acwc6hegi)

📋 任务开始

[Agent (model)]
----------------------------------------
演示完成！以下是我在沙箱环境中执行的步骤：

1. **环境信息**：
   - 操作系统信息：`Linux e2b.local 6.1.158 #2 SMP PREEMPT_DYNAMIC Tue Nov 25 15:58:27 UTC 2025 x86_64 GNU/Linux`
   - Python 版本：`Python 3.11.6`

2. **创建并运行 Python 脚本**：
   - 创建了一个 Python 脚本 `/home/user/hello.py`，内容是打印 `Hello from E2B Sandbox!`
   - 运行该脚本，输出为：`Hello from E2B Sandbox!`
----------------------------------------

🧹 正在关闭沙箱...
✅ 沙箱已关闭
演示结束
```

---

## 六、高级配置

### 6.1 自定义沙箱模板

E2B 支持多种预置模板和自定义模板：

```python
# 使用不同的预置模板
backend = E2BBackend(template="python-3.11")  # Python 3.11 环境
backend = E2BBackend(template="nodejs-18")   # Node.js 18 环境
backend = E2BBackend(template="base")        # 基础环境

# 自定义超时时间（秒）
backend = E2BBackend(
    template="base",
    timeout=600  # 10 分钟超时
)

# 添加元数据
backend = E2BBackend(
    template="base",
    metadata={
        "project": "DeepAgents-Demo",
        "environment": "production"
    }
)
```

### 6.2 文件上传下载

```python
from e2b_backend import E2BBackend

backend = E2BBackend()

# 上传文件
files_to_upload = [
    ("/home/user/script.py", b"print('Hello from E2B')"),
    ("/home/user/data.txt", b"Sample data content"),
]

upload_results = backend.upload_files(files_to_upload)
for result in upload_results:
    if result.error:
        print(f"❌ 上传失败 {result.path}: {result.error}")
    else:
        print(f"✅ 上传成功 {result.path}")

# 下载文件
files_to_download = ["/home/user/script.py", "/home/user/data.txt"]
download_results = backend.download_files(files_to_download)

for result in download_results:
    if result.error:
        print(f"❌ 下载失败 {result.path}: {result.error}")
    else:
        print(f"✅ 下载成功 {result.path}, 内容大小：{len(result.content)} bytes")
        # 保存文件
        with open(result.path.split("/")[-1], "wb") as f:
            f.write(result.content)

backend.close()
```

### 6.3 执行复杂命令

```python
from e2b_backend import E2BBackend

backend = E2BBackend()

# 执行单个命令
result = backend.execute("pip install numpy pandas matplotlib")
print(f"安装依赖 - 退出码：{result.exit_code}")
print(f"输出：{result.output}")

# 执行多行命令（使用 && 连接）
result = backend.execute("cd /home/user && python script.py")
print(f"执行脚本 - 退出码：{result.exit_code}")

# 执行带环境变量的命令
result = backend.execute("export API_KEY=secret && python app.py")

backend.close()
```

---

## 七、与 DeepAgents 集成

### 7.1 完整集成示例

```python
import asyncio
import os
from dotenv import load_dotenv
from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from e2b_backend import E2BBackend

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
    print("DeepAgents E2BBackend 完整集成演示")
    print("="*80)

    # 1. 检查 API Key
    if not os.getenv("E2B_API_KEY"):
        print("❌ 错误：未找到 E2B_API_KEY 环境变量")
        return

    # 2. 初始化 MCP
    mcp_client, mcp_tools = await setup_mcp_tools()

    # 3. 初始化 E2B Backend
    print("正在初始化 E2B 沙箱...")
    backend = E2BBackend(template="base")
    print(f"✅ 沙箱已启动 (ID: {backend.id})")

    try:
        # 4. 创建 DeepAgent
        llm = ChatOpenAI(model="gpt-4o", temperature=0)

        agent = create_deep_agent(
            model=llm,
            tools=mcp_tools,  # 赋予 MCP 工具能力
            backend=backend,  # 赋予 E2B 沙箱能力
            system_prompt="""你是一个拥有云端沙箱环境的高级技术助手。
            
你可以：
1. 使用 execute 工具执行任何 Linux 命令
2. 使用 write_file 和 read_file 操作文件
3. 使用 MCP 工具查询最新文档
4. 安装依赖包并运行复杂应用

请确保所有操作都在沙箱中进行，保持环境整洁。
"""
        )

        # 5. 执行复杂任务
        config = {"configurable": {"thread_id": "e2b_integrated_demo"}}

        task = """请完成以下数据分析任务：

1. 安装必要的依赖：numpy, pandas, matplotlib
2. 创建一个 Python 脚本 data_analysis.py，要求：
   - 生成 100 个随机数（正态分布，均值=50，标准差=10）
   - 计算统计信息（均值、中位数、标准差）
   - 绘制直方图并保存为 histogram.png
   - 将结果保存为 report.md
3. 执行脚本并返回结果
4. 下载生成的 report.md 文件并展示内容
"""

        print("\n📋 执行任务...")
        result = await agent.ainvoke({
            "messages": [("user", task)]
        }, config=config)

        print("\n" + "="*80)
        print("📊 执行结果")
        print("="*80)
        print(result["messages"][-1].content)

    except Exception as e:
        print(f"❌ 运行时错误：{e}")
        import traceback
        traceback.print_exc()
    finally:
        # 6. 清理资源
        print("\n🧹 正在关闭沙箱...")
        backend.close()
        print("✅ 沙箱已关闭")
        print("演示结束")

if __name__ == "__main__":
    asyncio.run(run_integrated_demo())
```

---

## 八、常见问题与故障排除

### 8.1 API Key 相关问题

**问题 1**：`Error: Invalid API key`

**解决方案**：
- 检查 `.env` 文件中 `E2B_API_KEY` 是否正确
- 确保 API Key 没有多余的空格或引号
- 重新创建新的 API Key

**问题 2**：`E2B_API_KEY not found`

**解决方案**：
```python
import os
print(f"当前环境变量：{os.getenv('E2B_API_KEY', '未设置')}")
# 手动设置
os.environ["E2B_API_KEY"] = "your_key_here"
```

### 8.2 沙箱启动失败

**问题**：`Sandbox creation failed: ...`

**可能原因**：
1. 网络连接问题
2. API Key 权限不足
3. 模板 ID 错误

**解决方案**：
```python
# 使用基础模板
backend = E2BBackend(template="base")

# 添加超时设置
backend = E2BBackend(template="base", timeout=60)
```

### 8.3 命令执行超时

**问题**：长时间运行的命令导致超时

**解决方案**：
```python
# 增加超时时间
backend = E2BBackend(timeout=600)  # 10 分钟

# 或者在创建沙箱时设置
from e2b import Sandbox
sandbox = Sandbox.create(template="base", timeout=600)
```

### 8.4 文件传输失败

**问题**：上传/下载文件时出错

**解决方案**：
```python
# 确保目录存在
backend.execute("mkdir -p /home/user/data")

# 检查文件路径
try:
    content = backend.sandbox.files.read("/path/to/file.txt")
except Exception as e:
    print(f"读取失败：{e}")
    # 列出目录内容
    result = backend.execute("ls -la /path/to/")
    print(result.output)
```

---

## 九、最佳实践

### 9.1 资源管理

```python
# 始终使用 try-finally 确保资源清理
backend = E2BBackend()
try:
    # 执行操作
    result = backend.execute("python script.py")
finally:
    backend.close()  # 确保沙箱关闭

# 或使用上下文管理器（如果支持）
with E2BBackend() as backend:
    result = backend.execute("python script.py")
```

### 9.2 错误处理

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

### 9.3 成本控制

- **监控使用量**：定期查看 E2B 控制台的使用量统计
- **设置预算告警**：在 E2B 控制台设置月度预算上限
- **及时清理**：任务完成后立即调用 `backend.close()`
- **复用沙箱**：多个任务使用同一个沙箱会话

---

## 十、参考资料

- **E2B 官方文档**：[https://e2b.dev/docs](https://e2b.dev/docs)
- **E2B GitHub**：[https://github.com/e2b-dev/e2b](https://github.com/e2b-dev/e2b)
- **DeepAgents 文档**：[https://github.com/langchain-ai/deepagents](https://github.com/langchain-ai/deepagents)
- **E2B 模板市场**：[https://e2b.dev/store](https://e2b.dev/store)

---

## 十一、总结

### 11.1 E2BBackend 核心优势

| 优势 | 说明 |
|------|------|
| **云端执行** | 不占用本地资源，支持弹性扩展 |
| **完全隔离** | 多租户环境，生产级安全性 |
| **持久会话** | 支持长时间运行的任务 |
| **标准环境** | 一致的 Linux 环境，避免依赖问题 |

### 11.2 使用流程总结

```
1. 注册 E2B 账号 → 2. 获取 API Key → 3. 配置环境变量
       ↓
4. 安装 e2b 包 → 5. 实现 E2BBackend → 6. 创建 DeepAgent
       ↓
7. 执行任务 → 8. 清理资源
```

### 11.3 下一步

- 实践：使用 E2BBackend 构建实际项目
- 深入：自定义 E2B 模板
- 优化：探索 E2B 的高级功能（如实时监控、日志收集等）
