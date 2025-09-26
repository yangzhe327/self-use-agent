import os
import json
import subprocess
import shutil
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
        self.running_process = None

    def analyze_project(self):
        self.project_info = self.analyzer.analyze()
        if not self.context_initialized:
            self.ai.messages.append({
                "role": "system",
                "content": (
                    "你是一位资深的UI开发工程师和UX设计师，精通前端架构、交互设计、用户体验优化。"
                    "你的任务是根据项目结构和用户需求，提出专业的分析、建议，并生成高质量、可直接应用的代码。"
                    "在输出时请遵循如下要求：\n"
                    "1. 代码需完整、规范、易维护。\n"
                    "2. 回答要简明扼要，避免无关内容。\n"
                    "当前项目结构如下：\n"
                    f"{json.dumps(self.project_info, ensure_ascii=False, indent=2)}"
                )
            })
            self.context_initialized = True

    def modify_project(self, user_requirement):
        self.analyze_project()
        ai_file_list = self.ai.ask(f"请根据当前项目结构和如下需求，列出所有需要修改或新增的文件路径（如 src/App.jsx），只输出文件路径列表，不要输出其他内容：\n{user_requirement}")
        file_paths = [line.strip() for line in ai_file_list.split('\n') if line.strip()]
        file_contents = []
        for path in file_paths:
            abs_path = os.path.join(self.project_path, path)
            content = FileOperator.read_file(abs_path)
            if content:
                file_contents.append(f"---file-start---\n{path}\n---code-start---\n{content}\n---code-end---\n---file-end---")
            else:
                file_contents.append(f"---file-start---\n{path}\n---code-start---\n(文件不存在，请生成新文件内容)\n---code-end---\n---file-end---")
        files_info = '\n'.join(file_contents)
        format_tip = (
            "请严格按照如下格式回复：\n"
            "每个需要修改或删除的文件用如下格式分隔：\n"
            "---file-start---\n文件路径（如 src/App.jsx）\n---code-start---\n代码内容（完整替换该文件内容）\n---code-end---\n---file-end---\n"
            "如需删除文件，请在 ---code-start--- 和 ---code-end--- 之间填写delete。\n"
            "如有多个文件，重复上述结构。不要输出多余内容。\n"
            "代码必须遵循以下要求：\n"
            "1. 切记不要修改原代码逻辑，除非用户明确要求。\n"
            "2. 必须遵循当前项目的设计语言和风格。\n"
            "3. 尽量不添加新的第三方库进项目，除非用户明确要求。"
        )
        full_prompt = (
            f"以下是项目中需要修改/新增的文件及其内容（如有），请根据用户需求“{user_requirement}”给出每个文件的完整新内容，严格按格式输出：\n{files_info}\n{format_tip}"
        )
        ai_response = self.ai.ask(full_prompt)
        print("AI建议需要修改/新增的文件：")
        print(ai_file_list)
        apply = input("是否将上述修改应用到项目？(y/n)：").strip().lower()
        if apply == 'y':
            self.apply_ai_changes(ai_response)
        else:
            print("已跳过自动应用修改。")

    def apply_ai_changes(self, ai_response):
        print("正在应用AI建议到项目...")
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
                
                # 判断操作类型
                if code_part.lower().strip() == "delete":
                    # 删除文件操作
                    if os.path.exists(abs_path):
                        os.remove(abs_path)
                        structure_changed = True  # 结构发生变化
                        files_changed = True
                    else:
                        print(f"文件不存在，无法删除: {abs_path}")
                else:
                    # 创建或修改文件操作
                    old_exists = os.path.exists(abs_path)
                    FileOperator.write_code_to_file(abs_path, code_part)
                    files_changed = True
                    
                    # 如果是新创建的文件，则结构发生变化
                    if not old_exists:
                        structure_changed = True
                        
            except Exception as e:
                print(f"解析AI回复时出错: {e}")
        
        # 只有在文件结构发生变化时才重新分析项目
        if structure_changed:
            print("检测到文件结构变更，重新分析项目结构...")
            self.analyze_project()
        elif files_changed:
            print("文件内容已更新。")
            
        print("应用完成！")

    def check_project_runnable(self):
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

    def install_dependencies(self):
        """安装项目依赖"""
        print("正在安装项目依赖...")
        try:
            # 检查是否存在 package.json
            package_json_path = os.path.join(self.project_path, 'package.json')
            if not os.path.exists(package_json_path):
                print("项目中没有找到 package.json 文件，无法安装依赖")
                return False
            
            # 检查npm是否可用
            npm_executable = self._find_npm_executable()
            if not npm_executable:
                print("未找到 npm 命令，请确保已安装 Node.js")
                return False
            
            # 执行 npm install，确保在正确的项目目录下执行
            cmd = [npm_executable, 'install']
            print(f"执行命令: {' '.join(cmd)} 在目录: {self.project_path}")
            result = subprocess.run(cmd, 
                                  cwd=self.project_path,  # 确保在用户指定的项目目录下执行
                                  capture_output=True, 
                                  text=True)
            
            if result.returncode == 0:
                print("依赖安装成功！")
                return True
            else:
                print(f"依赖安装失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"安装依赖时出错: {str(e)}")
            return False

    def run_project(self):
        """运行项目"""
        try:
            # 检查是否有项目正在运行
            if self.running_process and self.running_process.poll() is None:
                print("项目已在运行中，请先停止当前项目再启动新项目")
                return
            
            # 检查npm是否可用
            npm_executable = self._find_npm_executable()
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
            print("您也可以在agent中输入 'stop' 来停止项目")
            
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

    def stop_project(self):
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

    def _find_npm_executable(self):
        """查找npm可执行文件的完整路径"""
        try:
            # 首先尝试使用shutil.which查找
            npm_path = shutil.which('npm')
            if npm_path:
                return npm_path
            
            # 在Windows上，也尝试查找npm.cmd
            npm_cmd_path = shutil.which('npm.cmd')
            if npm_cmd_path:
                return npm_cmd_path
                
            return None
        except Exception:
            return None

    def analyze_failure_reason(self, message):
        """分析项目无法运行的原因"""
        # 准备项目信息供AI分析
        project_info = self.analyzer.analyze()
        project_context = json.dumps(project_info, ensure_ascii=False, indent=2)
        
        # 询问AI分析原因
        analysis_prompt = (
            f"项目无法运行，错误信息是：{message}\n"
            f"项目结构信息：\n{project_context}\n"
            "请分析项目无法运行的具体原因，并判断是否因为缺少依赖导致。\n"
            "如果是缺少依赖导致的，请回复'依赖问题'；如果是其他原因，请给出详细解释。\n"
            "只输出分析结果，不要输出其他内容。"
        )
        
        analysis_result = self.ai.ask(analysis_prompt)
        return analysis_result.strip()

def main():
    project_path = input("请输入你的UI项目根目录路径：").strip()
    if not os.path.isdir(project_path):
        print("项目路径不存在！")
        return
    agent = UIProjectAgent(project_path=project_path)
    
    # 检查项目是否可以运行
    runnable, message = agent.check_project_runnable()
    if runnable:
        print(f"项目检查完成: {message}")
        run_choice = input("是否要运行项目？(y/n): ").strip().lower()
        if run_choice == 'y':
            agent.run_project()
    else:
        print(f"项目暂时无法运行: {message}")
        # 让AI分析具体原因
        analysis_result = agent.analyze_failure_reason(message)
        print(f"AI分析结果: {analysis_result}")
        
        # 根据AI分析结果决定下一步操作
        if "依赖问题" in analysis_result or "依赖" in analysis_result:
            install_choice = input("是否要安装项目依赖？(y/n): ").strip().lower()
            if install_choice == 'y':
                if agent.install_dependencies():
                    run_choice = input("依赖安装成功，是否要运行项目？(y/n): ").strip().lower()
                    if run_choice == 'y':
                        agent.run_project()
        else:
            # 如果不是依赖问题，则已经由AI给出了详细解释，用户可以自行决定是否继续
            pass
    
    # 然后进行项目分析并进入修改模式
    print("\n欢迎使用 UI 项目分析与自动修改 Agent，输入你的新需求，exit 退出。")
    while True:
        user_input = input("你的需求：").strip()
        if user_input.lower() == "exit":
            # 停止正在运行的项目
            agent.stop_project()
            break
        elif user_input.lower() == "stop":
            agent.stop_project()
            continue
        elif user_input.lower() == "start":
            agent.run_project()
            continue
        agent.modify_project(user_input)

if __name__ == "__main__":
    main()

