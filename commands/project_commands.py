"""
Project Command Processing Module
"""

import os
import json
import subprocess
from typing import Dict, Any, Optional, Tuple
from services.project_analyzer import ProjectAnalyzer
from utils.helpers import find_executable, run_subprocess_command


class ProjectCommands:
    """Class for handling project-related commands"""
    
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.analyzer = ProjectAnalyzer(project_path)
        self.running_process: Optional[subprocess.Popen] = None

    def check_project_runnable(self) -> Tuple[bool, str]:
        """Check if the project can be run"""
        package_json_content = self.analyzer.read_file('package.json')
        if not package_json_content:
            return False, "package.json file not found in the project"
        
        try:
            package_data = json.loads(package_json_content)
            
            if 'scripts' not in package_data:
                return False, "No scripts defined in package.json"
            
            # Check for startup scripts
            start_scripts = ['start', 'dev', 'serve']
            for script in start_scripts:
                if script in package_data['scripts']:
                    return True, f"Project can be run using 'npm run {script}'"
            
            return True, "Project contains npm scripts and can be run"
        except json.JSONDecodeError as e:
            return False, f"package.json file format error: {str(e)}"
        except Exception as e:
            return False, f"Error checking project: {str(e)}"

    def install_dependencies(self) -> bool:
        """Install project dependencies"""
        print("Installing project dependencies...")
        try:
            # Check if package.json exists
            package_json_path = os.path.join(self.project_path, 'package.json')
            if not os.path.exists(package_json_path):
                print("package.json file not found in the project, cannot install dependencies")
                return False
            
            # Check if npm is available
            npm_executable = find_executable('npm')
            if not npm_executable:
                print("npm command not found, please ensure Node.js is installed")
                return False
            
            # Execute npm install, ensure it is executed in the correct project directory
            cmd = [npm_executable, 'install']
            print(f"Executing command: {' '.join(cmd)} in directory: {self.project_path}")
            result = run_subprocess_command(cmd, cwd=self.project_path)
            
            if result.returncode == 0:
                print("Dependencies installed successfully!")
                return True
            else:
                print(f"Dependency installation failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"Error installing dependencies: {str(e)}")
            return False

    def run_project(self) -> None:
        """Run project"""
        try:
            # Check if there is a project running
            if self.running_process and self.running_process.poll() is None:
                print("Project is already running, please stop the current project before starting a new project")
                return
            
            # Check if npm is available
            npm_executable = find_executable('npm')
            if not npm_executable:
                print("npm command not found, please ensure Node.js is installed")
                return
            
            package_json_path = os.path.join(self.project_path, 'package.json')
            if not os.path.exists(package_json_path):
                print("package.json file not found in the project")
                return
                
            with open(package_json_path, 'r', encoding='utf-8') as f:
                package_data = json.load(f)
            
            # Determine run command
            scripts = package_data.get('scripts', {})
            run_cmd = None
            script_name = None
            if 'start' in scripts:
                script_name = 'start'
                run_cmd = [npm_executable, 'run', 'start']
            elif 'dev' in scripts:
                script_name = 'dev'
                run_cmd = [npm_executable, 'run', 'dev']
            elif 'serve' in scripts:
                script_name = 'serve'
                run_cmd = [npm_executable, 'run', 'serve']
            else:
                # If there are no predefined scripts, use the default startup command
                script_name = 'start'
                run_cmd = [npm_executable, 'start']
            
            print(f"Starting project: {' '.join(run_cmd)}")
            print("The project will run in a new window, you can stop the project with Ctrl+C")
            print("You can also type 'stop' in cmd to stop the project")
            
            # Check if script is defined in package.json
            if script_name not in scripts:
                print(f"Warning: '{script_name}' script is not defined in package.json")
            
            # Run the project in a new window, making it visible and stoppable with Ctrl+C
            # Windows system uses start command to run in a new window
            cmd_string = ' '.join(run_cmd)
            # Use /d parameter to ensure correct drive and directory switching
            self.running_process = subprocess.Popen(
                f'start "Project Runner" cmd /k "cd /d \"{self.project_path}\" && {cmd_string}"',
                shell=True
            )
            
            print("Project started, please check the newly opened window")
        except json.JSONDecodeError as e:
            print(f"package.json file format error: {str(e)}")
        except Exception as e:
            print(f"Error running project: {str(e)}")

    def stop_project(self) -> None:
        """Stop the running project"""
        if self.running_process and self.running_process.poll() is None:
            self.running_process.terminate()
            try:
                self.running_process.wait(timeout=5)
                print("Project stopped")
            except subprocess.TimeoutExpired:
                self.running_process.kill()
                print("Project unresponsive, forcefully stopped")
            self.running_process = None
        else:
            print("No project is running")