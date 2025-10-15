"""
File Operation Module
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
        Validate if the file path is within the base path to prevent path traversal attacks
        
        Args:
            file_path: The file path to validate
            base_path: Base path (project root directory)
            
        Returns:
            bool: Whether the path is valid
        """
        return validate_file_path(file_path, base_path)

    @staticmethod
    def backup_file(file_path: str) -> Optional[str]:
        """
        Create file backup
        
        Args:
            file_path: The file path to backup
            
        Returns:
            str: Backup file path, returns None if file does not exist
        """
        try:
            if os.path.exists(file_path):
                backup_path = file_path + ".backup"
                shutil.copy2(file_path, backup_path)
                return backup_path
        except Exception as e:
            raise FileOperationError(f"Failed to create file backup: {str(e)}")
        return None

    @staticmethod
    def write_code_to_file(file_path: str, code: str, project_path: Optional[str] = None) -> bool:
        """
        Safely write code to file
        
        Args:
            file_path: Target file path
            code: Code content to write
            project_path: Project root path, used for path validation
            
        Returns:
            bool: Whether writing was successful
        """
        try:
            # If project path is provided, validate the file path
            if project_path and not FileOperator.validate_path(file_path, project_path):
                raise FileOperationError(f"File path '{file_path}' is outside the project directory scope")
            
            # Create directory (if it doesn't exist)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Create backup (if file already exists)
            FileOperator.backup_file(file_path)
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code)
            
            print(f"Written to file: {file_path}")
            return True
        except Exception as e:
            raise FileOperationError(f"Error writing to file '{file_path}': {str(e)}")

    @staticmethod
    def read_file(file_path: str, project_path: Optional[str] = None) -> str:
        """
        Safely read file content
        
        Args:
            file_path: The file path to read
            project_path: Project root path, used for path validation
            
        Returns:
            str: File content, returns empty string if file does not exist or reading fails
        """
        try:
            # If project path is provided, validate the file path
            if project_path and not FileOperator.validate_path(file_path, project_path):
                raise FileOperationError(f"File path '{file_path}' is outside the project directory scope")
            
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            raise FileOperationError(f"Error reading file '{file_path}': {str(e)}")
        
        return ""