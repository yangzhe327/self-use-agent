"""
Main Application Class
"""

import os
import json
import sys
from typing import Dict, Any, Optional, Tuple
from services.project_analyzer import ProjectAnalyzer
from services.ai_interactor import AIInteractor
from services.config import Config
from commands.project_commands import ProjectCommands
from commands.ai_commands import AICommands
from exceptions.project_exceptions import ProjectBaseException


class UIProjectAgent:
    def __init__(self, project_path: str):
        self.project_path = os.path.abspath(project_path)
        self.analyzer = ProjectAnalyzer(project_path)
        self.config = Config()
        self.ai = AIInteractor()
        self.ai.set_agent(self)  # Set agent reference
        self.context_initialized = False
        self.project_commands = ProjectCommands(project_path)
        self.ai_commands = AICommands(self.ai, project_path, self.analyzer)

    def analyze_project(self) -> None:
        """
        Analyze the project structure and generate project information
        """
        try:
            if not self.context_initialized:
                self.ai.messages.append({
                    "role": "system",
                    "content": (
                        "You are a senior UI development engineer and UX designer, proficient in front-end architecture, interaction design, and user experience optimization. "
                        "Your task is to provide professional analysis and suggestions based on the project structure and user requirements, and generate high-quality, directly applicable code. "
                        "When outputting, please follow these requirements:\n"
                        "1. The code should be complete, standardized, and maintainable.\n"
                        "2. Responses should be concise and avoid irrelevant content.\n"
                    )
                })
                self.context_initialized = True
        except Exception as e:
            raise ProjectBaseException(f"Error analyzing project: {str(e)}")

    def modify_project(self, user_requirement: str) -> None:
        """
        Modify project based on user requirements
        """
        try:
            self.analyze_project()
            self.ai_commands.process_user_requirement(user_requirement)
        except Exception as e:
            raise ProjectBaseException(f"Error modifying project: {str(e)}")

    def check_project_runnable(self) -> tuple[bool, str]:
        """Check if project is runnable"""
        return self.project_commands.check_project_runnable()

    def install_dependencies(self) -> bool:
        """Install project dependencies"""
        return self.project_commands.install_dependencies()

    def run_project(self) -> None:
        """Run project"""
        self.project_commands.run_project()

    def stop_project(self) -> None:
        """Stop running project"""
        self.project_commands.stop_project()

    def analyze_failure_reason(self, message: str) -> str:
        """Analyze reason for project not running"""
        return self.ai_commands.analyze_failure_reason(message)

    def execute_action(self, action_name: str, args: list) -> str:
        """
        Execute specific action
        """
        try:
            if action_name == "analyze_project":
                self.analyze_project()
                return "Project structure analyzed and updated"
                
            elif action_name == "read_file" and args:
                file_path = args[0]
                abs_path = os.path.join(self.project_path, file_path)
                if os.path.exists(abs_path):
                    with open(abs_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    return f"Content of file {file_path}:\n{content[:1000]}..."  # Limit content length
                else:
                    return f"File {file_path} does not exist"
                
            else:
                return f"Unknown action: {action_name} or insufficient parameters"
        except Exception as e:
            return f"Error executing action: {str(e)}"