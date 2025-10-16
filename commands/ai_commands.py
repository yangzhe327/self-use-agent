"""
AI Command Processing Module
"""

import json
import os
from typing import Dict, Any
from services.ai_interactor import AIInteractor
from services.file_operator import FileOperator


class AICommands:
    """Class for handling AI-related commands"""
    
    def __init__(self, ai_interactor: AIInteractor, project_path: str, analyzer):
        self.ai = ai_interactor
        self.project_path = project_path
        self.analyzer = analyzer
        self.project_info: Dict[str, Any] = {}

    def analyze_project_failure_reason(self, message: str) -> str:
        """Analyze the reason why the project cannot be run"""
        # Prepare project information for AI analysis
        project_info = self.analyzer.analyze()
        project_context = json.dumps(project_info, ensure_ascii=False, indent=2)
        
        # Simplified prompt as ReAct strategy is in system prompt
        analysis_prompt = (
            f"The project cannot be run, the error message is: {message}\n"
            f"Project structure information:\n{project_context}\n"
            "Analyze the specific reason why the project cannot be run, and determine whether it is caused by missing dependencies.\n"
            "If it is caused by missing dependencies, please reply 'dependency issue'; for other reasons, please provide a detailed explanation.\n"
            "Only output the analysis results, do not output other content."
        )
        
        analysis_result = self.ai.ask_with_react(analysis_prompt)
        return analysis_result.strip()

    def process_user_requirement(self, user_requirement: str) -> None:
        """
        Process user requirements, but let AI decide whether to analyze or modify
        """
        self.project_info = self.analyzer.analyze()
        
        # Simplified prompt as ReAct strategy is in system prompt
        decision_prompt = (
            f"User requirement: {user_requirement}\n\n"
            f"Project structure:\n{json.dumps(self.project_info, ensure_ascii=False, indent=2)}\n\n"
            f"Please decide which type of task this is and take appropriate action:\n"
            f"Action: Choose one of the following actions:\n"
            f"  - perform_file_operations(\"{user_requirement}\"): Use this when the task requires changing files in the project\n"
            f"  - perform_analysis_task(\"{user_requirement}\"): Use this when the task only requires providing information, explanations, or analysis\n\n"
            f"Examples of file operation tasks:\n"
            f"- 'Add a login page' - requires creating new files\n"
            f"- 'Change the color scheme' - requires modifying existing files\n"
            f"- 'Delete the unused components' - requires deleting files\n\n"
            f"Examples of analysis tasks:\n"
            f"- 'Analyze the project structure' - just needs to provide information\n"
            f"- 'Explain what this page does' - just needs to provide explanation\n"
            f"- 'What is the purpose of this code' - just needs to provide analysis\n"
            f"- 'How does this component work' - just needs to provide explanation"
        )
        
        # Get AI decision and execute
        result = self.ai.ask_with_react(decision_prompt)
        print("\nAI Result:")
        print("=" * 50)
        print(result)
        print("=" * 50)

    def _generate_react_prompt_for_file_list(self, user_requirement: str) -> str:
        """
        Generate prompt for file list generation
        """
        react_prompt = (
            f"Generate a list of files to be modified based on user requirements.\n"
            f"User requirement: {user_requirement}\n"
            f"Current project information: {json.dumps(self.project_info, ensure_ascii=False, indent=2)}\n\n"
            f"Action: analyze_project() or read_file(\"file path\") as needed\n"
            f"Final Answer: Only output the file path list, one file path per line (e.g., src/App.jsx), only output the file path list, do not output other content\n\n"
            f"Tips:\n"
            f"1. Analyze user requirements and project structure to determine which files need to be modified\n"
            f"2. If you need to view the content of a specific file to determine whether it needs to be modified, please use the read_file operation\n"
            f"3. Only give the final file list after sufficient analysis\n"
            f"4. Do not include files you are unsure whether they need to be modified"
        )
        return react_prompt

    def _generate_react_prompt_for_modifications(self, full_prompt: str) -> str:
        """
        Generate prompt for file modification content generation
        """
        react_prompt = (
            f"Generate specific modification plans based on user requirements and file content.\n"
            f"Task description: {full_prompt}\n\n"
            f"Action: analyze_project() or read_file(\"file path\") as needed\n"
            f"Final Answer: Strictly output file modification content in the specified format\n\n"
            f"Tips:\n"
            f"1. Analyze user requirements and current file content to determine how to modify\n"
            f"2. If you need to view other related files to ensure consistency of modifications, please use the read_file operation\n"
            f"3. Ensure that the generated code conforms to the existing style and structure of the project"
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