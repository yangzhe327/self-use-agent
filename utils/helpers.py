"""
General Utilities
"""

import os
import json
import subprocess
import shutil
from typing import Any, Optional, Dict, List
from pathlib import Path


def validate_file_path(file_path: str, base_path: str) -> bool:
    """
    Validate if the file path is within the base path to prevent path traversal attacks
    
    Args:
        file_path: The file path to validate
        base_path: Base path (project root directory)
        
    Returns:
        bool: Whether the path is valid
    """
    try:
        # Resolve paths to absolute paths
        abs_file_path = Path(file_path).resolve()
        abs_base_path = Path(base_path).resolve()
        
        # Check if file path is within base path
        return str(abs_file_path).startswith(str(abs_base_path))
    except Exception:
        return False


def find_executable(executable_name: str) -> Optional[str]:
    """
    Find the full path of an executable file
    
    Args:
        executable_name: Executable file name
        
    Returns:
        str: Full path of the executable file, returns None if not found
    """
    try:
        # First try to find using shutil.which
        executable_path = shutil.which(executable_name)
        if executable_path:
            return executable_path
        
        # On Windows, also try to find .cmd version
        if os.name == 'nt':
            executable_cmd_path = shutil.which(executable_name + '.cmd')
            if executable_cmd_path:
                return executable_cmd_path
                
            # Try .bat version
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
    Run subprocess command
    
    Args:
        command: Command list
        cwd: Working directory
        timeout: Timeout (seconds)
        
    Returns:
        subprocess.CompletedProcess: Command execution result
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
    Safely parse JSON string
    
    Args:
        json_string: JSON string
        
    Returns:
        Parsed object, returns None if parsing fails
    """
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return None