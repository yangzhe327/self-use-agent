"""
Project Command Processing Module
"""

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


    def test_run_project(self) -> Tuple[bool, str]:
        """
        Actually test run the project to see if all dependencies are properly installed
        Returns a tuple of (success, error_message)
        """
        try:
            # Check if npm is available
            npm_executable = find_executable('npm')
            if not npm_executable:
                return False, "npm command not found, please ensure Node.js is installed"
            
            # Use analyzer to read package.json instead of direct file operation
            package_json_content = self.analyzer.read_file_content('package.json')
            if not package_json_content:
                return False, "package.json file not found in the project"
                
            try:
                package_data = json.loads(package_json_content)
            except json.JSONDecodeError as e:
                return False, f"package.json file format error: {str(e)}"
            
            # Determine test run command
            scripts = package_data.get('scripts', {})
            test_cmd = None
            script_name = None
            
            # Try to find a script that would start the project without opening browser or long running process
            # We prioritize scripts that might do a quick build or dry-run
            if 'build' in scripts:
                script_name = 'build'
                test_cmd = [npm_executable, 'run', 'build']
            elif 'start' in scripts:
                script_name = 'start'
                test_cmd = [npm_executable, 'run', 'start']
            elif 'dev' in scripts:
                script_name = 'dev'
                test_cmd = [npm_executable, 'run', 'dev']
            elif 'serve' in scripts:
                script_name = 'serve'
                test_cmd = [npm_executable, 'run', 'serve']
            else:
                # If there are no predefined scripts, use the default startup command
                script_name = 'start'
                test_cmd = [npm_executable, 'start']
            
            # Run the command with a timeout to check if dependencies are properly installed
            try:
                result = subprocess.run(
                    test_cmd,
                    cwd=self.project_path,
                    capture_output=True,
                    text=True,
                    timeout=30  # 30 second timeout
                )
                
                # Check if it's a dependency issue
                stderr_output = result.stderr.lower()
                if "enoent" in stderr_output or "module not found" in stderr_output or "cannot find module" in stderr_output:
                    return False, f"Missing dependencies detected when running '{' '.join(test_cmd)}': {result.stderr}"
                elif "error" in stderr_output and result.returncode != 0:
                    return False, f"Error running '{' '.join(test_cmd)}': {result.stderr}"
                else:
                    # Command executed successfully or failed for non-dependency reasons
                    return True, f"Test run successful. Project can be run with 'npm run {script_name}'"
                    
            except subprocess.TimeoutExpired:
                # If the command times out, it's likely running successfully (e.g., dev server)
                return True, f"Test run timed out (likely running successfully). Project can be run with 'npm run {script_name}'"
                
        except Exception as e:
            return False, f"Error testing project run: {str(e)}"

    def install_dependencies(self) -> bool:
        """Install project dependencies"""
        print("Installing project dependencies...")
        try:
            # Use analyzer to check if package.json exists
            package_json_content = self.analyzer.read_file_content('package.json')
            if not package_json_content:
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
            
            # Use analyzer to read package.json instead of direct file operation
            package_json_content = self.analyzer.read_file_content('package.json')
            if not package_json_content:
                print("package.json file not found in the project")
                return
                
            try:
                package_data = json.loads(package_json_content)
            except json.JSONDecodeError as e:
                print(f"package.json file format error: {str(e)}")
                return
            
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