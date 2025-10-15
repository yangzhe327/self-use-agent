"""
通用工具类
"""

import os
import json
import subprocess
import shutil
from typing import Any, Optional, Dict, List
from pathlib import Path


def validate_file_path(file_path: str, base_path: str) -> bool:
    """
    验证文件路径是否在基础路径内，防止路径遍历攻击
    
    Args:
        file_path: 要验证的文件路径
        base_path: 基础路径（项目根目录）
        
    Returns:
        bool: 路径是否有效
    """
    try:
        # 将路径解析为绝对路径
        abs_file_path = Path(file_path).resolve()
        abs_base_path = Path(base_path).resolve()
        
        # 检查文件路径是否在基础路径内
        return str(abs_file_path).startswith(str(abs_base_path))
    except Exception:
        return False


def find_executable(executable_name: str) -> Optional[str]:
    """
    查找可执行文件的完整路径
    
    Args:
        executable_name: 可执行文件名
        
    Returns:
        str: 可执行文件的完整路径，如果未找到则返回None
    """
    try:
        # 首先尝试使用shutil.which查找
        executable_path = shutil.which(executable_name)
        if executable_path:
            return executable_path
        
        # 在Windows上，也尝试查找.cmd版本
        if os.name == 'nt':
            executable_cmd_path = shutil.which(executable_name + '.cmd')
            if executable_cmd_path:
                return executable_cmd_path
                
            # 尝试.bat版本
            executable_cmd_path = shutil.which(executable_name + '.bat')
            if executable_cmd_path:
                return executable_cmd_path
        
        return None
    except Exception:
        return None


def run_subprocess_command(
    command: List[str], 
    cwd: Optional[str] = None,
    timeout: Optional[int] = None
) -> subprocess.CompletedProcess:
    """
    运行子进程命令
    
    Args:
        command: 命令列表
        cwd: 工作目录
        timeout: 超时时间（秒）
        
    Returns:
        subprocess.CompletedProcess: 命令执行结果
    """
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout
    )


def safe_json_loads(json_string: str) -> Optional[Any]:
    """
    安全地解析JSON字符串
    
    Args:
        json_string: JSON字符串
        
    Returns:
        解析后的对象，如果解析失败则返回None
    """
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return None