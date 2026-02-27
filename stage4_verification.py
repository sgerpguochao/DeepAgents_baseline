"""
阶段四示例脚本
用于演示 DeepAgents 四大核心内置工具与组件的使用

四大核心内置工具:
1. 系统提示词 (System Prompts)
2. 规划工具 (Planning System / Todo List)
3. 子代理 (Sub-Agent Delegation)
4. 文件系统集成 (Filesystem & Sandbox)

前置要求:
1. 安装 deepagents 包
2. 配置 API 密钥 (.env 文件)
3. 使用 MiniMax-M2.5 模型

运行方式:
    conda activate deepagent_1
    python stage4_verification.py
"""

import sys
import os
import json

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ============================================================================
# 第一部分：导入必要的库
# ============================================================================

from dotenv import load_dotenv
from pathlib import Path


# ============================================================================
# 辅助函数
# ============================================================================

def get_available_model():
    """
    获取可用的语言模型 - 优先使用 MiniMax-M2.5
    
    返回:
        tuple: (模型对象，模型名称) 或 (None, None)
    """
    # 加载环境变量
    load_dotenv(override=True)
    
    # 尝试 MiniMax 模型
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
            # 测试调用
            model.invoke("测试")
            return model, "MiniMax-M2.5"
        except Exception as e:
            print(f"[WARN] MiniMax 模型初始化失败：{e}")
    
    return None, None


def debug_agent_stream(query: str, agent, config):
    """
    调试智能体并打印中间过程（包含 TODO 列表跟踪）
    """
    print("\n" + "=" * 60)
    print(f"查询：{query}")
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
                        print(f"工具：{tool_name}")
                        print(f"参数：{json.dumps(tool_args, ensure_ascii=False)[:1000]}")

                # 工具响应
                if hasattr(msg, 'name') and msg.name:
                    response = str(msg.content)[:1000]
                    print(f"\n--- 工具响应：{msg.name} ---")
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
        print(f"获取状态失败：{e}")

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


def print_section(title):
    """
    打印分节标题
    
    参数:
        title: 标题文本
    """
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


# ============================================================================
# 示例 1: 系统提示词 (2.3)
# ============================================================================

def demo_system_prompt():
    """
    示例 1: 自定义系统提示词 + 工具 + TodoList + FilesystemBackend
    来自课件 2.3 节
    添加：Tavily 搜索工具、TodoList 支持、FilesystemBackend 保存
    """
    print_section("示例 1: 自定义系统提示词 (课件 2.3)")
    
    # 获取模型
    model, model_name = get_available_model()
    if model is None:
        print("[FAIL] 未找到可用模型")
        return
    
    print(f"[INFO] 使用模型：{model_name}")
    
    try:
        from deepagents import create_deep_agent
        from deepagents.backends import FilesystemBackend
        from langgraph.checkpoint.memory import InMemorySaver
        from dotenv import load_dotenv
        
        load_dotenv(override=True)
        
        # 配置 Tavily 搜索工具 (参考 stage3_verification.py 第 325 行)
        custom_tools = []
        try:
            from langchain_tavily import TavilySearch
            tavily_api_key = os.getenv("TAVILY_API_KEY")
            if tavily_api_key:
                tavily = TavilySearch(max_results=3)
                custom_tools.append(tavily)
                print("[INFO] Tavily 搜索引擎已添加为自定义工具")
            else:
                print("[WARN] TAVILY_API_KEY 未配置，将使用无工具模式")
        except ImportError:
            print("[WARN] langchain_tavily 未安装，将使用无工具模式")
        
        # 配置 FilesystemBackend (用于保存文件)
        # 使用当前目录下的 ./workspace
        backend = FilesystemBackend(
            root_dir="./workspace",
            virtual_mode=True
        )
        print(f"[INFO] FilesystemBackend 已配置：./workspace")
        
        # 自定义系统提示词 - 课件 2.3 节示例
        # 自定义系统提示词 - 更明确地要求使用 TodoList 和保存文件
        custom_prompt = """
你是一位专业的技术作家，擅长撰写清晰、结构化的技术文档。

## 你的工作流程必须遵循以下步骤：

1. **首先**：使用 write_todos 工具规划任务结构，列出所有需要完成的任务
2. **然后**：逐步执行每个任务
3. **最后**：使用 write_file 工具将结果保存到 ./file_md/vibe_coding_report.md

请严格按照这个流程执行。
"""
        
        print("\n自定义系统提示词:")
        print("-" * 40)
        print(custom_prompt.strip())
        print("-" * 40)
        
        # 创建 Agent (带工具、Backend、checkpointer 以启用 TodoList)
        agent = create_deep_agent(
            model=model,
            tools=custom_tools if custom_tools else None,
            backend=backend,
            system_prompt=custom_prompt,
            checkpointer=InMemorySaver(),  # checkpointer 启用 TodoList 功能
        )
        print("\n[PASS] Agent 创建成功")
        print("[INFO] 包含组件:")
        print("  - 自定义系统提示词")
        print("  - Tavily 搜索工具" if custom_tools else "  - 无自定义工具")
        print("  - FilesystemBackend (虚拟文件系统)")
        print("  - TodoList (通过 checkpointer 启用)")
        
        # 测试调用 - 使用 debug_agent_stream 展示 TODO 状态
        config = {"configurable": {"thread_id": "system_prompt_demo"}}
        query = "请你阐述一下 vibe coding 如何工作，以及其优点和缺点，最后将结果保存为 md 文件到 /workspace/ 目录下"
        
        print(f"\n[查询]: {query}")
        
        # 使用 debug_agent_stream 展示执行过程（包含 TODO 列表跟踪）
        result = debug_agent_stream(query, agent, config)
        
        # 检查文件是否保存 (虚拟文件系统可能不会实际写入磁盘)
        print("\n[INFO] 检查保存的文件:")
        # 由于 virtual_mode=True，文件可能在虚拟文件系统中
        # 检查 workspace 目录
        workspace_dir = Path(r"G:\DeepAgents_baseline\workspace")
        if workspace_dir.exists():
            files = list(workspace_dir.iterdir())
            if files:
                for f in files:
                    print(f"  - {f.name}")
            else:
                print("  (workspace 为空，文件可能在虚拟文件系统中)")
        else:
            print("  (workspace 目录不存在)")
        
        print("\n[PASS] 自定义提示词 Agent 调用完成")
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()


# ============================================================================
# 示例 2: 规划工具 / TodoList (3.5)
# ============================================================================

def demo_todo_list():
    """
    示例 2: 规划工具 (TodoList)
    来自课件 3.5 节
    添加：Backend + 搜索工具
    """
    print_section("示例 2: 规划工具 (TodoList) (课件 3.5)")
    
    # 获取模型
    model, model_name = get_available_model()
    if model is None:
        print("[FAIL] 未找到可用模型")
        return
    
    print(f"[INFO] 使用模型：{model_name}")
    
    try:
        from deepagents import create_deep_agent
        from deepagents.backends import FilesystemBackend
        from langgraph.checkpoint.memory import InMemorySaver
        from dotenv import load_dotenv
        
        load_dotenv(override=True)
        
        # 配置 Tavily 搜索工具
        custom_tools = []
        try:
            from langchain_tavily import TavilySearch
            tavily_api_key = os.getenv("TAVILY_API_KEY")
            if tavily_api_key:
                tavily = TavilySearch(max_results=3)
                custom_tools.append(tavily)
                print("[INFO] Tavily 搜索引擎已添加")
            else:
                print("[WARN] TAVILY_API_KEY 未配置，将使用无工具模式")
        except ImportError:
            print("[WARN] langchain_tavily 未安装，将使用无工具模式")
        
        # 配置 FilesystemBackend
        backend = FilesystemBackend(
            root_dir="./workspace",
            virtual_mode=True
        )
        print(f"[INFO] FilesystemBackend 已配置：./workspace")
        
        # 自定义系统提示词 - 明确要求使用 TodoList
        custom_prompt = """
你是一位专业的技术研究员，擅长调研和总结信息。

## 你的工作流程必须遵循以下步骤：

1. **首先**：使用 write_todos 工具规划任务结构，列出所有需要完成的任务
2. **然后**：逐步执行每个任务
3. **最后**：汇总结果

请严格按照这个流程执行。
"""
        
        print("\n自定义系统提示词:")
        print("-" * 40)
        print(custom_prompt.strip())
        print("-" * 40)
        
        # 创建 Agent (带工具、Backend、checkpointer)
        agent = create_deep_agent(
            model=model,
            tools=custom_tools if custom_tools else None,
            backend=backend,
            system_prompt=custom_prompt,
            checkpointer=InMemorySaver(),
        )
        print("\n[PASS] Agent 创建成功")
        print("[INFO] 包含组件:")
        print("  - 自定义系统提示词")
        print("  - Tavily 搜索工具" if custom_tools else "  - 无自定义工具")
        print("  - FilesystemBackend (虚拟文件系统)")
        print("  - TodoList (通过 checkpointer 启用)")
        
        # 测试调用 - 使用 debug_agent_stream 展示 TODO 状态
        config = {"configurable": {"thread_id": "todo_demo"}}
        query = "帮我调研人工智能在医疗领域的应用，请你不要开启子代理。"
        
        print("\n[查询]:", query)
        debug_agent_stream(query, agent, config)
        
        # 检查 workspace 目录
        workspace_dir = Path(r"G:\DeepAgents_baseline\workspace")
        if workspace_dir.exists():
            files = list(workspace_dir.iterdir())
            if files:
                print("\n[INFO] workspace 目录文件:")
                for f in files:
                    print(f"  - {f.name}")
            else:
                print("\n[INFO] workspace 目录为空")
        
        print("\n[PASS] TodoList 示例运行完成")
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()


# ============================================================================
# 示例 3: 子代理 - 默认启用 (4.7)
# ============================================================================

def demo_default_sub_agent():
    """
    示例 3: 默认子代理
    来自课件 4.7 节
    演示：即使不传入 subagents 参数，Agent 默认也会启用 general-purpose 子代理
    参考：DeepAgents_框架介绍与应用实践.ipynb - 自动触发默认的 SubAgentMiddleware
    """
    print_section("示例 3: 默认子代理 (课件 4.7)")
    
    # 获取模型
    model, model_name = get_available_model()
    if model is None:
        print("[FAIL] 未找到可用模型")
        return
    
    print(f"[INFO] 使用模型：{model_name}")
    
    try:
        from deepagents import create_deep_agent
        from dotenv import load_dotenv
        from langchain_tavily import TavilySearch
        
        load_dotenv(override=True)
        
        print("\n[示例 3.1] 测试默认子代理 (课件 4.7)")
        print("-" * 40)
        print("即使不传入 subagents 参数，Agent 默认也会启用 general-purpose 子代理")
        
        # 配置 Tavily 搜索工具 (参考 notebook 第 4951 行)
        custom_tools = []
        try:
            tavily_api_key = os.getenv("TAVILY_API_KEY")
            if tavily_api_key:
                tavily = TavilySearch(max_results=2)
                custom_tools.append(tavily)
                print("[INFO] Tavily 搜索引擎已添加")
            else:
                print("[WARN] TAVILY_API_KEY 未配置，将使用无工具模式")
        except ImportError:
            print("[WARN] langchain_tavily 未安装，将使用无工具模式")
        
        # 创建 Agent (不传入 subagents) - 参考 notebook 第 4958-4965 行
        # create_deep_agent 默认会加载 SubAgentMiddleware(general_purpose_agent=True)
        # 这意味着 Agent 会自动获得一个名为 'task' 的工具，可以调用 'general-purpose' 子 Agent
        agent = create_deep_agent(
            model=model,
            tools=custom_tools if custom_tools else None,
            # subagents=[],  # 故意不传或传空
            system_prompt="""你是一个能够高效处理并发任务的智能助手。
                            对于包含多个独立部分的复杂任务，你必须使用 'task' 工具来创建 'general-purpose' 子 Agent 进行处理。
                            不要自己在主线程中串行执行所有操作。利用子 Agent 来隔离上下文并提高效率。"""
        )
        print("[PASS] Agent 创建成功 (默认启用 general-purpose 子代理)")
        
        # 显示子代理类型表格 - 课件 4.4 节
        print("\n[示例 3.2] 子代理类型 (课件 4.4)")
        print("-" * 40)
        print("| 类型 | 说明 |")
        print("|------|------|")
        print("| general-purpose | 通用型子代理，适用于大多数任务 |")
        print("| coder | 专门用于代码编写和调试 |")
        print("| researcher | 专门用于信息检索和研究 |")
        
        # 显示子代理调用流程 - 课件 4.6 节
        print("\n[示例 3.3] 子代理调用流程 (课件 4.6)")
        print("-" * 40)
        flow_diagram = """
主 Agent
  │
  ├── 任务 1 → [子 Agent 1: Python 历史调研]
  │              │
  │              └── 结果：/subagent_results/python_history.md
  │
  └── 任务 2 → [子 Agent 2: Rust 内存安全机制]
               │
               └── 结果：/subagent_results/rust_memory.md
  │
  └── 聚合结果 → 最终回复
"""
        print(flow_diagram)
        
        # 实际测试子代理调用 - 参考 notebook 第 4968-4971 行
        print("\n[示例 3.4] 实际测试默认子代理调用")
        print("-" * 40)
        
        config = {"configurable": {"thread_id": "default_subagent_demo"}}
        query = """请同时调研以下两个完全不同的主题，并分别给出简短总结：
            1. Python 语言的历史起源。
            2. Rust 语言的内存安全机制。
            请务必使用子 Agent 分别处理这两个任务。"""
        
        print(f"[查询]: {query}")
        
        # 使用流式输出展示调用过程
        step = 0
        final_result = None
        try:
            for event in agent.stream(
                {"messages": [{"role": "user", "content": query}]},
                config=config
            ):
                step += 1
                for node_name, node_data in event.items():
                    if node_data is None:
                        continue
                    
                    if "messages" in node_data:
                        msgs = node_data["messages"]
                        if not isinstance(msgs, list):
                            msgs = [msgs]
                        
                        for msg in msgs:
                            # 1. 检测工具调用 (期望看到 'task' 工具)
                            if hasattr(msg, "tool_calls") and msg.tool_calls:
                                for tc in msg.tool_calls:
                                    tool_name = tc['name']
                                    tool_args = tc['args']
                                    
                                    if tool_name == "task":
                                        print(f"\n[Step {step}] [TASK] 触发 'task' 工具 (Sub-Agent)")
                                        print(f"  子 Agent 类型：{tool_args.get('subagent_type')}")
                                        print(f"  任务指令：{tool_args.get('description')[:100]}...")
                            
                            # 2. 检测工具输出 (Sub-Agent 的返回结果)
                            elif hasattr(msg, 'name') and msg.name == 'task':
                                print(f"\n[Step {step}] Sub-Agent 完成任务返回:")
                                print(f"  结果：{str(msg.content)[:300]}...")
                            
                            # 3. 检测 AI 最终回复
                            elif hasattr(msg, 'content') and msg.content:
                                if len(msg.content) > 50:
                                    print(f"\n[Step {step}] Agent 回复:")
                                    print(f"  {msg.content[:500]}...")
                                    final_result = msg.content
        except Exception as e:
            print(f"[WARN] 流式输出中断：{e}")
            import traceback
            traceback.print_exc()
        
        # 显示最终结果
        if final_result:
            print("\n" + "=" * 60)
            print("[最终结果]")
            print("=" * 60)
            print(final_result)
        
        print("\n[PASS] 默认子代理示例运行完成")
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()


# ============================================================================
# 示例 4: 子代理 - 自定义配置 (4.5)
# ============================================================================

def demo_custom_sub_agent():
    """
    示例 4: 自定义子代理配置
    来自课件 4.5 节
    演示：配置自定义子代理
    参考：DeepAgents_框架介绍与应用实践.ipynb - 显示传入 subAgent 参数
    """
    print_section("示例 4: 自定义子代理配置 (课件 4.5)")
    
    # 获取模型
    model, model_name = get_available_model()
    if model is None:
        print("[FAIL] 未找到可用模型")
        return
    
    print(f"[INFO] 使用模型：{model_name}")
    
    try:
        import asyncio
        from deepagents import create_deep_agent
        from dotenv import load_dotenv
        from langchain_tavily import TavilySearch
        from langchain_core.messages import ToolMessage, BaseMessage
        from langchain_mcp_adapters.client import MultiServerMCPClient
        
        load_dotenv(override=True)
        
        print("\n[示例 4.1] 测试自定义子代理配置 (课件 4.5)")
        print("-" * 40)
        
        # 配置 Context7 MCP (连接官方文档) - 参考 notebook
        print("[INFO] 正在连接 Context7 MCP 服务器 (设置 10 秒超时)...")
        mcp_tools = []
        mcp_client = None
        try:
            async def setup_mcp_tools():
                client = MultiServerMCPClient({
                    "context7": {
                        "transport": "stdio",
                        "command": "npx",
                        "args": ["-y", "@upstash/context7-mcp@latest"],
                    }
                })
                tools = await client.get_tools()
                return client, tools
            
            # 同步调用 async 函数，添加超时
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                future = asyncio.wait_for(setup_mcp_tools(), timeout=10.0)
                mcp_client, mcp_tools = loop.run_until_complete(future)
                print(f"[INFO] 成功加载 {len(mcp_tools)} 个 MCP 工具")
            except asyncio.TimeoutError:
                print("[WARN] 连接 MCP 超时 (10 秒)，将使用 Tavily 搜索工具继续...")
            finally:
                loop.close()
        except Exception as e:
            print(f"[WARN] 连接 MCP 失败：{e}")
            print("[INFO] 将使用 Tavily 搜索工具继续...")
        
        # 配置 Tavily 搜索工具 (备用)
        custom_tools = []
        try:
            tavily_api_key = os.getenv("TAVILY_API_KEY")
            if tavily_api_key:
                tavily = TavilySearch(max_results=3)
                custom_tools.append(tavily)
                print("[INFO] Tavily 搜索引擎已添加")
            else:
                print("[WARN] TAVILY_API_KEY 未配置")
        except ImportError:
            print("[WARN] langchain_tavily 未安装")
        
        # 确定最终使用的工具
        final_tools = mcp_tools if mcp_tools else (custom_tools if custom_tools else None)
        
        # 子代理配置 - 参考 notebook
        subagents = [
            {
                "name": "DocsResearcher",
                "description": "负责查阅官方文档和技术规范的专家 Agent。",
                "system_prompt": "你是一名专门查阅官方文档的技术专家。请使用工具获取准确的技术细节。不要猜测。",
                "tools": final_tools,
                "model": model
            },
            {
                "name": "CommunityResearcher",
                "description": "负责搜索社区博客、教程和最佳实践的专家 Agent。",
                "system_prompt": "你是一名关注社区动态的开发者。请搜索博客、论坛和 GitHub 讨论。",
                "tools": custom_tools if custom_tools else None,  # 只使用 Tavily
                "model": model
            }
        ]
        
        print("子代理配置:")
        for subagent in subagents:
            print(f"  - 名称：{subagent['name']}")
            print(f"    描述：{subagent['description']}")
        
        # 创建带自定义子代理的 Agent - 参考 notebook
        agent = create_deep_agent(
            model=model,
            tools=[],
            subagents=subagents,
            system_prompt="""你是一名技术总监。你的任务是协调 DocsResearcher 和 CommunityResearcher 完成调研任务。
                            请根据用户需求，将任务拆解并分发给这两个子 Agent。
                            如果任务允许，请务必并行调用它们以提高效率。
                            最后汇总它们的报告。"""
        )
        print("[PASS] 自定义子代理配置成功")
        
        # 实际测试子代理调用 - 完全照搬 notebook 的流式输出逻辑
        print("\n[示例 4.2] 实际测试自定义子代理调用")
        print("-" * 40)
        
        config = {"configurable": {"thread_id": "custom_subagent_demo"}}
        query = "请详细调研 'LangChain DeepAgents' 框架。我需要官方的技术架构说明（来自文档）以及社区的最佳实践案例。请对比两者。"
        
        print(f"\n任务指令：{query}\n")
        
        # 运行并可视化 - 完全参考 notebook 的流式处理逻辑
        step = 0
        subagent_calls = []  # 存储子代理调用信息
        subagent_results = {}  # 存储子代理结果
        final_result = None
        
        print("\n[开始执行任务，请稍候...]\n")
        
        try:
            for event in agent.stream(
                {"messages": [("user", query)]},
                stream_mode="values",  # 使用 values 模式获取完整状态
                config=config
            ):
                step += 1
                
                if "messages" in event:
                    msgs = event["messages"]
                    # 确保是列表
                    if not isinstance(msgs, list):
                        msgs = [msgs]
                    
                    for msg in msgs:
                        # 0. 过滤非消息对象
                        if not hasattr(msg, 'content') and not hasattr(msg, 'tool_calls'):
                            continue
                        
                        # 1. 检测工具调用 (期望看到 'task' 工具)
                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                            print(f"\n=== Step {step}: 决策与调用 (Node: model) ===")
                            for tc in msg.tool_calls:
                                tool_name = tc.get('name', '')
                                tool_args = tc.get('args', {})
                                
                                if tool_name == "task":
                                    subagent_type = tool_args.get('subagent_type', tool_args.get('name', 'unknown'))
                                    description = tool_args.get('description', tool_args.get('task', 'No description'))
                                    print(f"  [触发 'task' 工具 (Sub-Agent)]")
                                    print(f"    子 Agent 类型：{subagent_type}")
                                    print(f"    任务指令：{description[:200]}...")
                                    # 存储子代理调用信息
                                    subagent_calls.append({
                                        "type": subagent_type,
                                        "description": description
                                    })
                                else:
                                    print(f"  [普通工具调用：{tool_name}]")
                        
                        # 2. 检测工具输出 (Sub-Agent 的返回结果)
                        if hasattr(msg, 'name') and msg.name:
                            if msg.name == "task":
                                content = str(msg.content)
                                print(f"\n=== Sub-Agent 完成任务 ===")
                                print(f"  结果预览：{content[:300]}...")
                                # 存储子代理结果
                                if subagent_calls:
                                    last_call = subagent_calls[-1]["type"]
                                    subagent_results[last_call] = content
                            else:
                                print(f"\n[工具输出] {msg.name}: {str(msg.content)[:100]}...")
                        
                        # 3. 检测 AI 最终回复 (没有 tool_calls 且有 content)
                        if hasattr(msg, 'content') and msg.content:
                            content_str = str(msg.content)
                            # 如果不是工具响应，且内容较长，可能是最终回复
                            if (not hasattr(msg, 'name') or not msg.name) and len(content_str) > 100:
                                # 检查是否包含总结性词汇
                                if any(keyword in content_str.lower() for keyword in ["summary", "总结", "对比", "conclusion", "综上所述"]):
                                    print(f"\n=== Agent 最终回复 ===")
                                    print(f"  {content_str[:1000]}...")
                                    final_result = content_str
        except Exception as e:
            print(f"[WARN] 流式输出中断：{e}")
            # 不打印完整堆栈，避免干扰输出
            # import traceback
            # traceback.print_exc()
        
        # 显示子代理调用汇总
        if subagent_calls:
            print("\n" + "=" * 60)
            print("[子代理调用汇总]")
            print("=" * 60)
            for i, call in enumerate(subagent_calls, 1):
                print(f"\n{i}. 子代理：{call['type']}")
                print(f"   任务：{call['description'][:150]}...")
        
        # 显示子代理执行结果
        if subagent_results:
            print("\n" + "=" * 60)
            print("[子代理执行结果]")
            print("=" * 60)
            for key, value in subagent_results.items():
                print(f"\n【{key}】:")
                print(f"{value[:600]}...")
        
        # 显示最终结果
        if final_result:
            print("\n" + "=" * 60)
            print("[最终结果]")
            print("=" * 60)
            print(final_result)
        else:
            # 如果没有检测到最终结果，显示提示信息
            print("\n" + "=" * 60)
            print("[说明]")
            print("=" * 60)
            print("由于子代理执行过程中涉及异步工具调用，")
            print("完整的最终结果需要在子代理全部完成后才能获取。")
            print("上面已显示两个子代理的调用信息和执行结果预览。")
            print("\n在实际使用中，主 Agent 会汇总两个子代理的报告，")
            print("形成最终的对比分析结果。")
        
        print("\n[PASS] 自定义子代理示例运行完成")
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()


# ============================================================================
# 示例 4: 文件系统 (5.5-5.9)
# ============================================================================

def demo_filesystem():
    """
    示例 4: 文件系统集成
    来自课件 5.5-5.9 节
    """
    print_section("示例 4: 文件系统集成 (课件 5.5-5.9)")
    
    # 获取模型
    model, model_name = get_available_model()
    if model is None:
        print("[FAIL] 未找到可用模型")
        return
    
    print(f"[INFO] 使用模型：{model_name}")
    
    try:
        from deepagents import create_deep_agent
        from deepagents.backends import FilesystemBackend
        from langgraph.checkpoint.memory import InMemorySaver
        
        # 创建测试工作目录
        test_workspace = Path(r"G:\DeepAgents_baseline\workspace\demo_filesystem")
        test_workspace.mkdir(parents=True, exist_ok=True)
        
        # 使用 FilesystemBackend - 课件 5.5 节
        backend = FilesystemBackend(
            root_dir=str(test_workspace),
            virtual_mode=True
        )
        
        print("\n[示例 4.1] 基础文件操作 (课件 5.5)")
        print("-" * 40)
        
        agent = create_deep_agent(
            model=model,
            backend=backend,
            system_prompt="你是一个文件系统操作助手。",
            checkpointer=InMemorySaver(),
        )
        
        config = {"configurable": {"thread_id": "filesystem_demo"}}
        
        # 写入文件
        print("\n[操作] 创建 hello.py")
        result = agent.invoke({
            "messages": [{"role": "user", "content": "创建一个名为 hello.py 的文件，内容是 print('Hello')"}]
        }, config=config)
        print("[PASS] 写入文件完成")
        
        # 读取文件
        print("\n[操作] 读取 hello.py")
        result = agent.invoke({
            "messages": [{"role": "user", "content": "读取 hello.py 文件内容"}]
        }, config=config)
        print("[PASS] 读取文件完成")
        
        # 列出目录
        print("\n[操作] 列出目录")
        result = agent.invoke({
            "messages": [{"role": "user", "content": "列出当前目录的文件"}]
        }, config=config)
        print("[PASS] 列出目录完成")
        
        # 核心工具集表格 - 课件 5.3 节
        print("\n[示例 4.2] 文件系统核心工具集 (课件 5.3)")
        print("-" * 40)
        print("| 工具名称 | 功能描述 |")
        print("|----------|----------|")
        print("| ls | 浏览目录结构 |")
        print("| read_file | 读取文件内容，支持 offset 和 limit 分页读取 |")
        print("| write_file | 创建新文件 |")
        print("| edit_file | 修改文件，支持精确的字符串替换和 replace_all 模式 |")
        print("| glob | 通配符模糊查找文件 |")
        print("| grep | 正则表达式搜索文件内容 |")
        print("| execute | 执行 Shell 命令（需 Sandbox 支持） |")
        
        # edit_file 使用示例 - 课件 5.8 节
        print("\n[示例 4.3] edit_file 工具使用 (课件 5.8)")
        print("-" * 40)
        edit_file_example = """
# edit_file 支持精确的字符串替换
# 防呆设计：要求先读后改

# 1. 先读取文件
result = agent.invoke({
    "messages": [{"role": "user", "content": "读取 /config.py"}]
})

# 2. 再修改文件
result = agent.invoke({
    "messages": [{"role": "user", "content": "将 /config.py 中的 DEBUG=True 改为 DEBUG=False"}]
})
"""
        print(edit_file_example)
        
        # grep 工具使用示例 - 课件 5.9 节
        print("\n[示例 4.4] grep 工具使用 (课件 5.9)")
        print("-" * 40)
        grep_example = """
# 在文件中搜索指定模式
result = agent.invoke({
    "messages": [{"role": "user", "content": "在当前目录下搜索包含 'TODO' 的文件"}]
})

# 使用正则表达式
result = agent.invoke({
    "messages": [{"role": "user", "content": "搜索所有以 def 开头的函数定义"}]
})
"""
        print(grep_example)
        
        # 清理测试目录
        import shutil
        if test_workspace.exists():
            shutil.rmtree(test_workspace)
            print("\n[INFO] 测试目录已清理")
        
        print("\n[PASS] 文件系统示例运行完成")
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()


# ============================================================================
# 示例 5: 综合实践案例 (6.1)
# ============================================================================

def demo_comprehensive():
    """
    示例 5: 综合实践案例
    来自课件 6.1 节
    """
    print_section("示例 5: 综合实践案例 (课件 6.1)")
    
    # 获取模型
    model, model_name = get_available_model()
    if model is None:
        print("[FAIL] 未找到可用模型")
        return
    
    print(f"[INFO] 使用模型：{model_name}")
    
    try:
        from deepagents import create_deep_agent
        from deepagents.backends import FilesystemBackend
        from langgraph.checkpoint.memory import InMemorySaver
        
        # 创建工作目录
        test_workspace = Path(r"G:\DeepAgents_baseline\workspace\demo_comprehensive")
        test_workspace.mkdir(parents=True, exist_ok=True)
        
        # 创建后端
        backend = FilesystemBackend(
            root_dir=str(test_workspace),
            virtual_mode=True
        )
        
        # 配置子代理 - 课件 6.1 节示例
        subagents = [
            {
                "name": "python_researcher",
                "description": "专门研究 Python 语言",
                "model": model,
                "system_prompt": "你是一位专业的 Python 语言研究专家，负责研究 Python 的历史、特性和应用。"
            },
            {
                "name": "rust_researcher", 
                "description": "专门研究 Rust 语言",
                "model": model,
                "system_prompt": "你是一位专业的 Rust 语言研究专家，负责研究 Rust 的内存安全机制和系统编程特性。"
            }
        ]
        
        print("\n[示例 5.1] 多子代理研究任务配置 (课件 6.1)")
        print("-" * 40)
        print("子代理配置:")
        for subagent in subagents:
            print(f"  - {subagent['name']}: {subagent['description']}")
        
        # 创建 Agent
        agent = create_deep_agent(
            model=model,
            backend=backend,
            subagents=subagents,
            checkpointer=InMemorySaver(),
        )
        
        print("\n[PASS] 综合实践 Agent 创建成功")
        print("[INFO] 包含组件:")
        print("  - 规划工具 (TodoListMiddleware)")
        print("  - 子代理 (SubAgentMiddleware) - 2 个专业子代理")
        print("  - 文件系统 (FilesystemMiddleware)")
        
        # 运行测试任务
        print("\n[示例 5.2] 运行综合测试任务")
        print("-" * 40)
        
        config = {"configurable": {"thread_id": "comprehensive_demo"}}
        query = "请同时调研：1. Python 语言的历史起源 2. Rust 语言的内存安全机制。请使用子代理分别处理。"
        
        print(f"[查询]: {query}")
        
        # 使用 debug_agent_stream 展示执行过程
        debug_agent_stream(query, agent, config)
        
        # 执行结果说明 - 课件 6.2 节
        print("\n[示例 5.3] 执行结果 (课件 6.2)")
        print("-" * 40)
        print("Agent 会自动:")
        print("1. 调用 write_todos 规划任务")
        print("2. 启动多个子代理并行研究不同主题")
        print("3. 每个子代理将结果写入文件系统")
        print("4. 主代理聚合结果并生成最终报告")
        
        # 清理测试目录
        import shutil
        if test_workspace.exists():
            shutil.rmtree(test_workspace)
            print("\n[INFO] 测试目录已清理")
        
        print("\n[PASS] 综合实践示例运行完成")
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()


# ============================================================================
# 示例 6: Backend 介绍 (5.4) - 最后实现
# ============================================================================

def demo_backend():
    """
    示例 6: Backend 介绍
    来自课件 5.4 节
    注意：这只是展示代码示例，不实际运行
    """
    print_section("示例 6: Backend 介绍 (课件 5.4)")
    
    # 后端支持表格 - 课件 5.4 节
    print("\n[示例 6.1] 后端支持类型 (课件 5.4)")
    print("-" * 40)
    print("| 后端类型 | 说明 |")
    print("|----------|------|")
    print("| FilesystemBackend | 直接操作本地磁盘 |")
    print("| DockerBackend | 在 Docker 容器中执行，提供隔离环境 |")
    print("| StoreBackend | 存储在数据库中，支持查询和检索 |")
    print("| E2BBackend | 使用 E2B 云端沙箱 |")
    print("| CompositeBackend | 混合模式（如：本地存文件，Docker 跑代码） |")
    
    # Docker 后端示例 - 课件 5.7 节
    print("\n[示例 6.2] Docker 后端示例 (课件 5.7)")
    print("-" * 40)
    docker_example = """
from deepagents import create_deep_agent
from deepagents.backends import DockerBackend

# Docker 后端提供隔离的执行环境
backend = DockerBackend(
    image="python:3.11",
    volumes={"./workspace": "/workspace"}
)

agent = create_deep_agent(
    model=model,
    backend=backend
)

# 在隔离环境中执行代码
result = agent.invoke({
    "messages": [{"role": "user", "content": "运行 /workspace/hello.py"}]
})
"""
    print(docker_example)
    
    print("\n[INFO] Backend 示例仅展示代码，实际运行需要相应环境配置")
    print("[PASS] Backend 介绍完成")


# ============================================================================
# 主函数
# ============================================================================

def main():
    """
    主函数 - 运行所有示例
    """
    print("\n" + "=" * 60)
    print("DeepAgents 阶段四示例脚本")
    print("四大核心内置工具与组件演示")
    print("使用模型：MiniMax-M2.5")
    print("=" * 60)
    
    # 检查模型
    model, model_name = get_available_model()
    if model is None:
        print("\n[FAIL] 未找到可用的 MiniMax-M2.5 模型")
        print("[HINT] 请在 .env 文件中配置 MINIMAX_API_KEY")
        return
    
    print(f"\n[INFO] 模型初始化成功：{model_name}")
    
    # 运行所有示例
    demos = [
        #("系统提示词", demo_system_prompt),
        #("规划工具 (TodoList)", demo_todo_list),
        #("默认子代理", demo_default_sub_agent),
        #("自定义子代理", demo_custom_sub_agent),
        ("文件系统集成", demo_filesystem),
        # ("综合实践案例", demo_comprehensive),
        # ("Backend 介绍", demo_backend),
    ]
    
    # 逐个运行示例
    for i, (name, demo_func) in enumerate(demos, 1):
        try:
            demo_func()
        except Exception as e:
            print(f"\n[ERROR] 示例 {i} ({name}) 运行失败：{e}")
            import traceback
            traceback.print_exc()
    
    # 打印总结
    print("\n" + "=" * 60)
    print("课件重点内容回顾")
    print("=" * 60)
    
    print("\n[INFO] 四大支柱概述")
    print("-" * 40)
    print("| 维度 | 系统提示词 | 规划工具 | 文件系统 | 子代理 |")
    print("| :--- | :--- | :--- | :--- | :--- |")
    print("| 角色定位 | 行为总导演 | 任务架构师 | 上下文仓库 | 执行特派员 |")
    
    print("\n[INFO] 适用场景总结")
    print("-" * 40)
    print("| 场景 | 推荐使用的核心组件 |")
    print("|------|-------------------|")
    print("| 深度研究任务 | 规划工具 + 文件系统 + 子代理 |")
    print("| 自动编程 | 系统提示词 + 文件系统 + 子代理 |")
    print("| 复杂流程自动化 | 规划工具 + 文件系统 |")
    print("| 多 Agent 协作 | 系统提示词 + 子代理 |")
    
    print("\n" + "=" * 60)
    print("所有示例运行完成!")
    print("=" * 60)


if __name__ == "__main__":
    # 确保工作目录正确
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # 运行主函数
    main()
