"""
AI Command Processing Module
"""

import json
import os
from typing import Dict, Any
from services.ai_interactor import AIInteractor
from services.file_operator import FileOperator
from services.project_analyzer import ProjectAnalyzer  # Added missing import


class AICommands:
    """Class for handling AI-related commands"""
    
    def __init__(self, ai_interactor: AIInteractor, project_path: str, analyzer: ProjectAnalyzer):
        self.ai = ai_interactor
        self.project_path = project_path
        self.analyzer = analyzer
        self.project_info: Dict[str, Any] = {}

    def analyze_failure_reason(self, message: str) -> str:
        """Analyze the reason why the project cannot be run"""
        # Prepare project information for AI analysis
        project_info = self.analyzer.analyze()
        project_context = json.dumps(project_info, ensure_ascii=False, indent=2)
        
        # Use ReAct strategy to analyze failure reason
        analysis_prompt = (
            f"The project cannot be run, the error message is: {message}\n"
            f"Project structure information:\n{project_context}\n"
            "Please use the ReAct strategy to analyze the specific reason why the project cannot be run, and determine whether it is caused by missing dependencies.\n"
            "Please follow the following format for reasoning and action:\n"
            "Thought: Analyze the error message and project structure to determine the possible cause\n"
            "Action: analyze_project(), read_file(\"file path\")\n"
            "Observation: Based on the analysis results, determine the specific cause\n"
            "Final Answer: If it is caused by missing dependencies, please reply 'dependency issue'; for other reasons, please provide a detailed explanation.\n"
            "Only output the analysis results, do not output other content."
        )
        
        analysis_result = self.ai.ask_with_react(analysis_prompt)
        return analysis_result.strip()

    def process_user_requirement(self, user_requirement: str) -> None:
        """
        Process user requirements and generate project modifications
        """
        # Update project info with latest analysis
        self.project_info = self.analyzer.analyze()
        
        # Use ReAct strategy to generate file list
        react_prompt = self._generate_react_prompt_for_file_list(user_requirement)
        ai_file_list = self.ai.ask_with_react(react_prompt)
        
        file_paths = [line.strip() for line in ai_file_list.split('\n') if line.strip()]
        file_contents = []
        for path in file_paths:
            abs_path = os.path.join(self.project_path, path)
            content = FileOperator.read_file(abs_path, self.project_path)
            if content:
                file_contents.append(f"---file-start---\n{path}\n---code-start---\n{content}\n---code-end---\n---file-end---")
            else:
                file_contents.append(f"---file-start---\n{path}\n---code-start---\n(File does not exist, please generate new file content)\n---code-end---\n---file-end---")
        files_info = '\n'.join(file_contents)
        full_react_prompt = (
            f"Generate specific modification plans based on user requirements and file content. Please use the ReAct strategy to think and act.\n"
            f"Task description: The following files in the project that need to be modified/added and their content (if any), {files_info}\n"
            f"Please give the complete new content of each file according to the user requirement \"{user_requirement}\". "
            f"Follow these rules:\n"
            f"Please strictly follow the following format for reply:\n"
            f"Each file that needs to be modified, deleted, or added should be separated in the following format:\n"
            f"---file-start---\nFile path (e.g., src/App.jsx)\n---code-start---\nCode content (completely replace the file content)\n---code-end---\n---file-end---\n"
            f"If you need to delete a file, please fill in 'delete' between ---code-start--- and ---code-end---.\n"
            f"If there are multiple files, repeat the above structure. Do not output extra content.\n"
            f"The code must follow these requirements:\n"
            f"1. Remember not to modify the original code logic unless explicitly requested by the user.\n"
            f"2. Must follow the design language and style of the current project.\n"
            f"3. For tables, please use material-react-table.\n"
            f"4. For components, please use components from material-ui.\n"
            f"5. Try not to add new third-party libraries to the project unless explicitly requested by the user.\n\n"
            f"Please follow the following format for reasoning and action:\n"
            f"Thought: Analyze user requirements and current file content to determine how to modify. If you need to view other related files to ensure consistency of modifications, you can use the read_file operation.\n"
            f"Action: analyze_project(), read_file(\"file path\")\n"
            f"Observation: Based on the analysis results, generate code modification plans that meet the requirements\n"
            f"Final Answer: Strictly output file modification content in the specified format\n\n"
            f"Important tips:\n"
            f"1. In the Thought stage, carefully analyze user requirements and provided file content\n"
            f"2. If you need to view other related files to ensure consistency of modifications, please use the read_file operation\n"
            f"3. Ensure that the generated code conforms to the existing style and structure of the project"
        )
        
        # Use ReAct strategy to generate file modification content
        ai_response = self.ai.ask_with_react(full_react_prompt)
        
        print("Suggested files to modify:")
        print(ai_file_list)
        apply = input("Do you want to apply the above modifications to the project? (y/n): ").strip().lower()
        if apply == 'y':
            self.apply_ai_changes(ai_response)
        else:
            print("Skipped automatic application of modifications.")
            # When user refuses to apply modifications, clear the related conversation history (file list request + specific content request)
            self.ai.rollback_last_interaction()  # Clear conversation history of file list request

    def _generate_react_prompt_for_file_list(self, user_requirement: str) -> str:
        """
        Generate prompt for file list generation using ReAct strategy
        """
        react_prompt = (
            f"Generate a list of files to be modified based on user requirements. Please use the ReAct strategy to think and act.\n"
            f"User requirement: {user_requirement}\n"
            f"Current project information: {json.dumps(self.project_info, ensure_ascii=False, indent=2)}\n\n"
            f"Please follow the following format for reasoning and action:\n"
            f"Thought: Analyze user requirements and project structure to determine which files need to be modified. If you need to understand the content of a specific file to make a judgment, you can use the read_file operation.\n"
            f"Action: analyze_project(), read_file(\"file path\")\n"
            f"Observation: Based on the analysis results, list the file paths that need to be modified, deleted, or added\n"
            f"Final Answer: Only output the file path list, one file path per line (e.g., src/App.jsx), only output the file path list, do not output other content\n\n"
            f"Important tips:\n"
            f"1. In the Thought stage, carefully analyze user requirements and consider which files may need to be modified\n"
            f"2. If you need to view the content of a specific file to determine whether it needs to be modified, please use the read_file operation\n"
            f"3. Only give the final file list after sufficient analysis\n"
            f"4. Do not include files you are unsure whether they need to be modified"
        )
        return react_prompt

    def apply_ai_changes(self, ai_response: str) -> None:
        """
        Apply AI-generated modifications to the project
        """
        print("Applying suggestions to the project...")
        files = ai_response.split('---file-start---')
        files_changed = False
        structure_changed = False
        
        for file_block in files:
            file_block = file_block.strip()
            if not file_block:
                continue
            try:
                # Safely split file blocks to avoid index out of bounds
                parts = file_block.split('---code-start---')
                if len(parts) < 2:
                    print(f"Warning: File block format is incorrect, skipping processing: {file_block[:50]}...")
                    continue
                    
                path_part = parts[0].strip()
                code_parts = parts[1].split('---code-end---')
                if len(code_parts) < 1:
                    print(f"Warning: File block is missing code end marker, skipping processing: {path_part[:50]}...")
                    continue
                    
                code_part = code_parts[0].strip()
                rel_path = path_part.split('\n')[0].strip()
                abs_path = os.path.join(self.project_path, rel_path)
                
                # Determine operation type
                if code_part.lower().strip() == "delete":
                    # Delete file operation
                    if os.path.exists(abs_path):
                        os.remove(abs_path)
                        structure_changed = True  # Structure has changed
                        files_changed = True
                        print(f"Deleted file: {abs_path}")
                    else:
                        print(f"File does not exist, cannot delete: {abs_path}")
                else:
                    # Create or modify file operation
                    old_exists = os.path.exists(abs_path)
                    if FileOperator.write_code_to_file(abs_path, code_part, self.project_path):
                        files_changed = True
                        
                        # If it's a newly created file, the structure has changed
                        if not old_exists:
                            structure_changed = True
                    else:
                        print(f"Failed to write file: {abs_path}")
                        
            except Exception as e:
                print(f"Error parsing reply: {e}")
        
        # Only re-analyze the project when the file structure changes
        if structure_changed:
            print("Detected file structure changes, re-analyzing project structure...")
            self.project_info = self.analyzer.analyze()
        elif files_changed:
            print("File content updated.")
            
        print("Application completed!")