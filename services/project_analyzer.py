"""
Project Analysis Module
"""

import os
import json
from typing import List, Dict, Any, Optional
from utils.helpers import safe_json_loads
from services.file_operator import FileOperator
from exceptions.project_exceptions import ProjectAnalysisError


class ProjectAnalyzer:
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.project_info: Dict[str, Any] = {}
        # Configurable list of files and directories
        self.key_files = [
            'package.json',
            'vite.config.js',
            'webpack.config.js',
            'tsconfig.json',
            'babel.config.js',
            'next.config.js',
            'nuxt.config.js'
        ]
        self.key_directories = [
            'src',
            'public',
            'assets',
            'components',
            'pages',
            'routes',
            'views'
        ]
        self.component_extensions = ['.js', '.jsx', '.ts', '.tsx', '.vue']

    def analyze_project_structure(self) -> Dict[str, Any]:
        """
        Analyze project structure and key files
        """
        try:
            # Read key files
            for file_name in self.key_files:
                self.project_info[file_name] = self.read_file_content(file_name)
            
            # Find files in key directories
            for dir_name in self.key_directories:
                self.project_info[dir_name] = self.find_files_in_directory(dir_name, self.component_extensions)
            
            # Special handling of common structures in src directory
            src_subdirs = ['components', 'pages', 'views', 'routes', 'utils', 'hooks', 'services']
            for subdir in src_subdirs:
                self.project_info[f'src/{subdir}'] = self.find_files_in_directory(f'src/{subdir}', self.component_extensions)
            
            return self.project_info
        except Exception as e:
            raise ProjectAnalysisError(f"Project analysis failed: {str(e)}")

    def find_files_in_directory(self, folder: str, exts: List[str]) -> List[str]:
        """
        Find files with specific extensions in the specified directory
        
        Args:
            folder: Directory to search
            exts: List of file extensions
            
        Returns:
            List[str]: List of found file paths
        """
        result: List[str] = []
        abs_folder = os.path.join(self.project_path, folder)
        if not os.path.exists(abs_folder):
            return result
            
        try:
            for root, _, files in os.walk(abs_folder):
                for f in files:
                    if any(f.endswith(ext) for ext in exts):
                        result.append(os.path.relpath(os.path.join(root, f), self.project_path))
        except Exception as e:
            raise ProjectAnalysisError(f"Error searching directory '{folder}': {str(e)}")
            
        return result

    def read_file_content(self, rel_path: str) -> str:
        """
        Read file in the project
        
        Args:
            rel_path: File path relative to project root directory
            
        Returns:
            str: File content, returns empty string if file does not exist or reading fails
        """
        return FileOperator.read_file(
            os.path.join(self.project_path, rel_path),
            self.project_path
        )