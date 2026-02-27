#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
容器目录结构一致性测试

验证 DockerBackend 的 upload_files、download_files、execute 等方法
操作的目录结构与容器内实际目录结构一致。

测试内容：
1. 根目录文件操作
2. 子目录创建和文件操作
3. 多层嵌套目录
4. 文件上传下载一致性
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from docker_backend import DockerBackend


def clean_workspace(backend: DockerBackend):
    """清空工作目录"""
    backend.execute("rm -rf /workspace/*")
    backend.execute("mkdir -p /workspace")


def test_root_directory_operations(backend: DockerBackend):
    """测试根目录文件操作"""
    print("\n[测试 1] 根目录文件操作")
    
    # 上传文件到根目录
    backend.upload_files([
        ("root1.txt", b"Root file 1"),
        ("root2.txt", b"Root file 2"),
        ("root3.json", b'{"key": "value"}'),
    ])
    
    # 验证文件存在
    result = backend.execute("ls -la /workspace/")
    print(f"  容器内文件列表:\n{result.output}")
    
    assert "root1.txt" in result.output, "root1.txt 不存在"
    assert "root2.txt" in result.output, "root2.txt 不存在"
    assert "root3.json" in result.output, "root3.json 不存在"
    
    # 验证内容
    result = backend.execute("cat /workspace/root1.txt")
    assert "Root file 1" in result.output, "root1.txt 内容错误"
    
    print("  ✓ 根目录文件操作正常")
    return True


def test_subdirectory_operations(backend: DockerBackend):
    """测试子目录文件操作"""
    print("\n[测试 2] 子目录文件操作")
    
    # 创建子目录并上传文件
    backend.execute("mkdir -p /workspace/subdir1")
    backend.upload_files([
        ("subdir1/file1.txt", b"Subdir file 1"),
        ("subdir1/file2.txt", b"Subdir file 2"),
    ])
    
    # 验证文件存在
    result = backend.execute("ls -la /workspace/subdir1/")
    print(f"  子目录文件列表:\n{result.output}")
    
    assert "file1.txt" in result.output, "file1.txt 不存在"
    assert "file2.txt" in result.output, "file2.txt 不存在"
    
    # 验证内容
    result = backend.execute("cat /workspace/subdir1/file1.txt")
    assert "Subdir file 1" in result.output, "file1.txt 内容错误"
    
    print("  ✓ 子目录文件操作正常")
    return True


def test_nested_directory_operations(backend: DockerBackend):
    """测试多层嵌套目录"""
    print("\n[测试 3] 多层嵌套目录操作")
    
    # 创建嵌套目录结构
    backend.execute("mkdir -p /workspace/level1/level2/level3")
    
    # 上传文件到不同层级
    backend.upload_files([
        ("level1/l1.txt", b"Level 1"),
        ("level1/level2/l2.txt", b"Level 2"),
        ("level1/level2/level3/l3.txt", b"Level 3"),
    ])
    
    # 验证所有文件
    result = backend.execute("find /workspace/level1 -type f")
    print(f"  所有文件:\n{result.output}")
    
    assert "level1/l1.txt" in result.output, "l1.txt 不存在"
    assert "level1/level2/l2.txt" in result.output, "l2.txt 不存在"
    assert "level1/level2/level3/l3.txt" in result.output, "l3.txt 不存在"
    
    # 验证各层文件内容
    result = backend.execute("cat /workspace/level1/l1.txt")
    assert "Level 1" in result.output
    
    result = backend.execute("cat /workspace/level1/level2/l2.txt")
    assert "Level 2" in result.output
    
    result = backend.execute("cat /workspace/level1/level2/level3/l3.txt")
    assert "Level 3" in result.output
    
    print("  ✓ 多层嵌套目录操作正常")
    return True


def test_download_consistency(backend: DockerBackend):
    """测试上传下载一致性"""
    print("\n[测试 4] 上传下载一致性")
    
    # 上传文件
    test_content = b"Test content for consistency check"
    backend.upload_files([("consistency.txt", test_content)])
    
    # 下载文件
    responses = backend.download_files(["/workspace/consistency.txt"])
    
    assert responses[0].error is None, f"下载失败: {responses[0].error}"
    assert responses[0].content == test_content, f"内容不匹配: {responses[0].content} != {test_content}"
    
    print(f"  上传内容: {test_content}")
    print(f"  下载内容: {responses[0].content}")
    print("  ✓ 上传下载内容一致")
    
    # 测试子目录文件
    backend.execute("mkdir -p /workspace/test_dir")
    backend.upload_files([("test_dir/nested.txt", b"Nested content")])
    
    responses = backend.download_files(["/workspace/test_dir/nested.txt"])
    assert responses[0].content == b"Nested content", "子目录文件内容不一致"
    
    print("  ✓ 子目录上传下载一致")
    return True


def test_mixed_operations(backend: DockerBackend):
    """测试混合操作"""
    print("\n[测试 5] 混合操作")
    
    # 使用 execute 创建目录
    backend.execute("mkdir -p /workspace/mixed/dir1 /workspace/mixed/dir2")
    
    # 使用 upload 上传文件
    backend.upload_files([
        ("mixed/file1.txt", b"File 1"),
        ("mixed/dir1/file2.txt", b"File 2"),
        ("mixed/dir2/file3.txt", b"File 3"),
    ])
    
    # 使用 download 验证
    r1 = backend.download_files(["/workspace/mixed/file1.txt"])
    r2 = backend.download_files(["/workspace/mixed/dir1/file2.txt"])
    r3 = backend.download_files(["/workspace/mixed/dir2/file3.txt"])
    
    assert r1[0].error is None, f"file1.txt 下载失败: {r1[0].error}"
    assert r1[0].content == b"File 1", f"file1.txt 内容错误: {r1[0].content}"
    
    assert r2[0].error is None, f"file2.txt 下载失败: {r2[0].error}"
    assert r2[0].content == b"File 2", f"file2.txt 内容错误: {r2[0].content}"
    
    assert r3[0].error is None, f"file3.txt 下载失败: {r3[0].error}"
    assert r3[0].content == b"File 3", f"file3.txt 内容错误: {r3[0].content}"
    
    print("  ✓ 混合操作正常")
    return True


def test_directory_structure_sync(backend: DockerBackend):
    """测试目录结构同步"""
    print("\n[测试 6] 目录结构同步")
    
    # 清理并创建结构
    backend.execute("rm -rf /workspace/project")
    backend.execute("mkdir -p /workspace/project/src /workspace/project/tests /workspace/project/docs")
    
    # 上传文件
    backend.upload_files([
        ("project/main.py", b"def main(): pass"),
        ("project/src/__init__.py", b""),
        ("project/src/module.py", b"class Module: pass"),
        ("project/tests/test_module.py", b"def test(): pass"),
        ("project/docs/README.md", b"# Project"),
    ])
    
    # 获取容器内完整目录结构
    result = backend.execute("find /workspace/project -type f")
    print(f"  容器内目录结构:\n{result.output}")
    
    # 验证关键路径存在
    assert "/workspace/project/main.py" in result.output, "main.py 不存在"
    assert "/workspace/project/src/__init__.py" in result.output, "__init__.py 不存在"
    assert "/workspace/project/src/module.py" in result.output, "module.py 不存在"
    assert "/workspace/project/tests/test_module.py" in result.output, "test_module.py 不存在"
    assert "/workspace/project/docs/README.md" in result.output, "README.md 不存在"
    
    print("  ✓ 目录结构同步正常")
    return True


def test_binary_file_operations(backend: DockerBackend):
    """测试二进制文件操作"""
    print("\n[测试 7] 二进制文件操作")
    
    # 上传二进制数据
    binary_data = bytes(range(256))  # 0-255
    backend.upload_files([("binary/file.bin", binary_data)])
    
    # 下载验证
    response = backend.download_files(["/workspace/binary/file.bin"])
    assert response[0].content == binary_data, "二进制内容不一致"
    
    # 容器内验证
    result = backend.execute("ls -la /workspace/binary/file.bin")
    assert "256" in result.output, "文件大小不正确"
    
    print("  ✓ 二进制文件操作正常")
    return True


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("容器目录结构一致性测试")
    print("=" * 60)
    
    backend = None
    passed = 0
    failed = 0
    
    try:
        backend = DockerBackend()
        print(f"\n容器: {backend.container_name}")
        print(f"容器 ID: {backend.id[:12]}")
        
        # 清理工作目录
        clean_workspace(backend)
        
        # 运行各项测试
        tests = [
            test_root_directory_operations,
            test_subdirectory_operations,
            test_nested_directory_operations,
            test_download_consistency,
            test_mixed_operations,
            test_directory_structure_sync,
            test_binary_file_operations,
        ]
        
        for test in tests:
            try:
                test(backend)
                passed += 1
            except Exception as e:
                print(f"  ✗ 测试失败: {e}")
                import traceback
                traceback.print_exc()
                failed += 1
        
    except Exception as e:
        print(f"\n❌ 创建 DockerBackend 失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        if backend:
            # 不关闭容器，保持运行
            print(f"\n✓ 断开连接，容器保持运行")
            # backend.close()
    
    # 总结
    print("\n" + "=" * 60)
    print(f"测试总结: {passed}/{passed + failed} 通过")
    if failed > 0:
        print(f"失败: {failed}")
    else:
        print("🎉 所有测试通过！")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
