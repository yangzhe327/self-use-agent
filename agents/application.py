"""
主应用类
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
        self.ai.set_agent(self)  # 设置 agent 引用
        self.project_info: Dict[str, Any] = {}
        self.context_initialized = False
        self.project_commands = ProjectCommands(project_path)
        self.ai_commands = AICommands(self.ai, project_path, self.analyzer)

    def analyze_project(self) -> None:
        """
        分析项目结构
        """
        try:
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
        except Exception as e:
            raise ProjectBaseException(f"分析项目时出错: {str(e)}")

    def modify_project(self, user_requirement: str) -> None:
        """
        根据用户需求修改项目
        """
        try:
            self.analyze_project()
            self.ai_commands.project_info = self.project_info
            self.ai_commands.modify_project(user_requirement)
        except Exception as e:
            raise ProjectBaseException(f"修改项目时出错: {str(e)}")

    def check_project_runnable(self) -> tuple[bool, str]:
        """检查项目是否可以运行"""
        return self.project_commands.check_project_runnable()

    def install_dependencies(self) -> bool:
        """安装项目依赖"""
        return self.project_commands.install_dependencies()

    def run_project(self) -> None:
        """运行项目"""
        self.project_commands.run_project()

    def stop_project(self) -> None:
        """停止正在运行的项目"""
        self.project_commands.stop_project()

    def analyze_failure_reason(self, message: str) -> str:
        """分析项目无法运行的原因"""
        return self.ai_commands.analyze_failure_reason(message)

    def _execute_action(self, action_name: str, args: list) -> str:
        """
        执行特定行动
        """
        try:
            if action_name == "analyze_project":
                self.analyze_project()
                return "项目结构已分析并更新"
                
            elif action_name == "read_file" and args:
                file_path = args[0]
                abs_path = os.path.join(self.project_path, file_path)
                if os.path.exists(abs_path):
                    with open(abs_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    return f"文件 {file_path} 的内容:\n{content[:1000]}..."  # 限制内容长度
                else:
                    return f"文件 {file_path} 不存在"
                    
            elif action_name == "write_file" and len(args) >= 2:
                file_path = args[0]
                content = args[1] if len(args) == 2 else ' '.join(args[1:])
                abs_path = os.path.join(self.project_path, file_path)
                os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                with open(abs_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return f"文件 {file_path} 已写入"
                
            else:
                return f"未知行动: {action_name} 或参数不足"
        except Exception as e:
            return f"执行行动时出错: {str(e)}"


def main():
    try:
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
            print(f"分析结果: {analysis_result}")
            
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
        print("\n输入你的新需求，exit 退出")
        while True:
            user_input = input("你的需求：").strip()
            if user_input.lower() == "exit":
                # 停止正在运行的项目
                agent.stop_project()
                break
            agent.modify_project(user_input)
    
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(0)
    except ProjectBaseException as e:
        print(f"项目错误: {e.message}")
        sys.exit(1)
    except Exception as e:
        print(f"程序运行出错: {str(e)}")
        sys.exit(1)