"""
Main Application Class
"""

import os
import json
import subprocess
import sys
from typing import Dict, Any, Optional
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
        self.project_info: Dict[str, Any] = {}
        self.context_initialized = False
        self.project_commands = ProjectCommands(project_path)
        self.ai_commands = AICommands(self.ai, project_path, self.analyzer)

    def analyze_project(self) -> None:
        """
        Analyze project structure
        """
        try:
            self.project_info = self.analyzer.analyze()
            if not self.context_initialized:
                self.ai.messages.append({
                    "role": "system",
                    "content": (
                        "You are a senior UI development engineer and UX designer, proficient in front-end architecture, interaction design, and user experience optimization. "
                        "Your task is to provide professional analysis and suggestions based on the project structure and user requirements, and generate high-quality, directly applicable code. "
                        "When outputting, please follow these requirements:\n"
                        "1. The code should be complete, standardized, and maintainable.\n"
                        "2. Responses should be concise and avoid irrelevant content.\n"
                        "The current project structure is as follows:\n"
                        f"{json.dumps(self.project_info, ensure_ascii=False, indent=2)}"
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
            self.ai_commands.project_info = self.project_info
            self.ai_commands.modify_project(user_requirement)
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

    def _execute_action(self, action_name: str, args: list) -> str:
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
                    
            elif action_name == "write_file" and len(args) >= 2:
                file_path = args[0]
                content = args[1] if len(args) == 2 else ' '.join(args[1:])
                abs_path = os.path.join(self.project_path, file_path)
                os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                with open(abs_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return f"File {file_path} written"
                
            else:
                return f"Unknown action: {action_name} or insufficient parameters"
        except Exception as e:
            return f"Error executing action: {str(e)}"


def main():
    try:
        project_path = input("Please enter your UI project root directory path: ").strip()
        if not os.path.isdir(project_path):
            print("Project path does not exist!")
            return
        
        agent = UIProjectAgent(project_path=project_path)
        
        # Check if project is runnable
        runnable, message = agent.check_project_runnable()
        if runnable:
            print(f"Project check completed: {message}")
            run_choice = input("Do you want to run the project? (y/n): ").strip().lower()
            if run_choice == 'y':
                agent.run_project()
        else:
            print(f"Project cannot be run temporarily: {message}")
            # Let AI analyze the specific reason
            analysis_result = agent.analyze_failure_reason(message)
            print(f"Analysis result: {analysis_result}")
            
            # Decide next action based on AI analysis
            if "dependency issue" in analysis_result or "dependency" in analysis_result:
                install_choice = input("Do you want to install project dependencies? (y/n): ").strip().lower()
                if install_choice == 'y':
                    if agent.install_dependencies():
                        run_choice = input("Dependencies installed successfully, do you want to run the project? (y/n): ").strip().lower()
                        if run_choice == 'y':
                            agent.run_project()
            else:
                # If it's not a dependency issue, AI has already provided detailed explanation, user can decide whether to continue
                pass
        
        # Then analyze the project and enter modification mode
        print("\nEnter your new requirements, 'exit' to quit")
        while True:
            user_input = input("Your requirement: ").strip()
            if user_input.lower() == "exit":
                # Stop running project
                agent.stop_project()
                break
            agent.modify_project(user_input)
    
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
        sys.exit(0)
    except ProjectBaseException as e:
        print(f"Project error: {e.message}")
        sys.exit(1)
    except Exception as e:
        print(f"Program runtime error: {str(e)}")
        sys.exit(1)