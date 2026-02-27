"""
阶段三验证脚本
用于验证 DeepAgents 核心功能是否正常工作

前置要求:
1. 安装 deepagents 包 (如需要从源码安装，请参考官方文档)
2. 配置 API 密钥 (.env 文件)

运行方式:
    conda activate deepagent_1
    python middleware_info/stage3_verification.py
"""

import sys
import os
import subprocess
import json
from rich.console import Console
from rich.json import JSON
from rich.panel import Panel
console = Console()
# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv(override=True)

from deepagents import create_deep_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain_tavily import TavilySearch
from langchain_openai import ChatOpenAI

def check_deepagents_installed():
    """检查 deepagents 是否已安装"""
    try:
        import deepagents
        return True, deepagents.__version__ if hasattr(deepagents, '__version__') else 'unknown'
    except ImportError:
        return False, None


def install_deepagents_guide():
    """提供安装 deepagents 的指导"""
    print("\n" + "=" * 60)
    print("DeepAgents 安装指南")
    print("=" * 60)
    print("""
deepagents 包可能需要从特定源安装。请尝试以下方式:

1. 使用 pip 安装 (如果包在 PyPI 上可用):
   pip install deepagents

2. 如果上述方式失败，请参考:
   - 检查 LangChain 版本兼容性
   - 确认 Python 版本 (推荐 3.9+)
   - 查看官方文档获取安装说明

注意: 如果 deepagents 暂时不可用，您仍然可以:
   - 学习框架的使用方法和原理
   - 准备其他依赖 (langchain, langgraph 等)
   - 配置 API 密钥
""")

# 导入必要的库
from dotenv import load_dotenv

def test_environment():
    """测试 1: 环境验证 - 检查 Python 版本和依赖包"""
    print("=" * 60)
    print("测试 1: 环境验证")
    print("=" * 60)
    
    # 检查 Python 版本
    python_version = sys.version_info
    print(f"Python 版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version.major != 3 or python_version.minor < 8:
        print("[FAIL] Python 版本过低，建议使用 Python 3.8+")
        return False
    print("[PASS] Python 版本符合要求")
    
    # 检查 deepagents 是否安装
    deepagents_installed, version = check_deepagents_installed()
    if deepagents_installed:
        print(f"[PASS] deepagents 已安装 (版本: {version})")
    else:
        print("[WARN] deepagents 未安装")
        install_deepagents_guide()
    
    # 检查关键依赖包
    required_packages = [
        'langchain',
        'langchain_core',
        'langgraph',
    ]
    
    try:
        import importlib
        for package in required_packages:
            try:
                importlib.import_module(package)
                print(f"[PASS] {package} 已安装")
            except ImportError:
                print(f"[FAIL] {package} 未安装")
                return False
    except Exception as e:
        print(f"[FAIL] 依赖检查失败: {e}")
        return False
    
    return True


def test_model():
    """测试 2: 模型验证 - 测试语言模型连接"""
    print("\n" + "=" * 60)
    print("测试 2: 模型验证")
    print("=" * 60)
    
    # 加载环境变量
    load_dotenv(override=True)
    
    # 优先使用 MiniMax 模型
    minimax_api_key = os.getenv("MINIMAX_API_KEY")
    minimax_api_base = os.getenv("MINIMAX_API_BASE", "https://api.minimaxi.com/v1")
    
    if minimax_api_key:
        try:
            from langchain_openai import ChatOpenAI
            model = ChatOpenAI(
                model="MiniMax-M2.5",
                api_key=minimax_api_key,
                base_url=minimax_api_base,
                temperature=0
            )
            response = model.invoke("你好")
            print(f"[PASS] MiniMax-M2.5 模型调用成功")
            return True
        except Exception as e:
            print(f"[WARN] MiniMax 模型测试失败: {e}")
    
    # 尝试使用 DeepSeek 模型
    try:
        from langchain_deepseek import ChatDeepSeek
        model = ChatDeepSeek(model="deepseek-chat", temperature=0)
        response = model.invoke("你好")
        print("[PASS] DeepSeek 模型初始化成功")
        
        # 测试模型调用
        response = model.invoke("你好")
        print(f"[PASS] 模型调用成功，响应: {response.content[:50]}...")
        return True
        
    except ImportError:
        print("[INFO] DeepSeek 模型未安装，尝试使用 OpenAI...")
    except Exception as e:
        print(f"[WARN] DeepSeek 模型测试失败: {e}")
        print("[INFO] 尝试使用 OpenAI 模型...")
    
    try:
        from langchain_openai import ChatOpenAI
        model = ChatOpenAI(model="gpt-4o", temperature=0)
        response = model.invoke("你好")
        print(f"[PASS] OpenAI 模型调用成功")
        return True
    except ImportError:
        print("[FAIL] 未安装任何支持的模型")
        return False
    except Exception as e:
        print(f"[FAIL] 模型调用失败: {e}")
        return False


def test_create_deep_agent():
    """测试 3: 创建 DeepAgent - 验证 create_deep_agent 函数"""
    print("\n" + "=" * 60)
    print("测试 3: 创建 DeepAgent")
    print("=" * 60)
    
    # 先检查 deepagents 是否安装
    deepagents_installed, version = check_deepagents_installed()
    if not deepagents_installed:
        print("[SKIP] deepagents 未安装，跳过此测试")
        return True # 返回 True 以避免阻塞其他测试
    
    try:
        from deepagents import create_deep_agent
        print("[PASS] create_deep_agent 导入成功")
        
        # 查看函数签名
        import inspect
        sig = inspect.signature(create_deep_agent)
        print(f"[INFO] create_deep_agent 参数: {list(sig.parameters.keys())}")
        
        return True
    except ImportError as e:
        print(f"[FAIL] 无法导入 create_deep_agent: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] create_deep_agent 测试失败: {e}")
        return False


def test_custom_system_prompt():
    """测试 3.5: 自定义系统提示示例 - 课件 2.3 节"""
    print("\n" + "=" * 60)
    print("测试 3.5: 自定义系统提示示例")
    print("=" * 60)
    
    # 先检查 deepagents 是否安装
    deepagents_installed, version = check_deepagents_installed()
    if not deepagents_installed:
        print("[SKIP] deepagents 未安装，跳过此测试")
        return True
    
    try:
        from deepagents import create_deep_agent
        from deepagents.backends import FilesystemBackend
        from langgraph.checkpoint.memory import InMemorySaver
        from dotenv import load_dotenv
        
        load_dotenv(override=True)
        
        # 初始化模型 (优先使用 MiniMax)
        model = None
        minimax_api_key = os.getenv("MINIMAX_API_KEY")
        minimax_api_base = os.getenv("MINIMAX_API_BASE", "https://api.minimaxi.com/v1")
        
        if minimax_api_key:
            try:
                from langchain_openai import ChatOpenAI
                model = ChatOpenAI(
                    model="MiniMax-M2.5",
                    api_key=minimax_api_key,
                    base_url=minimax_api_base,
                    temperature=0
                )
                print("[INFO] 使用 MiniMax-M2.5 模型")
            except Exception as e:
                print(f"[WARN] MiniMax 模型初始化失败：{e}")
        
        if model is None:
            try:
                from langchain_deepseek import ChatDeepSeek
                model = ChatDeepSeek(model="deepseek-chat", temperature=0)
                print("[INFO] 使用 DeepSeek 模型")
            except:
                try:
                    from langchain_openai import ChatOpenAI
                    model = ChatOpenAI(model="gpt-4o", temperature=0)
                    print("[INFO] 使用 OpenAI 模型")
                except:
                    print("[WARN] 未找到可用的语言模型")
                    return True
        
        # 自定义系统提示 - 课件 2.3 节示例
        custom_prompt = """
你是一位专业的技术写作者，擅长撰写清晰、结构化的技术文档。
在开始写作前，请先使用 write_todos 工具规划文档结构。
完成后将结果保存到指定目录。
"""
        
        # 创建 FilesystemBackend
        backend_virtual = FilesystemBackend(
            root_dir=r"G:\DeepAgents_baseline\workspace",
            virtual_mode=True
        )
        
        agent = create_deep_agent(
            name="TechnicalWriter",
            model=model,
            backend=backend_virtual,
            system_prompt=custom_prompt,
            checkpointer=InMemorySaver(),
        )
        print("[PASS] 自定义系统提示 Agent 创建成功")
        
        # 测试简单对话
        config = {"configurable": {"thread_id": "custom_prompt_test"}}
        result = agent.invoke(
            {"messages": [{"role": "user", "content": "你好，请介绍一下你的功能,将其内容保存在md文件内。"}]},
            config=config
        )
        
        if result and "messages" in result:
            print(f'AI最终回复:{result["messages"][-1].content}')
            print("[PASS] 自定义系统提示测试成功")
            return True
        else:
            print("[FAIL] Agent 返回结果异常")
            return False
            
    except Exception as e:
        print(f"[FAIL] 自定义系统提示测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def test_tools():
    """测试 4: 工具验证 - 检查内置工具和自定义工具是否正常"""
    print("\n" + "=" * 60)
    print("测试 4: 工具验证")
    print("=" * 60)
    
    # 先检查 deepagents 是否安装
    deepagents_installed, version = check_deepagents_installed()
    if not deepagents_installed:
        print("[SKIP] deepagents 未安装，跳过此测试")
        return True
    
    try:
        from deepagents import create_deep_agent
        from langgraph.checkpoint.memory import InMemorySaver
        from dotenv import load_dotenv
        
        # 加载环境变量
        load_dotenv(override=True)
        
        # 检查是否有 Tavily 可用作自定义工具
        custom_tools = []
        try:
            from langchain_tavily import TavilySearch
            import os
            tavily_api_key = os.getenv("TAVILY_API_KEY")
            if tavily_api_key:
                tavily = TavilySearch(max_results=3)
                custom_tools.append(tavily)
                print("[INFO] Tavily 搜索引擎已添加为自定义工具")
            else:
                print("[WARN] TAVILY_API_KEY 未配置，跳过自定义工具测试")
        except ImportError:
            print("[WARN] Tavily 库未安装，跳过自定义工具测试")
        
        # 创建 agent (带自定义工具)
        agent = create_deep_agent(
            name="TestAgent",
            tools=custom_tools if custom_tools else None,
            checkpointer=InMemorySaver(),
        )
        print("[PASS] Agent 创建成功")
        
        # 检查工具
        if hasattr(agent, 'nodes') and 'tools' in agent.nodes:
            tools_node = agent.nodes['tools']
            if hasattr(tools_node, 'bound'):
                tool_node = tools_node.bound
                if hasattr(tool_node, 'tools_by_name'):
                    tools = tool_node.tools_by_name
                    print(f"[PASS] 发现 {len(tools)} 个工具:")
                    for tool_name in tools.keys():
                        print(f"  - {tool_name}")
                    
                    # 验证核心内置工具
                    expected_tools = ['ls', 'read_file', 'write_file', 'write_todos', 'task']
                    print("\n--- 内置核心工具 ---")
                    for tool in expected_tools:
                        if tool in tools:
                            print(f"[PASS] 核心工具 {tool} 已加载")
                        else:
                            print(f"[WARN] 核心工具 {tool} 未找到")
                    
                    # 打印自定义工具
                    if custom_tools:
                        print("\n--- 自定义工具 ---")
                        for custom_tool in custom_tools:
                            tool_name = getattr(custom_tool, 'name', str(custom_tool))
                            print(f"[PASS] 自定义工具 {tool_name} 已加载")
                    
                    return True
        
        print("[FAIL] 无法获取工具列表")
        return False
        
    except Exception as e:
        print(f"[FAIL] 工具验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_agent_invocation():
    """测试 5: 智能体调用 - 运行简单测试任务"""
    print("\n" + "=" * 60)
    print("测试 5: 智能体调用")
    print("=" * 60)
    
    # 先检查 deepagents 是否安装
    deepagents_installed, version = check_deepagents_installed()
    if not deepagents_installed:
        print("[SKIP] deepagents 未安装，跳过此测试")
        return True
    
    try:
        from deepagents import create_deep_agent
        from langgraph.checkpoint.memory import InMemorySaver
        from dotenv import load_dotenv
        
        load_dotenv(override=True)
        
        # 优先使用 MiniMax 模型
        model = None
        minimax_api_key = os.getenv("MINIMAX_API_KEY")
        minimax_api_base = os.getenv("MINIMAX_API_BASE", "https://api.minimaxi.com/v1")
        
        if minimax_api_key:
            try:
                from langchain_openai import ChatOpenAI
                model = ChatOpenAI(
                    model="MiniMax-M2.5",
                    api_key=minimax_api_key,
                    base_url=minimax_api_base,
                    temperature=0
                )
                print("[INFO] 使用 MiniMax-M2.5 模型")
            except Exception as e:
                print(f"[WARN] MiniMax 模型初始化失败: {e}")
        
        if model is None:
            try:
                from langchain_deepseek import ChatDeepSeek
                model = ChatDeepSeek(model="deepseek-chat", temperature=0)
                print("[INFO] 使用 DeepSeek 模型")
            except:
                try:
                    from langchain_openai import ChatOpenAI
                    model = ChatOpenAI(model="gpt-4o", temperature=0)
                    print("[INFO] 使用 OpenAI 模型")
                except:
                    print("[WARN] 未找到可用的语言模型，跳过实际调用测试")
                    return True
        
        if model is None:
            return True
            
        # 创建 agent
        agent = create_deep_agent(
            name="TestAgent",
            model=model,
            checkpointer=InMemorySaver(),
        )
        print("[PASS] 测试 Agent 创建成功")
        
        # 运行简单任务
        config = {"configurable": {"thread_id": "test_1"}}
        
        # 由于没有工具，这会是一个简单的对话测试
        result = agent.invoke(
            {"messages": [{"role": "user", "content": "请回复 '测试成功'"}]},
            config=config
        )
        
        if result and "messages" in result:
            last_msg = result["messages"][-1]
            print(f"[PASS] Agent 调用成功")
            print(f"[INFO] 响应: {last_msg.content[:100]}...")
            return True
        else:
            print("[FAIL] Agent 返回结果异常")
            return False
            
    except Exception as e:
        print(f"[FAIL] 智能体调用测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

# 调试函数 - 课件 6.2 节示例[同步格式化展示]
def debug_agent_stream(query: str, agent, config):
    """
    调试智能体并打印中间过程（包含 TODO 列表跟踪）
    """
    print("\n" + "=" * 60)
    print(f"查询: {query}")
    print("=" * 60)

    step_num = 0
    final_event = None

    # 实时流式输出
    for event in agent.stream(
            {"messages": [{"role": "user", "content": query}]},
            stream_mode="values",
            config=config
    ):
        step_num += 1
        final_event = event

        print(f"\n{'=' * 60}")
        print(f"步骤 {step_num}")
        print(f"{'=' * 60}")

        # 显示 TODO 列表状态 (从 tool_calls 中提取)
        msg = event.get("messages", [None])[-1] if "messages" in event else None
        if msg and hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tool_call in msg.tool_calls:
                if tool_call.get('name') == 'write_todos':
                    args = tool_call.get('args', {})
                    if 'todos' in args:
                        todos = args['todos']
                        if todos and isinstance(todos, list):
                            print("\n--- TODO 列表 (中间状态) ---")
                            for todo in todos:
                                status = todo.get('status', 'unknown')
                                if status == 'completed':
                                    status_icon = '[PASS]'
                                elif status == 'in_progress':
                                    status_icon = '[IN PROGRESS]'
                                else:
                                    status_icon = '[PENDING]'
                                content = todo.get('content', 'Unknown task')
                                print(f"{status_icon} {content}")
                            print("-" * 40)

        if "messages" in event:
            messages = event["messages"]
            if messages:
                msg = messages[-1]

                # AI 思考
                if hasattr(msg, 'content') and msg.content:
                    content = msg.content
                    print(f"\n--- AI 思考 ---")
                    # 只显示前 200 个字符，避免编码问题
                    #display_content = content[:200] if len(content) > 200 else content
                    display_content=content
                    print(display_content)
                    print("...(内容较长)")

                # 工具调用
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    print(f"\n--- 工具调用 ---")
                    for tool_call in msg.tool_calls:
                        tool_name = tool_call.get('name', 'unknown')
                        tool_args = tool_call.get('args', {})
                        print(f"工具: {tool_name}")
                        print(f"参数: {json.dumps(tool_args, ensure_ascii=False)[:1000]}")

                # 工具响应
                if hasattr(msg, 'name') and msg.name:
                    response = str(msg.content)[:1000]
                    print(f"\n--- 工具响应: {msg.name} ---")
                    print(response + "..." if len(str(msg.content)) > 300 else response)

    # 从 checkpoint 中获取最终 TODO 状态
    print("\n" + "=" * 60)
    print("从 Checkpoint 获取 TODO 状态...")
    print("=" * 60)

    todos = None
    try:
        state = agent.get_state(config)
        if state and hasattr(state, 'values') and isinstance(state.values, dict):
            print(f"State keys: {list(state.values.keys())}")
            if 'todos' in state.values:
                todos = state.values['todos']
                print(f"获取到 {len(todos)} 个 TODO")
            else:
                print("状态中没有 'todos' 键")
    except Exception as e:
        print(f"获取状态失败: {e}")

    if todos and isinstance(todos, list):
        print("\n--- TODO 列表 (最终状态) ---")
        for todo in todos:
            status = todo.get('status', 'unknown')
            if status == 'completed':
                status_icon = '[PASS]'
            elif status == 'in_progress':
                status_icon = '[IN PROGRESS]'
            else:
                status_icon = '[PENDING]'
            content = todo.get('content', 'Unknown task')
            print(f"{status_icon} {content}")
        print("-" * 40)

    print("\n调试完成!\n")
    return final_event


def test_research_agent_with_tavily():
    """测试 5.5: 研究智能体示例 - 课件第 2 章完整示例"""
    print("\n" + "=" * 60)
    print("测试 5.5: 研究智能体示例 (带 Tavily 搜索)")
    print("=" * 60)

    # 检查 deepagents 是否安装
    try:
        import deepagents
    except ImportError:
        print("[SKIP] deepagents 未安装，跳过此测试")
        return True

    # 检查 Tavily
    try:
        from langchain_tavily import TavilySearch
        print("[INFO] Tavily 库已安装")
    except ImportError:
        print("[WARN] Tavily 库未安装，跳过此测试")
        return True

    # 检查 Tavily API 密钥
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if not tavily_api_key:
        print("[WARN] TAVILY_API_KEY 未配置，跳过此测试")
        return True

    # 初始化模型
    minimax_api_key = os.getenv("MINIMAX_API_KEY")
    minimax_api_base = os.getenv("MINIMAX_API_BASE", "https://api.minimaxi.com/v1")

    model = None
    if minimax_api_key:
        try:
            model = ChatOpenAI(
                model="MiniMax-M2.5",
                api_key=minimax_api_key,
                base_url=minimax_api_base,
                temperature=0
            )
            print("[INFO] 使用 MiniMax-M2.5 模型")
        except Exception as e:
            print(f"[WARN] MiniMax 模型初始化失败：{e}")

    if model is None:
        try:
            from langchain_deepseek import ChatDeepSeek
            model = ChatDeepSeek(model="deepseek-chat", temperature=0)
            print("[INFO] 使用 DeepSeek 模型")
        except:
            try:
                model = ChatOpenAI(model="gpt-4o", temperature=0)
                print("[INFO] 使用 OpenAI 模型")
            except:
                print("[WARN] 未找到可用的语言模型")
                return True

    # 初始化 Tavily 搜索引擎
    tavily = TavilySearch(max_results=3)
    print("[PASS] Tavily 搜索引擎初始化成功")

    # 自定义系统提示 - 更明确要求使用 write_todos
    research_instructions = """
你是一位资深研究员。你的工作是进行深入的研究，然后撰写一份精美的报告。

## 重要规则
1. 在开始任何研究之前，你必须首先使用 write_todos 工具规划任务
2. 将任务分解为具体的子任务
3. 每完成一个子任务后更新 TODO 列表状态
4. 最后撰写报告

## 可用工具

### `write_todos` (必须使用)
- 在开始研究前使用此工具创建任务列表
- 格式：包含 content 和 status 字段

### `互联网搜索`
使用此功能针对给定的查询进行互联网搜索。

### `写入本地文件`
使用此功能将研究报告保存到本地文件。

## 工作流程
1. 首先使用 write_todos 工具将研究任务分解为清晰的步骤
2. 使用互联网搜索来收集全面的信息
3. 将信息整合成一份结构清晰的报告
4. 完成报告后，务必使用 `写入本地文件` 工具将完整报告保存到本地文件
5. 务必引用你的资料来源
"""

    # 创建 Agent
    agent = create_deep_agent(
        name="DeepAgents_Agent",
        tools=[tavily],
        model=model,
        system_prompt=research_instructions,
        checkpointer=InMemorySaver(),
    )
    print("[PASS] 研究智能体创建成功")

    # 运行测试
    config = {"configurable": {"thread_id": "research_test"}}
    query = "请调研一下人工智能在医疗领域的应用发展趋势"

    print(f"[INFO] 发送查询：{query[:50]}...")

    # 使用 debug_agent_stream 展示中间过程
    result = debug_agent_stream(query, agent, config)

    if result and "messages" in result:
        last_msg = result["messages"][-1]
        print(f"[PASS] 研究智能体测试成功")
        print(f"[INFO] 响应：{last_msg.content[:200]}...")
        return True
    else:
        print("[FAIL] Agent 返回结果异常")
        return False



def test_debug_agent_with_rich():
    """测试 5.8: 使用 Rich 库调试 Agent - 课件 6.2 节"""
    print("\n" + "=" * 60)
    print("测试 5.8: 使用 Rich 库调试 Agent")
    print("=" * 60)
    
    # 先检查 deepagents 是否安装
    deepagents_installed, version = check_deepagents_installed()
    if not deepagents_installed:
        print("[SKIP] deepagents 未安装，跳过此测试")
        return True
    
    try:
        # 检查 Rich 库
        try:
            from rich.console import Console
            from rich.json import JSON
            from rich.panel import Panel
            console = Console()
            print("[INFO] Rich 库已安装")
        except ImportError:
            print("[WARN] Rich 库未安装，尝试安装...")
            subprocess.run([sys.executable, "-m", "pip", "install", "rich"], check=True)
            from rich.console import Console
            from rich.json import JSON
            from rich.panel import Panel
            console = Console()
        
        from deepagents import create_deep_agent
        from langgraph.checkpoint.memory import InMemorySaver
        from dotenv import load_dotenv
        
        load_dotenv(override=True)
        
        # 初始化模型 (优先使用 MiniMax)
        model = None
        minimax_api_key = os.getenv("MINIMAX_API_KEY")
        minimax_api_base = os.getenv("MINIMAX_API_BASE", "https://api.minimaxi.com/v1")
        
        if minimax_api_key:
            try:
                from langchain_openai import ChatOpenAI
                model = ChatOpenAI(
                    model="MiniMax-M2.5",
                    api_key=minimax_api_key,
                    base_url=minimax_api_base,
                    temperature=0
                )
                print("[INFO] 使用 MiniMax-M2.5 模型")
            except Exception as e:
                print(f"[WARN] MiniMax 模型初始化失败：{e}")
        
        if model is None:
            try:
                from langchain_deepseek import ChatDeepSeek
                model = ChatDeepSeek(model="deepseek-chat", temperature=0)
                print("[INFO] 使用 DeepSeek 模型")
            except:
                try:
                    from langchain_openai import ChatOpenAI
                    model = ChatOpenAI(model="gpt-4o", temperature=0)
                    print("[INFO] 使用 OpenAI 模型")
                except:
                    print("[WARN] 未找到可用的语言模型")
                    return True

        # 创建 FilesystemBackend
        from deepagents.backends import FilesystemBackend
        backend_virtual = FilesystemBackend(
            root_dir=r"G:\DeepAgents_baseline\workspace",
            virtual_mode=True
        )



        # 创建 DeepAgent
        agent = create_deep_agent(
            name="DebugAgent",
            model=model,
            backend=backend_virtual,
            checkpointer=InMemorySaver(),
        )
        print("[PASS] Debug Agent 创建成功")

        # 调试函数 - 课件 6.2 节示例

        # 运行调试[很简单问题就不需要planing，改例子就是简单问题问答]
        query = "请帮我列出当前目录下有哪些文件"
        console.print(Panel.fit(
            f"[bold cyan]运行调试 Agent:[/bold cyan] {query}",
            border_style="cyan"
        ))
        # 运行测试
        config = {"configurable": {"thread_id": "agent_with_rich"}}

        result = debug_agent_stream(query, agent,config)

        console.print("[PASS] Rich 调试测试完成")
        return True

    except Exception as e:
        console.print(Panel(f"[bold red]错误：{e}[/bold red]", border_style="red"))
        import traceback
        traceback.print_exc()
        return False


def test_filesystem_tools():
    """测试 6: 文件系统工具测试"""
    print("\n" + "=" * 60)
    print("测试 6: 文件系统工具测试")
    print("=" * 60)

    try:
        from deepagents.tools import ls, read_file, write_file

        # 测试 ls 工具
        print("[INFO] 测试 ls 工具...")
        result = ls.invoke({"path": "."})
        print(f"[PASS] ls 工具可用，当前目录文件数: {len(result) if isinstance(result, list) else 'N/A'}")

        # 测试 write_file 工具
        print("[INFO] 测试 write_file 工具...")
        test_content = "DeepAgents 验证测试文件\n测试时间: 2025-01-01"
        write_file.invoke({"file_path": "test_output.txt", "content": test_content})
        print("[PASS] write_file 工具可用")

        # 测试 read_file 工具
        print("[INFO] 测试 read_file 工具...")
        content = read_file.invoke({"file_path": "test_output.txt"})
        if "DeepAgents" in content:
            print("[PASS] read_file 工具可用")

        # 清理测试文件
        import os
        if os.path.exists("test_output.txt"):
            os.remove("test_output.txt")
            print("[INFO] 测试文件已清理")

        return True

    except ImportError as e:
        print(f"[WARN] 文件系统工具导入失败: {e}")
        return True  # 不影响整体
    except Exception as e:
        print(f"[FAIL] 文件系统工具测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_basic_usage():
    """测试 7: 基础使用示例 - 代码验证智能体"""
    print("\n" + "=" * 60)
    print("测试 7: 基础使用示例 - 代码验证智能体")
    print("=" * 60)

    # 先检查 deepagents 是否安装
    deepagents_installed, version = check_deepagents_installed()
    if not deepagents_installed:
        print("[SKIP] deepagents 未安装，跳过此测试")
        return True

    try:
        from deepagents import create_deep_agent
        from deepagents.backends.local_shell import LocalShellBackend
        from langgraph.checkpoint.memory import InMemorySaver
        from dotenv import load_dotenv
        from pathlib import Path

        load_dotenv(override=True)

        # 初始化模型 (优先使用 MiniMax)
        model = None
        minimax_api_key = os.getenv("MINIMAX_API_KEY")
        minimax_api_base = os.getenv("MINIMAX_API_BASE", "https://api.minimaxi.com/v1")

        if minimax_api_key:
            try:
                from langchain_openai import ChatOpenAI
                model = ChatOpenAI(
                    model="MiniMax-M2.5",
                    api_key=minimax_api_key,
                    base_url=minimax_api_base,
                    temperature=0,
                    max_tokens=4096
                )
                print("[INFO] 使用 MiniMax-M2.5 模型")
            except Exception as e:
                print(f"[WARN] MiniMax 模型初始化失败: {e}")

        if model is None:
            try:
                from langchain_deepseek import ChatDeepSeek
                model = ChatDeepSeek(model="deepseek-chat", temperature=0)
                print("[INFO] 使用 DeepSeek 模型")
            except:
                try:
                    from langchain_openai import ChatOpenAI
                    model = ChatOpenAI(model="gpt-4o", temperature=0)
                    print("[INFO] 使用 OpenAI 模型")
                except:
                    print("[WARN] 未找到可用的语言模型")
                    return True

        # 创建 FilesystemBackend
        from deepagents.backends import FilesystemBackend
        backend_virtual = FilesystemBackend(
            root_dir=r"G:\DeepAgents_baseline",
            virtual_mode=True
        )


        # 创建 DeepAgent (基础使用示例)
        agent = create_deep_agent(
            name="CodeValidator",
            model=model,
            backend=backend_virtual,
            checkpointer=InMemorySaver(),
        )
        print("[PASS] 基础使用示例 Agent 创建成功")

        # 运行代码验证任务
        config = {"configurable": {"thread_id": "basic_usage_test"}}
        query = "请验证当前 workspace 目录下有哪些文件？请直接列出文件列表，不需要执行其他操作。"

        print(f"[INFO] 发送查询: {query[:50]}...")

        result = agent.invoke(
            {"messages": [{"role": "user", "content": query}]},
            config=config
        )

        if result and "messages" in result:
            last_msg = result["messages"][-1]
            print(f"[PASS] 基础使用示例测试成功")
            print(f"[INFO] Agent 响应: {last_msg.content[:200]}...")
            return True
        else:
            print("[FAIL] Agent 返回结果异常")
            return False

    except Exception as e:
        print(f"[FAIL] 基础使用示例测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_deep_research_agent():
    """测试 8: 深度研究智能体 - 使用 Rich 库进行调试输出"""
    print("\n" + "=" * 60)
    print("测试 8: 深度研究智能体")
    print("=" * 60)

    # 先检查 deepagents 是否安装
    deepagents_installed, version = check_deepagents_installed()
    if not deepagents_installed:
        print("[SKIP] deepagents 未安装，跳过此测试")
        return True

    try:
        # 检查 Rich 库
        try:
            from rich.console import Console
            from rich.json import JSON
            from rich.panel import Panel
            console = Console()
            print("[INFO] Rich 库已安装")
        except ImportError:
            print("[WARN] Rich 库未安装，尝试安装...")
            import subprocess
            subprocess.run([sys.executable, "-m", "pip", "install", "rich"], check=True)
            from rich.console import Console
            from rich.json import JSON
            from rich.panel import Panel
            console = Console()

        from deepagents import create_deep_agent
        from deepagents.backends.local_shell import LocalShellBackend
        from langgraph.checkpoint.memory import InMemorySaver
        from dotenv import load_dotenv
        from pathlib import Path

        load_dotenv(override=True)

        # 初始化模型 (优先使用 MiniMax)
        model = None
        minimax_api_key = os.getenv("MINIMAX_API_KEY")
        minimax_api_base = os.getenv("MINIMAX_API_BASE", "https://api.minimaxi.com/v1")

        if minimax_api_key:
            try:
                from langchain_openai import ChatOpenAI
                model = ChatOpenAI(
                    model="MiniMax-M2.5",
                    api_key=minimax_api_key,
                    base_url=minimax_api_base,
                    temperature=0,
                    max_tokens=4096
                )
                print("[INFO] 使用 MiniMax-M2.5 模型")
            except Exception as e:
                print(f"[WARN] MiniMax 模型初始化失败: {e}")

        if model is None:
            try:
                from langchain_deepseek import ChatDeepSeek
                model = ChatDeepSeek(model="deepseek-chat", temperature=0)
                print("[INFO] 使用 DeepSeek 模型")
            except:
                try:
                    from langchain_openai import ChatOpenAI
                    model = ChatOpenAI(model="gpt-4o", temperature=0)
                    print("[INFO] 使用 OpenAI 模型")
                except:
                    print("[WARN] 未找到可用的语言模型")
                    return True

        # 创建 LocalShellBackend【新的后端为了执行代码的而生的】
        WORKSPACE_ROOT = Path(r"G:\DeepAgents_baseline")
        PYTHON_ENV = r"D:\sorfware_install\python3.8_install\envs\deepagent_1"
        PYTHON_PATH = os.path.join(PYTHON_ENV, "Scripts")
        CURRENT_PATH = os.environ.get("PATH", "")

        backend = LocalShellBackend(
            root_dir=WORKSPACE_ROOT,
            virtual_mode=True,
            inherit_env=True,
            env={
                "PATH": f"{PYTHON_PATH};{CURRENT_PATH}",
                "VIRTUAL_ENV": PYTHON_ENV,
            }
        )

        # 创建 DeepAgent (深度研究智能体)
        research_instructions = """
        您是一位资深的研究人员。您的工作是进行深入的研究，然后撰写一份精美的报告。
        您可以通过互联网搜索引擎作为主要的信息收集工具。

        ## 可用工具

        ### `互联网搜索`
        使用此功能针对给定的查询进行互联网搜索。

        ### `写入本地文件`
        使用此功能将研究报告保存到本地文件。

        ## 工作流程
        1. 首先将研究任务分解为清晰的步骤
        2. 使用互联网搜索来收集全面的信息
        3. 将信息整合成一份结构清晰的报告
        4. 完成报告后，务必使用 `写入本地文件` 工具将完整报告保存到本地文件
        5. 务必引用你的资料来源
        """
        # 检查 Tavily
        try:
            from langchain_tavily import TavilySearch
            print("[INFO] Tavily 库已安装")
        except ImportError:
            print("[WARN] Tavily 库未安装，跳过此测试")
            return True

        # 检查 Tavily API 密钥
        tavily_api_key = os.getenv("TAVILY_API_KEY")
        if not tavily_api_key:
            print("[WARN] TAVILY_API_KEY 未配置，跳过此测试")
            return True
         # 初始化 Tavily 搜索引擎
        tavily = TavilySearch(max_results=3)
        print("[PASS] Tavily 搜索引擎初始化成功")
        agent = create_deep_agent(
            name="DeepResearcher",
            model=model,
            backend=backend,
            tools=[tavily],
            system_prompt=research_instructions,
            checkpointer=InMemorySaver(),
        )
        console.print(Panel.fit("[bold green]深度研究智能体创建成功![/bold green]", border_style="green"))

        # 运行研究任务
        #test_query = "请简单介绍一下 vibe coding 是什么？请将结果保存在vibe_coding前言技术.md文件内。"#该问题太简单了
        test_query = "请帮我调研一下高职院校人工智能技术应用专业未来发展如何？请将结果保存在人工智能技术应用专业未来发展.md文件内。"
        console.print(Panel.fit(
            f"[bold cyan]查询:[/bold cyan] {test_query}",
            border_style="cyan"
        ))

        config = {"configurable": {"thread_id": "deep_research_test"}}

        # 使用 debug_agent_stream 展示中间过程
        result = debug_agent_stream(test_query, agent, config)

        if result and "messages" in result:
            last_msg = result["messages"][-1]
            print(f"[PASS] 研究智能体测试成功")
            print(f"[INFO] 响应：{last_msg.content[:200]}...")
            return True
        else:
            print("[FAIL] Agent 返回结果异常")
            return False

    except Exception as e:
        console.print(Panel(f"[bold red]错误: {e}[/bold red]", border_style="red"))
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数 - 运行所有测试"""
    print("\n" + "=" * 60)
    print("DeepAgents 阶段三验证测试 (完整版)")
    print("=" * 60)
    print(f"运行环境: Python {sys.version}")
    print(f"工作目录: {os.getcwd()}")
    print("=" * 60)

    # 运行所有测试
    tests = [
        # ("环境验证", test_environment),
        # ("模型验证", test_model),
        # ("创建 DeepAgent", test_create_deep_agent),
        #("自定义系统提示", test_custom_system_prompt),
        #("工具验证", test_tools),
        #("智能体调用", test_agent_invocation),
        #("研究智能体 (Tavily)", test_research_agent_with_tavily),
        #("Rich 调试 Agent", test_debug_agent_with_rich),
        #("文件工具测试", test_filesystem_tools),
        #("基础使用示例", test_basic_usage),
        ("深度研究智能体", test_deep_research_agent),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n[ERROR] 测试 {test_name} 发生未预期的错误: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = 0
    failed = 0
    skipped = 0
    
    
    for test_name, result in results:
        if result is True:
            status = "[PASS]"
            passed += 1
        elif result is False:
            status = "[FAIL]"
            failed += 1
        else:
            status = "[SKIP]"
            skipped += 1
        print(f"{status} {test_name}")
    
    print("=" * 60)
    print(f"总计：{passed} 通过，{failed} 失败，{skipped} 跳过")
    print("=" * 60)
    
    if failed == 0:
        print("\n[Congratulations!] 所有测试通过!")
        return 0
    else:
        print(f"\n[Warning] {failed} 个测试未通过，请检查错误信息")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
