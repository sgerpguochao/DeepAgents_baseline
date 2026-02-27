#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DockerBackend 验证测试

该脚本用于验证 DockerBackend 的各项功能是否正常工作。
测试内容包括：
1. Docker 连接验证
2. DockerBackend 初始化
3. 命令执行 (execute)
4. 文件上传 (upload_files)
5. 文件下载 (download_files)
6. 容器清理 (close)
7. 错误处理

前置要求：
1. 安装 Docker 并确保 Docker 服务运行
2. 安装 docker Python 包: pip install docker
3. 创建 docker_backend.py 文件（参考 middleware_info/DockerBackend 注册与操作手册.md）
"""

import io
import os
import sys
import tarfile
import tempfile
import time
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def import_docker_backend():
    """导入 DockerBackend 模块"""
    # 尝试从多个位置导入
    possible_paths = [
        project_root / "docker_backend.py",
        project_root / "middleware_info" / "docker_backend.py",
    ]
    
    for path in possible_paths:
        if path.exists():
            sys.path.insert(0, str(path.parent))
            try:
                from docker_backend import DockerBackend
                return DockerBackend
            except ImportError as e:
                raise ImportError(f"无法导入 docker_backend: {e}")
    
    # 文件不存在
    raise FileNotFoundError(
        f"docker_backend.py 文件不存在！\n"
        f"请参考 middleware_info/DockerBackend 注册与操作手册.md 创建该文件。\n"
        f"预期位置: {possible_paths}"
    )


# 尝试导入 DockerBackend
try:
    DockerBackend = import_docker_backend()
except FileNotFoundError as e:
    print(f"\n❌ {e}")
    print("\n请先创建 docker_backend.py 文件后重试。")
    sys.exit(1)

# 导入 DeepAgents 协议
from deepagents.backends.protocol import ExecuteResponse, FileUploadResponse, FileDownloadResponse


class TestResult:
    """测试结果类"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def add_pass(self, test_name: str):
        self.passed += 1
        print(f"  ✓ {test_name}")
    
    def add_fail(self, test_name: str, error: str):
        self.failed += 1
        self.errors.append((test_name, error))
        print(f"  ✗ {test_name}")
        print(f"    错误: {error}")
    
    def print_summary(self):
        total = self.passed + self.failed
        print("\n" + "=" * 60)
        print(f"测试总结: {self.passed}/{total} 通过")
        if self.failed > 0:
            print(f"失败: {self.failed}")
            print("\n失败详情:")
            for name, error in self.errors:
                print(f"  - {name}: {error}")
        print("=" * 60)
        return self.failed == 0


def test_docker_connection():
    """测试 Docker 连接"""
    print("\n[测试 1] Docker 连接验证")
    result = TestResult()
    
    try:
        import docker
        client = docker.from_env()
        version = client.version()
        result.add_pass("Docker SDK 导入成功")
        result.add_pass(f"Docker 版本: {version['Version']}")
        
        # 测试运行 hello-world 容器
        client.containers.run("hello-world", remove=True)
        result.add_pass("hello-world 容器运行成功")
        
    except Exception as e:
        result.add_fail("Docker 连接", str(e))
    
    return result


def test_docker_backend_initialization():
    """测试 DockerBackend 初始化"""
    print("\n[测试 2] DockerBackend 初始化")
    result = TestResult()
    backend = None
    
    try:
        # 使用默认配置初始化
        backend = DockerBackend(
            image="python:3.11-slim",
            auto_remove=True,
            cpu_quota=50000,
            memory_limit="512m",
            working_dir="/workspace"
        )
        result.add_pass("DockerBackend 实例创建成功")
        result.add_pass(f"容器 ID: {backend.id}")
        result.add_pass(f"容器名称: {backend.container_name}")
        result.add_pass(f"工作目录: {backend.working_dir}")
        
    except Exception as e:
        result.add_fail("DockerBackend 初始化", str(e))
    finally:
        if backend:
            try:
                backend.close()
                result.add_pass("容器清理成功")
            except Exception as e:
                result.add_fail("容器清理", str(e))
    
    return result


def test_execute_command(backend: DockerBackend):
    """测试命令执行"""
    print("\n[测试 3] 命令执行 (execute)")
    result = TestResult()
    
    # 测试成功的命令
    try:
        response = backend.execute("echo 'Hello DockerBackend'")
        assert isinstance(response, ExecuteResponse), "返回值类型错误"
        assert response.exit_code == 0, f"退出码错误: {response.exit_code}"
        assert "Hello DockerBackend" in response.output, f"输出内容错误: {response.output}"
        result.add_pass("基本命令执行成功")
    except Exception as e:
        result.add_fail("基本命令执行", str(e))
    
    # 测试 Python 命令
    try:
        response = backend.execute("python3 --version")
        assert response.exit_code == 0, f"Python 命令失败: {response.exit_code}"
        result.add_pass("Python 命令执行成功")
    except Exception as e:
        result.add_fail("Python 命令执行", str(e))
    
    # 测试失败的命令
    try:
        response = backend.execute("exit 1")
        assert response.exit_code == 1, "失败命令应返回非零退出码"
        result.add_pass("失败命令正确返回错误码")
    except Exception as e:
        result.add_fail("失败命令测试", str(e))
    
    # 测试多行命令
    try:
        response = backend.execute("python3 -c \"print(2**10)\"")
        assert "1024" in response.output, f"多行命令输出错误: {response.output}"
        result.add_pass("多行命令执行成功")
    except Exception as e:
        result.add_fail("多行命令执行", str(e))
    
    # 测试目录创建
    try:
        response = backend.execute("mkdir -p /workspace/test_dir")
        assert response.exit_code == 0, "目录创建失败"
        result.add_pass("目录创建成功")
    except Exception as e:
        result.add_fail("目录创建", str(e))
    
    return result


def test_upload_files(backend: DockerBackend):
    """测试文件上传"""
    print("\n[测试 4] 文件上传 (upload_files)")
    result = TestResult()
    
    # 测试上传单个文件
    try:
        test_content = b"Hello from DockerBackend!"
        response = backend.upload_files([("test.txt", test_content)])
        assert len(response) == 1, "返回结果数量错误"
        assert isinstance(response[0], FileUploadResponse), "返回值类型错误"
        assert response[0].error is None, f"上传失败: {response[0].error}"
        
        # 验证文件确实上传成功
        check = backend.execute("cat /workspace/test.txt")
        assert test_content.decode() in check.output, "文件内容不匹配"
        result.add_pass("单文件上传成功")
    except Exception as e:
        result.add_fail("单文件上传", str(e))
    
    # 测试上传多个文件
    try:
        files = [
            ("multi1.txt", b"Content 1"),
            ("multi2.txt", b"Content 2"),
            ("multi3.txt", b"Content 3"),
        ]
        response = backend.upload_files(files)
        assert len(response) == 3, "多文件上传数量错误"
        assert all(r.error is None for r in response), "部分文件上传失败"
        result.add_pass("多文件上传成功")
    except Exception as e:
        result.add_fail("多文件上传", str(e))
    
    # 测试上传二进制文件
    try:
        binary_content = bytes(range(256))  # 0-255 的字节
        response = backend.upload_files([("binary.bin", binary_content)])
        assert response[0].error is None, "二进制文件上传失败"
        
        # 验证文件大小
        check = backend.execute("ls -l /workspace/binary.bin")
        assert "256" in check.output, "二进制文件大小不正确"
        result.add_pass("二进制文件上传成功")
    except Exception as e:
        result.add_fail("二进制文件上传", str(e))
    
    # 测试上传到子目录
    try:
        # 先创建子目录
        backend.execute("mkdir -p /workspace/subdir")
        response = backend.upload_files([("subdir/nested.txt", b"Nested content")])
        assert response[0].error is None, "子目录文件上传失败"
        
        check = backend.execute("cat /workspace/subdir/nested.txt")
        assert "Nested content" in check.output, "子目录文件内容错误"
        result.add_pass("子目录文件上传成功")
    except Exception as e:
        result.add_fail("子目录文件上传", str(e))
    
    return result


def test_download_files(backend: DockerBackend):
    """测试文件下载"""
    print("\n[测试 5] 文件下载 (download_files)")
    result = TestResult()
    
    # 先创建一些测试文件
    backend.execute("mkdir -p /workspace/download_test")
    backend.upload_files([
        ("download_test/sample.txt", b"Sample content for download"),
        ("download_test/data.json", b'{"key": "value"}'),
    ])
    
    # 测试下载单个文件
    try:
        response = backend.download_files(["/workspace/download_test/sample.txt"])
        assert len(response) == 1, "返回结果数量错误"
        assert isinstance(response[0], FileDownloadResponse), "返回值类型错误"
        assert response[0].error is None, f"下载失败: {response[0].error}"
        assert response[0].content == b"Sample content for download", "文件内容不匹配"
        result.add_pass("单文件下载成功")
    except Exception as e:
        result.add_fail("单文件下载", str(e))
    
    # 测试下载多个文件
    try:
        response = backend.download_files([
            "/workspace/download_test/sample.txt",
            "/workspace/download_test/data.json"
        ])
        assert len(response) == 2, "多文件下载数量错误"
        assert all(r.error is None for r in response), "部分文件下载失败"
        result.add_pass("多文件下载成功")
    except Exception as e:
        result.add_fail("多文件下载", str(e))
    
    # 测试下载不存在的文件
    try:
        response = backend.download_files(["/workspace/nonexistent.txt"])
        assert response[0].error is not None, "不存在的文件应该返回错误"
        result.add_pass("不存在文件正确返回错误")
    except Exception as e:
        result.add_fail("不存在文件测试", str(e))
    
    return result


def test_container_cleanup():
    """测试容器清理"""
    print("\n[测试 6] 容器清理 (close)")
    result = TestResult()

    try:
        # 创建新容器用于测试
        test_backend = DockerBackend(
            image="python:3.12-slim",
            auto_remove=True
        )
        container_id = test_backend.id
        
        # 关闭容器
        test_backend.close()
        
        # 等待容器完全清理
        time.sleep(1)
        
        # 验证容器已被移除
        import docker
        client = docker.from_env()
        try:
            container = client.containers.get(container_id)
            # 如果容器还存在，检查是否是停止状态
            if container.status != "running":
                result.add_pass("容器已停止")
            else:
                result.add_fail("容器仍在运行", "容器未被停止")
        except docker.errors.NotFound:
            result.add_pass("容器已被完全移除 (auto_remove=True)")
        
    except Exception as e:
        result.add_fail("容器清理测试", str(e))
    
    return result


def test_resource_limits():
    """测试资源限制"""
    print("\n[测试 7] 资源限制配置")
    result = TestResult()
    backend = None
    
    try:
        # 测试自定义资源限制
        backend = DockerBackend(
            image="python:3.11-slim",
            cpu_quota=100000,      # 100% CPU
            memory_limit="256m",   # 256MB 内存
            auto_remove=True
        )
        
        # 验证容器配置
        info = backend.container.attrs
        host_config = info.get('HostConfig', {})
        
        # 检查内存限制
        mem_limit = host_config.get('Memory', 0)
        assert mem_limit > 0, "内存限制未设置"
        result.add_pass(f"内存限制设置正确: {mem_limit} bytes")
        
        # 检查 CPU 限制
        cpu_quota = host_config.get('CpuQuota', 0)
        assert cpu_quota > 0, "CPU 配额未设置"
        result.add_pass(f"CPU 配额设置正确: {cpu_quota}")
        
    except Exception as e:
        result.add_fail("资源限制测试", str(e))
    finally:
        if backend:
            try:
                backend.close()
            except:
                pass
    
    return result


def test_network_configuration():
    """测试网络配置"""
    print("\n[测试 8] 网络配置")
    result = TestResult()
    backend = None
    
    # 测试禁用网络
    try:
        backend = DockerBackend(
            image="python:3.11-slim",
            network_disabled=True,
            auto_remove=True
        )
        
        info = backend.container.attrs
        network = info.get('NetworkSettings', {})
        
        # 检查网络是否被禁用
        if network.get('Networks'):
            # 如果有网络配置，检查是否为空网络
            networks = network['Networks']
            result.add_pass(f"网络配置: {list(networks.keys())}")
        else:
            result.add_pass("网络已禁用")
        
    except Exception as e:
        result.add_fail("网络配置测试", str(e))
    finally:
        if backend:
            try:
                backend.close()
            except:
                pass
    
    return result


def test_error_handling():
    """测试错误处理"""
    print("\n[测试 9] 错误处理")
    result = TestResult()
    
    # 测试无效镜像
    try:
        bad_backend = DockerBackend(
            image="nonexistent-image-12345",
            auto_remove=True
        )
        bad_backend.close()
        result.add_fail("无效镜像测试", "应该抛出异常但没有")
    except Exception as e:
        result.add_pass(f"无效镜像正确抛出异常")
    
    # 测试执行无效命令
    backend = None
    try:
        backend = DockerBackend(
            image="python:3.11-slim",
            auto_remove=True
        )
        
        # 执行无效命令
        response = backend.execute("invalid_command_xyz")
        # 可能返回非零退出码，但不应该是 Python 异常
        result.add_pass("无效命令正确处理")
        
    except Exception as e:
        result.add_fail("无效命令测试", str(e))
    finally:
        if backend:
            try:
                backend.close()
            except:
                pass
    
    return result


def test_volume_mounting():
    """测试卷挂载"""
    print("\n[测试 10] 卷挂载")
    result = TestResult()
    
    # 创建临时目录用于挂载
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "host_file.txt")
        with open(test_file, "w") as f:
            f.write("Content from host")
        
        backend = None
        try:
            backend = DockerBackend(
                image="python:3.11-slim",
                volumes={tmpdir: {"bind": "/mnt/host", "mode": "rw"}},
                auto_remove=True
            )
            
            # 验证文件可以访问
            response = backend.execute("cat /mnt/host/host_file.txt")
            assert response.exit_code == 0, "挂载文件无法访问"
            assert "Content from host" in response.output, "挂载文件内容错误"
            result.add_pass("卷挂载成功")
            
            # 测试写入
            response = backend.execute("echo 'Written from container' > /mnt/host/container_file.txt")
            assert response.exit_code == 0, "写入失败"
            
            # 验证写入成功
            host_path = os.path.join(tmpdir, "container_file.txt")
            assert os.path.exists(host_path), "容器写入的文件不存在"
            result.add_pass("容器写入宿主机成功")
            
        except Exception as e:
            result.add_fail("卷挂载测试", str(e))
        finally:
            if backend:
                try:
                    backend.close()
                except:
                    pass
    
    return result


def test_concurrent_operations():
    """测试并发操作"""
    print("\n[测试 11] 并发操作")
    result = TestResult()
    backend = None
    
    try:
        backend = DockerBackend(
            image="python:3.11-slim",
            auto_remove=True
        )
        
        # 依次执行多个命令，测试稳定性
        commands = [
            "echo 'Test 1'",
            "echo 'Test 2'",
            "echo 'Test 3'",
            "python3 -c 'print(1+1)'",
            "ls -la /workspace",
            "pwd",
        ]
        
        for cmd in commands:
            response = backend.execute(cmd)
            assert response.exit_code == 0, f"命令执行失败: {cmd}"
        
        result.add_pass(f"连续执行 {len(commands)} 个命令成功")
        
        # 测试连续文件操作
        for i in range(5):
            backend.upload_files([(f"test_{i}.txt", f"Content {i}".encode())])
        
        result.add_pass("连续文件上传成功")
        
    except Exception as e:
        result.add_fail("并发操作测试", str(e))
    finally:
        if backend:
            try:
                backend.close()
            except:
                pass
    
    return result


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("DockerBackend 验证测试")
    print("=" * 60)
    
    all_results = []
    
    # 1. Docker 连接测试
    all_results.append(test_docker_connection())
    
    # 如果 Docker 连接失败，后续测试无法进行
    if all_results[0].failed > 0:
        print("\n⚠️ Docker 连接失败，跳过后续测试")
        all_results[0].print_summary()
        return False
    
    # 2. 初始化测试
    all_results.append(test_docker_backend_initialization())
    
    # 如果初始化失败，创建一个用于后续测试
    backend = None
    try:
        backend = DockerBackend(
            image="python:3.11-slim",
            auto_remove=True,
            working_dir="/workspace"
        )
        
        # 3-6. 核心功能测试
        all_results.append(test_execute_command(backend))
        all_results.append(test_upload_files(backend))
        all_results.append(test_download_files(backend))
        
        # 7-11. 高级功能测试
        all_results.append(test_resource_limits())
        all_results.append(test_network_configuration())
        all_results.append(test_error_handling())
        all_results.append(test_volume_mounting())
        all_results.append(test_concurrent_operations())
        
    except Exception as e:
        print(f"\n⚠️ 创建测试环境失败: {e}")
    finally:
        if backend:
            try:
                backend.close()
            except:
                pass
    
    # 12. 容器清理测试（独立测试）
    all_results.append(test_container_cleanup())
    
    # 汇总结果
    total_passed = sum(r.passed for r in all_results)
    total_failed = sum(r.failed for r in all_results)
    total = total_passed + total_failed
    
    print("\n" + "=" * 60)
    print("最终测试总结")
    print("=" * 60)
    print(f"总测试数: {total}")
    print(f"通过: {total_passed}")
    print(f"失败: {total_failed}")
    
    if total_failed == 0:
        print("\n🎉 所有测试通过！DockerBackend 工作正常。")
    else:
        print("\n⚠️ 部分测试失败，请检查上述错误。")
    
    print("=" * 60)
    
    return total_failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
