"""
文件操作模块
"""

import os
import shutil
from typing import Optional
from pathlib import Path
from exceptions.project_exceptions import FileOperationError
from utils.helpers import validate_file_path


class FileOperator:
    @staticmethod
    def validate_path(file_path: str, base_path: str) -> bool:
        """
        验证文件路径是否在基础路径内，防止路径遍历攻击
        
        Args:
            file_path: 要验证的文件路径
            base_path: 基础路径（项目根目录）
            
        Returns:
            bool: 路径是否有效
        """
        return validate_file_path(file_path, base_path)

    @staticmethod
    def backup_file(file_path: str) -> Optional[str]:
        """
        创建文件备份
        
        Args:
            file_path: 要备份的文件路径
            
        Returns:
            str: 备份文件路径，如果文件不存在则返回None
        """
        try:
            if os.path.exists(file_path):
                backup_path = file_path + ".backup"
                shutil.copy2(file_path, backup_path)
                return backup_path
        except Exception as e:
            raise FileOperationError(f"创建文件备份失败: {str(e)}")
        return None

    @staticmethod
    def write_code_to_file(file_path: str, code: str, project_path: Optional[str] = None) -> bool:
        """
        安全地将代码写入文件
        
        Args:
            file_path: 目标文件路径
            code: 要写入的代码内容
            project_path: 项目根路径，用于路径验证
            
        Returns:
            bool: 是否写入成功
        """
        try:
            # 如果提供了项目路径，则验证文件路径
            if project_path and not FileOperator.validate_path(file_path, project_path):
                raise FileOperationError(f"文件路径 '{file_path}' 超出项目目录范围")
            
            # 创建目录（如果不存在）
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 创建备份（如果文件已存在）
            FileOperator.backup_file(file_path)
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code)
            
            print(f"已写入文件: {file_path}")
            return True
        except Exception as e:
            raise FileOperationError(f"写入文件 '{file_path}' 时出错: {str(e)}")

    @staticmethod
    def read_file(file_path: str, project_path: Optional[str] = None) -> str:
        """
        安全地读取文件内容
        
        Args:
            file_path: 要读取的文件路径
            project_path: 项目根路径，用于路径验证
            
        Returns:
            str: 文件内容，如果文件不存在或读取失败则返回空字符串
        """
        try:
            # 如果提供了项目路径，则验证文件路径
            if project_path and not FileOperator.validate_path(file_path, project_path):
                raise FileOperationError(f"文件路径 '{file_path}' 超出项目目录范围")
            
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            raise FileOperationError(f"读取文件 '{file_path}' 时出错: {str(e)}")
        
        return ""