"""
项目分析模块
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
        # 可配置的文件和目录列表
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

    def analyze(self) -> Dict[str, Any]:
        """
        分析项目结构和关键文件
        """
        try:
            # 读取关键文件
            for file_name in self.key_files:
                self.project_info[file_name] = self.read_file(file_name)
            
            # 查找关键目录中的文件
            for dir_name in self.key_directories:
                self.project_info[dir_name] = self.find_files(dir_name, self.component_extensions)
            
            # 特殊处理src目录中的常见结构
            src_subdirs = ['components', 'pages', 'views', 'routes', 'utils', 'hooks', 'services']
            for subdir in src_subdirs:
                self.project_info[f'src/{subdir}'] = self.find_files(f'src/{subdir}', self.component_extensions)
            
            return self.project_info
        except Exception as e:
            raise ProjectAnalysisError(f"项目分析失败: {str(e)}")

    def find_files(self, folder: str, exts: List[str]) -> List[str]:
        """
        查找指定目录中具有特定扩展名的文件
        
        Args:
            folder: 要搜索的目录
            exts: 文件扩展名列表
            
        Returns:
            List[str]: 找到的文件路径列表
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
            raise ProjectAnalysisError(f"搜索目录 '{folder}' 时出错: {str(e)}")
            
        return result

    def read_file(self, rel_path: str) -> str:
        """
        读取项目中的文件
        
        Args:
            rel_path: 相对于项目根目录的文件路径
            
        Returns:
            str: 文件内容，如果文件不存在或读取失败则返回空字符串
        """
        return FileOperator.read_file(
            os.path.join(self.project_path, rel_path),
            self.project_path
        )