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
from services.file_operator import FileOperator
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
            self.project_info = self.analyzer.analyze_project_structure()
            if not self.context_initialized:
                # Unified role definition with ReAct strategy
                system_prompt = (
                    "You are a senior UI development engineer and UX designer who uses the ReAct (Reasoning + Action) strategy. "
                    "You are proficient in front-end architecture, interaction design, and user experience optimization. "
                    "Your task is to provide professional analysis and suggestions based on the project structure and user requirements, "
                    "and generate high-quality, directly applicable code.\n\n"
                    "You use the ReAct strategy which means you think through problems step by step before taking action. "
                    "Use the following format in your responses:\n"
                    "Thought: Describe your reasoning and planning process\n"
                    "Action: Choose an action to take from the available actions\n"
                    "Observation: Observe the results of your action\n"
                    "Final Answer: Provide the final answer to the original question\n\n"
                    "Available Actions:\n"
                    "1. analyze_project() - Re-analyze the project structure\n"
                    "2. read_file(\"file_path\") - Read the content of a specific file\n"
                    "3. write_file(\"file_path\", \"content\") - Write content to a file\n"
                    "4. perform_analysis_task(\"requirement\") - Perform an analysis task that doesn't require file operations\n"
                    "5. perform_file_operations(\"requirement\") - Perform tasks that require file operations\n\n"
                    "Examples of when to use each action:\n"
                    "- Use perform_analysis_task for questions like 'What does this code do?' or 'Explain the project structure'\n"
                    "- Use perform_file_operations for requests like 'Add a new component' or 'Modify the homepage'\n"
                    "Always provide a Final Answer that directly addresses the user's request.\n\n"
                    "When outputting code, please follow these requirements:\n"
                    "1. The code should be complete, standardized, and maintainable.\n"
                    "2. Responses should be concise and avoid irrelevant content.\n"
                    "The current project structure is as follows:\n"
                    f"{json.dumps(self.project_info, ensure_ascii=False, indent=2)}"
                )
                
                self.ai.messages.append({
                    "role": "system",
                    "content": system_prompt
                })
                self.context_initialized = True
        except Exception as e:
            raise ProjectBaseException(f"Error analyzing project: {str(e)}")

    def analyze_project_only(self, user_requirement: str) -> None:
        """
        Analyze project based on user requirements without making modifications
        """
        try:
            # Ensure project is analyzed first
            if not self.project_info:
                self.analyze_project()
                
            # Create a prompt for analysis-only tasks
            analysis_prompt = (
                f"Based on the following project structure and user requirements, please provide a detailed analysis:\n\n"
                f"User requirement: {user_requirement}\n\n"
                f"Project structure:\n{json.dumps(self.project_info, ensure_ascii=False, indent=2)}\n\n"
                f"Please provide a comprehensive analysis of the project based on the user's requirements. "
                f"Include but not limited to:\n"
                f"1. Current project structure overview\n"
                f"2. Analysis of how the project meets or fails to meet the requirements\n"
                f"3. Suggestions for improvements or modifications\n"
                f"4. Potential issues or risks\n"
                f"5. Best practices that should be followed\n\n"
                f"Provide your analysis in a clear and structured format."
            )
            
            # Get AI analysis
            analysis_result = self.ai.ask_with_react(analysis_prompt)
            print("\nAI Analysis Result:")
            print("=" * 50)
            print(analysis_result)
            print("=" * 50)
            
        except Exception as e:
            raise ProjectBaseException(f"Error analyzing project: {str(e)}")

    def modify_project(self, user_requirement: str) -> None:
        """
        Modify project based on user requirements - now enhanced to let AI decide action
        """
        try:
            self.analyze_project()
            self.ai_commands.project_info = self.project_info
            self.ai_commands.process_user_requirement(user_requirement)
        except Exception as e:
            raise ProjectBaseException(f"Error modifying project: {str(e)}")

    def test_run_project(self) -> tuple[bool, str]:
        """Actually test run the project to see if all dependencies are properly installed"""
        return self.project_commands.test_run_project()

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
        return self.ai_commands.analyze_project_failure_reason(message)

    def _execute_action(self, action_name: str, args: list) -> str:
        """
        Execute specific action
        """
        try:
            if action_name == "analyze_project":
                self.analyze_project()
                return "Project structure analyzed and updated"
                
            elif action_name == "perform_analysis_task":
                # Perform analysis without file operations
                if args:
                    requirement = ' '.join(args)
                else:
                    requirement = "Analyze the project and provide information"
                
                # Create a prompt for detailed analysis
                analysis_prompt = (
                    f"Based on the project structure and user requirements, please provide a detailed analysis or explanation.\n"
                    f"User requirement: {requirement}\n\n"
                    f"Project structure:\n{json.dumps(self.project_info, ensure_ascii=False, indent=2)}\n\n"
                    f"Please provide a comprehensive response to the user's requirement. "
                    f"This should be an analysis, explanation, or information delivery task that does not require any file operations.\n"
                    f"Examples of such tasks:\n"
                    f"- Explaining what a page or component does\n"
                    f"- Analyzing the purpose of specific code\n"
                    f"- Describing how components work\n"
                    f"- Providing project structure overview\n"
                    f"- Explaining technical choices\n\n"
                    f"Provide your response in a clear and structured format."
                )
                
                analysis_result = self.ai.ask_with_react(analysis_prompt)
                return analysis_result
                
            elif action_name == "perform_file_operations":
                # Perform file operations (modifications, creations, deletions)
                if args:
                    requirement = ' '.join(args)
                else:
                    requirement = "Modify the project as needed"
                self.ai_commands.project_info = self.project_info
                
                # Use ReAct strategy to generate file list
                react_prompt = self.ai_commands._generate_react_prompt_for_file_list(requirement)
                ai_file_list = self.ai.ask_with_react(react_prompt)
                
                file_paths = [line.strip() for line in ai_file_list.split('\n') if line.strip()]
                file_contents = []
                for path in file_paths:
                    # Use analyzer's read_file_content method instead of FileOperator
                    content = self.analyzer.read_file_content(path)
                    if content:
                        file_contents.append(f"---file-start---\n{path}\n---code-start---\n{content}\n---code-end---\n---file-end---")
                    else:
                        file_contents.append(f"---file-start---\n{path}\n---code-start---\n(File does not exist, please generate new file content)\n---code-end---\n---file-end---")
                files_info = '\n'.join(file_contents)
                format_tip = (
                    "Please strictly follow the following format for reply:\n"
                    "Each file that needs to be modified, deleted, or added should be separated in the following format:\n"
                    "---file-start---\nFile path (e.g., src/App.jsx)\n---code-start---\nCode content (completely replace the file content)\n---code-end---\n---file-end---\n"
                    "If you need to delete a file, please fill in 'delete' between ---code-start--- and ---code-end---.\n"
                    "If there are multiple files, repeat the above structure. Do not output extra content.\n"
                    "The code must follow these requirements:\n"
                    "1. Remember not to modify the original code logic unless explicitly requested by the user.\n"
                    "2. Must follow the design language and style of the current project.\n"
                    "3. For tables, please use material-react-table.\n"
                    "4. For components, please use components from material-ui.\n"
                    "5. Try not to add new third-party libraries to the project unless explicitly requested by the user."
                )
                full_prompt = (
                    f"The following files in the project that need to be modified/added and their content (if any), {files_info}\n Please give the complete new content of each file according to the user requirement \"{requirement}\". Follow these rules:\n{format_tip}"
                )
                
                # Use ReAct strategy to generate file modification content
                react_modify_prompt = self.ai_commands._generate_react_prompt_for_modifications(full_prompt)
                ai_response = self.ai.ask_with_react(react_modify_prompt)
                
                print("Suggested files to modify:")
                print(ai_file_list)
                apply = input("Do you want to apply the above modifications to the project? (y/n): ").strip().lower()
                if apply == 'y':
                    self.ai_commands.apply_ai_changes(ai_response)
                    return "Project modifications completed"
                else:
                    print("Skipped automatic application of modifications.")
                    # When user refuses to apply modifications, clear the related conversation history (file list request + specific content request)
                    self.ai.remove_last_interaction()  # Clear conversation history of specific content request
                    self.ai.remove_last_interaction()  # Clear conversation history of file list request
                    return "Project modifications skipped by user"
                
            elif action_name == "read_file" and args:
                file_path = args[0]
                # Use analyzer's read_file_content method
                content = self.analyzer.read_file_content(file_path)
                if content:
                    return f"Content of file {file_path}:\n{content[:1000]}..."  # Limit content length
                else:
                    return f"File {file_path} does not exist"
                    
            elif action_name == "write_file" and len(args) >= 2:
                file_path = args[0]
                content = args[1] if len(args) == 2 else ' '.join(args[1:])
                abs_path = os.path.join(self.project_path, file_path)
                # Use FileOperator to write file
                try:
                    if FileOperator.write_code_to_file(abs_path, content, self.project_path):
                        return f"File {file_path} written"
                    else:
                        return f"Failed to write file {file_path}"
                except Exception as e:
                    return f"Error writing file {file_path}: {str(e)}"
                
            else:
                return f"Unknown action: {action_name} or insufficient parameters"
        except Exception as e:
            return f"Error executing action: {str(e)}"