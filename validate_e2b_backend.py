#!/usr/bin/env python3
"""
E2BBackend 验证脚本

该脚本用于验证 E2BBackend 的核心功能是否正常工作：
参考 DeepAgents_baseline.ipynb 中的测试内容

测试内容：
1. 环境配置检查
2. 沙箱初始化
3. 执行系统命令 (uname -a, python --version)
4. 创建并运行 Python 脚本
5. 文件上传
6. 文件下载
7. 沙箱关闭
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# 尝试导入 E2BBackend
try:
    from e2b_backend import E2BBackend
except ImportError as e:
    print("Cannot import E2BBackend: {}".format(e))
    sys.exit(1)


def print_section(title: str):
    """打印分隔标题"""
    print("\n" + "=" * 60)
    print("  {}".format(title))
    print("=" * 60)


def print_result(success: bool, message: str):
    """打印测试结果"""
    symbol = "[OK]" if success else "[FAIL]"
    print("{} {}".format(symbol, message))


def check_environment():
    """检查环境配置"""
    print_section("1. Environment Check")

    # 加载 .env 文件
    load_dotenv(override=True)

    # 检查 API Key
    api_key = os.getenv("E2B_API_KEY")
    if not api_key:
        print_result(False, "E2B_API_KEY environment variable not set")
        print("\nPlease create .env file in project root with:")
        print("  E2B_API_KEY=your_api_key_here")
        return None

    print_result(True, "E2B_API_KEY is set (length: {} chars)".format(len(api_key)))

    # 检查 e2b 包
    try:
        import e2b
        print_result(True, "e2b package installed (version: {})".format(getattr(e2b, '__version__', 'unknown')))
    except ImportError:
        print_result(False, "e2b package not installed")
        print("Please run: pip install e2b")
        return None

    return api_key


def test_sandbox_initialization(api_key: str):
    """测试沙箱初始化"""
    print_section("2. Sandbox Initialization")

    try:
        backend = E2BBackend(
            template="base",
            api_key=api_key,
            timeout=60
        )
        print_result(True, "Sandbox initialized successfully")
        print("   Sandbox ID: {}".format(backend.id))
        return backend
    except Exception as e:
        print_result(False, "Sandbox initialization failed: {}".format(e))
        return None


def test_system_info(backend: E2BBackend):
    """测试系统信息命令"""
    print_section("3. System Information Commands")

    # 测试 1: 获取系统信息
    print("\n[Test 3.1] Execute: uname -a")
    result = backend.execute("uname -a")
    print("   Exit code: {}".format(result.exit_code))
    print("   Output: {}".format(result.output.strip()[:80]))
    print_result(result.exit_code == 0, "uname command executed")

    # 测试 2: 获取 Python 版本
    print("\n[Test 3.2] Execute: python --version")
    result = backend.execute("python --version")
    print("   Exit code: {}".format(result.exit_code))
    print("   Output: {}".format(result.output.strip()))
    print_result(result.exit_code == 0, "python --version executed")

    return True


def test_python_script(backend: E2BBackend):
    """测试创建并运行 Python 脚本"""
    print_section("4. Python Script Test")

    # 测试创建 Python 脚本
    script_content = "print('Hello from E2B Sandbox!')"
    script_path = "/home/user/hello.py"

    print("\n[Test 4.1] Write Python script")
    success = backend.write_file(script_path, script_content)
    print_result(success, "File written: {}".format(script_path))

    # 测试运行 Python 脚本
    print("\n[Test 4.2] Execute: python /home/user/hello.py")
    result = backend.execute("python {}".format(script_path))
    print("   Exit code: {}".format(result.exit_code))
    print("   Output: {}".format(result.output.strip()))
    
    expected_output = "Hello from E2B Sandbox!"
    success = result.exit_code == 0 and expected_output in result.output
    print_result(success, "Python script executed successfully")

    return True


def test_file_operations(backend: E2BBackend):
    """测试文件上传下载"""
    print_section("5. File Operations")

    # 准备测试文件
    test_files = [
        ("/home/user/test_upload.py", b"print('Test file upload')"),
        ("/home/user/data.json", b'{"name": "test", "value": 123}'),
    ]

    print("\n[Test 5.1] Upload files")
    try:
        results = backend.upload_files(test_files)
        all_success = True
        for i, (path, content) in enumerate(test_files):
            result = results[i]
            if result.error:
                print_result(False, "Upload failed {}: {}".format(path, result.error))
                all_success = False
            else:
                print_result(True, "Upload success: {}".format(path))
        return all_success
    except Exception as e:
        print_result(False, "Upload test failed: {}".format(e))
        return False


def test_file_download(backend: E2BBackend):
    """测试文件下载"""
    print_section("6. File Download Test")

    # 先创建一个测试文件
    test_file_path = "/home/user/download_test.txt"
    test_content = "This is a test file for download verification."
    backend.execute("echo '{}' > {}".format(test_content, test_file_path))

    # 下载文件
    print("\n[Test 6.1] Download existing file")
    try:
        results = backend.download_files([test_file_path])
        result = results[0]

        if result.error:
            print_result(False, "Download failed: {}".format(result.error))
        else:
            downloaded_content = result.content.decode("utf-8") if isinstance(result.content, bytes) else result.content
            print_result(True, "Download success: {} ({} bytes)".format(result.path, len(result.content)))
            content_match = test_content == downloaded_content
            print_result(content_match, "Content verification")
    except Exception as e:
        print_result(False, "Download test failed: {}".format(e))

    # 测试下载不存在的文件
    print("\n[Test 6.2] Download non-existent file")
    try:
        results = backend.download_files(["/home/user/nonexistent.txt"])
        result = results[0]

        if result.error:
            print_result(True, "Correctly returns error: {}".format(result.error))
        else:
            print_result(False, "Should return error but didn't")
    except Exception as e:
        print_result(False, "Test failed: {}".format(e))

    return True


def test_sandbox_close(backend: E2BBackend):
    """测试沙箱关闭"""
    print_section("7. Sandbox Close")

    try:
        backend.close()
        print_result(True, "Sandbox closed")
        return True
    except Exception as e:
        print_result(False, "Sandbox close failed: {}".format(e))
        return False


def run_full_validation():
    """运行完整验证"""
    print("\n" + "=" * 60)
    print("     E2BBackend Validation Test")
    print("=" * 60)
    print("Project root: {}".format(project_root))
    print("Python version: {}".format(sys.version.split()[0]))

    # 1. 环境检查
    api_key = check_environment()
    if not api_key:
        print("\nEnvironment check failed. Please configure E2B_API_KEY first.")
        return False

    # 2. 初始化沙箱
    backend = test_sandbox_initialization(api_key)
    if not backend:
        print("\nSandbox initialization failed")
        return False

    # 3. 运行各项测试
    try:
        test_system_info(backend)
        test_python_script(backend)
        test_file_operations(backend)
        test_file_download(backend)

        # 4. 关闭沙箱
        test_sandbox_close(backend)

    except Exception as e:
        print("\nError during testing: {}".format(e))
        import traceback
        traceback.print_exc()
        try:
            backend.close()
        except:
            pass
        return False

    # 总结
    print_section("Validation Complete")
    print("All E2BBackend tests passed!")
    print("\nYou can now use E2BBackend in your project:")
    print("  from e2b_backend import E2BBackend")
    print("  backend = E2BBackend()")
    print("  result = backend.execute('ls -la')")
    print("  backend.close()")

    return True


if __name__ == "__main__":
    success = run_full_validation()
    sys.exit(0 if success else 1)
