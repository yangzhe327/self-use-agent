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
                    "你是一位资深的UI开发工程师和UX设计师，精通前端架构、交互设计、用户体验优化。"
                    "你的任务是根据项目结构和用户需求，提出专业的分析、建议，并生成高质量、可直接应用的代码。"
                    "在输出时请遵循如下要求：\n"
                    "1. 代码需完整、规范、易维护。\n"
                    "2. 如涉及文件删除，请严格按指定格式输出。\n"
                    "3. 回答要简明扼要，避免无关内容。\n"
                    "当前项目结构如下：\n"
                    f"{json.dumps(self.project_info, ensure_ascii=False, indent=2)}"
                )
            })
            self.context_initialized = True

    def modify_project(self, user_requirement):
        self.analyze_project()
        print("AI正在分析需要修改/新增的文件...")
        ai_file_list = self.ai.ask(f"请根据当前项目结构和如下需求，列出所有需要修改或新增的文件路径（如 src/App.jsx），只输出文件路径列表，不要输出其他内容：\n{user_requirement}")
        print("AI建议需要修改/新增的文件：")
        print(ai_file_list)
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
        print("\nAI建议的具体修改：")
        ai_response = self.ai.ask(full_prompt)
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

def main():
    project_path = input("请输入你的UI项目根目录路径：").strip()
    if not os.path.isdir(project_path):
        print("项目路径不存在！")
        return
    agent = UIProjectAgent(project_path=project_path)
    agent.analyze_project()
    print("\nAI建议的安装和运行方法：")
    install_prompt = "请根据当前项目结构，给出详细的安装和运行步骤（包括依赖安装、启动命令等），并说明注意事项。切记只做分析不要提出修改意见"
    agent.ai.ask(install_prompt)
    print("\n欢迎使用 UI 项目分析与自动修改 Agent，输入你的新需求，exit 退出。")
    while True:
        user_input = input("你的需求：")
        if user_input.strip().lower() == "exit":
            break
        agent.modify_project(user_input)

if __name__ == "__main__":
    main()
