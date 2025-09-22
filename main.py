import os
import json
from project_analyzer import ProjectAnalyzer
from ai_interactor import AIInteractor
from file_operator import FileOperator

QWEN_API_KEY = os.getenv("DASHSCOPE_API_KEY", "YOUR_QWEN_API_KEY")

class UIProjectAgent:
    def __init__(self, project_path):
        self.project_path = project_path
        self.analyzer = ProjectAnalyzer(project_path)
        self.ai = AIInteractor(QWEN_API_KEY)
        self.project_info = {}
        self.context_initialized = False

    def analyze_project(self):
        self.project_info = self.analyzer.analyze()
        if not self.context_initialized:
            self.ai.messages.append({
                "role": "system",
                "content": (
                    "You are a senior UI developer and UX designer, expert in front-end architecture, interaction design, and user experience optimization. "
                    "Your task is to provide professional analysis and suggestions based on the project structure and user requirements, and generate high-quality, directly applicable code. "
                    "When outputting, please follow these requirements:\n"
                    "1. Code must be complete, standardized, and maintainable.\n"
                    "2. Responses should be concise and avoid irrelevant content.\n"
                    "Current project structure:\n"
                    f"{json.dumps(self.project_info, ensure_ascii=False, indent=2)}"
                )
            })
            self.context_initialized = True

    def modify_project(self, user_requirement):
        self.analyze_project()
        print("AI is analyzing files that need to be modified...")
        ai_file_list = self.ai.ask(f"Based on the current project structure and the following requirements, list all file paths that need to be modified or added or deleted (e.g., src/App.jsx), output only the file path list, no other content:\n{user_requirement}")
        print("Files AI suggests modifying:")
        print(ai_file_list)
        file_paths = [line.strip() for line in ai_file_list.split('\n') if line.strip()]
        file_contents = []
        for path in file_paths:
            abs_path = os.path.join(self.project_path, path)
            content = FileOperator.read_file(abs_path)
            if content:
                file_contents.append(f"---file-start---\n{path}\n---code-start---\n{content}\n---code-end---\n---file-end---")
            else:
                file_contents.append(f"---file-start---\n{path}\n---code-start---\n(File does not exist, please generate new file content)\n---code-end---\n---file-end---")
        files_info = '\n'.join(file_contents)
        format_tip = (
            "Please strictly follow this format for replies:\n"
            "Each file that needs to be modified or added or deleted should be separated with the following format:\n"
            "---file-start---\nFile path (e.g., src/App.jsx)\n---code-start---\nCode content (completely replace the file content)\n---code-end---\n---file-end---\n"
            "To delete a file, fill in 'delete' between ---code-start--- and ---code-end---.\n"
            "For multiple files, repeat the above structure. Do not output extra content.\n"
            "Code must follow these requirements:\n"
            "1. Remember not to modify the original code logic unless explicitly requested by the user.\n"
            "2. Must follow the design language and style of the current project.\n"
            "3. Try not to add new third-party libraries to the project unless explicitly requested by the user."
        )
        full_prompt = (
            f"Below are the files in the project that need to be modified/added/deleted and their content (if any). According to the user requirement '{user_requirement}', provide the complete new content for each file and output strictly in the specified format:\n{files_info}\n{format_tip}"
        )
        print("\nAI's specific modification suggestions:")
        ai_response = self.ai.ask(full_prompt)
        apply = input("Apply the above modifications to the project? (y/n): ").strip().lower()
        if apply == 'y':
            self.apply_ai_changes(ai_response)
        else:
            print("Skipped automatically applying modifications.")

    def apply_ai_changes(self, ai_response):
        print("Applying AI suggestions to the project...")
        files = ai_response.split('---file-start---')
        files_changed = False
        structure_changed = False
        
        for file_block in files:
            file_block = file_block.strip()
            if not file_block:
                continue
            try:
                path_part = file_block.split('---code-start---')[0].strip()
                code_part = file_block.split('---code-start---')[1].split('---code-end---')[0].strip()
                rel_path = path_part.split('\n')[0].strip()
                abs_path = os.path.join(self.project_path, rel_path)
                
                # Determine operation type
                if code_part.lower().strip() == "delete":
                    # File deletion operation
                    if os.path.exists(abs_path):
                        os.remove(abs_path)
                        structure_changed = True  # Structure has changed
                        files_changed = True
                    else:
                        print(f"File does not exist, cannot delete: {abs_path}")
                else:
                    # Create or modify file operation
                    old_exists = os.path.exists(abs_path)
                    FileOperator.write_code_to_file(abs_path, code_part)
                    files_changed = True
                    
                    # If it's a newly created file, structure has changed
                    if not old_exists:
                        structure_changed = True
                        
            except Exception as e:
                print(f"Error parsing AI response: {e}")
        
        # Only re-analyze the project when file structure changes
        if structure_changed:
            print("Detected file structure changes, re-analyzing project structure...")
            self.analyze_project()
        elif files_changed:
            print("File content has been updated.")
            
        print("Application completed!")

def main():
    project_path = input("Please enter the root directory path of your UI project: ").strip()
    if not os.path.isdir(project_path):
        print("Project path does not exist!")
        return
    agent = UIProjectAgent(project_path=project_path)
    agent.analyze_project()
    print("\nAI's suggested installation and running methods:")
    install_prompt = "Based on the current project structure, provide detailed installation and running steps (including dependency installation, startup commands, etc.), and explain precautions. Remember to only do analysis without proposing modifications"
    agent.ai.ask(install_prompt)
    print("\nWelcome to the UI Project Analysis and Auto-modification Agent. Enter your new requirements, 'exit' to quit.")
    while True:
        user_input = input("Your requirement: ")
        if user_input.strip().lower() == "exit":
            break
        agent.modify_project(user_input)

if __name__ == "__main__":
    main()