"""
项目命令处理模块
"""

import os
import json
import subprocess
from typing import Dict, Any, Optional, Tuple
from services.project_analyzer import ProjectAnalyzer
from utils.helpers import find_executable, run_subprocess_command


class ProjectCommands:
    """处理项目相关命令的类"""
    
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.analyzer = ProjectAnalyzer(project_path)
        self.running_process: Optional[subprocess.Popen] = None

    def check_project_runnable(self) -> Tuple[bool, str]:
        """检查项目是否可以运行"""
        package_json_content = self.analyzer.read_file('package.json')
        if not package_json_content:
            return False, "项目中没有找到 package.json 文件"
        
        try:
            package_data = json.loads(package_json_content)
            
            if 'scripts' not in package_data:
                return False, "package.json 中没有定义 scripts"
            
            # 检查是否有启动脚本
            start_scripts = ['start', 'dev', 'serve']
            for script in start_scripts:
                if script in package_data['scripts']:
                    return True, f"项目可以使用 'npm run {script}' 运行"
            
            return True, "项目包含 npm 脚本，可以运行"
        except json.JSONDecodeError as e:
            return False, f"package.json 文件格式错误: {str(e)}"
        except Exception as e:
            return False, f"检查项目时出错: {str(e)}"

    def install_dependencies(self) -> bool:
        """安装项目依赖"""
        print("正在安装项目依赖...")
        try:
            # 检查是否存在 package.json
            package_json_path = os.path.join(self.project_path, 'package.json')
            if not os.path.exists(package_json_path):
                print("项目中没有找到 package.json 文件，无法安装依赖")
                return False
            
            # 检查npm是否可用
            npm_executable = find_executable('npm')
            if not npm_executable:
                print("未找到 npm 命令，请确保已安装 Node.js")
                return False
            
            # 执行 npm install，确保在正确的项目目录下执行
            cmd = [npm_executable, 'install']
            print(f"执行命令: {' '.join(cmd)} 在目录: {self.project_path}")
            result = run_subprocess_command(cmd, cwd=self.project_path)
            
            if result.returncode == 0:
                print("依赖安装成功！")
                return True
            else:
                print(f"依赖安装失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"安装依赖时出错: {str(e)}")
            return False

    def run_project(self) -> None:
        """运行项目"""
        try:
            # 检查是否有项目正在运行
            if self.running_process and self.running_process.poll() is None:
                print("项目已在运行中，请先停止当前项目再启动新项目")
                return
            
            # 检查npm是否可用
            npm_executable = find_executable('npm')
            if not npm_executable:
                print("未找到 npm 命令，请确保已安装 Node.js")
                return
            
            package_json_path = os.path.join(self.project_path, 'package.json')
            if not os.path.exists(package_json_path):
                print("项目中没有找到 package.json 文件")
                return
                
            with open(package_json_path, 'r', encoding='utf-8') as f:
                package_data = json.load(f)
            
            # 确定运行命令
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
                # 如果没有预定义的脚本，使用默认的启动命令
                script_name = 'start'
                run_cmd = [npm_executable, 'start']
            
            print(f"正在启动项目: {' '.join(run_cmd)}")
            print("项目将在新窗口中运行，您可以通过 Ctrl+C 停止项目")
            print("您也可以在cmd中输入 'stop' 来停止项目")
            
            # 检查脚本是否在package.json中定义
            if script_name not in scripts:
                print(f"警告: package.json 中未定义 '{script_name}' 脚本")
            
            # 在新窗口中运行项目，使其可见且可以使用Ctrl+C停止
            # Windows系统使用start命令在新窗口中运行
            cmd_string = ' '.join(run_cmd)
            # 使用 /d 参数确保正确切换驱动器和目录
            self.running_process = subprocess.Popen(
                f'start "Project Runner" cmd /k "cd /d \"{self.project_path}\" && {cmd_string}"',
                shell=True
            )
            
            print("项目已启动，请查看新打开的窗口")
        except json.JSONDecodeError as e:
            print(f"package.json 文件格式错误: {str(e)}")
        except Exception as e:
            print(f"运行项目时出错: {str(e)}")

    def stop_project(self) -> None:
        """停止正在运行的项目"""
        if self.running_process and self.running_process.poll() is None:
            self.running_process.terminate()
            try:
                self.running_process.wait(timeout=5)
                print("项目已停止")
            except subprocess.TimeoutExpired:
                self.running_process.kill()
                print("项目无响应，已强制停止")
            self.running_process = None
        else:
            print("没有正在运行的项目")