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
                "content": f"当前项目结构：{json.dumps(self.project_info, ensure_ascii=False, indent=2)}"
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
            "如有多个文件，重复上述结构。不要输出多余内容。"
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
        for file_block in files:
            file_block = file_block.strip()
            if not file_block:
                continue
            try:
                path_part = file_block.split('---code-start---')[0].strip()
                code_part = file_block.split('---code-start---')[1].split('---code-end---')[0].strip()
                rel_path = path_part.split('\n')[0].strip()
                abs_path = os.path.join(self.project_path, rel_path)
                if code_part.lower().strip() == "delete":
                    self.delete_file(abs_path)
                else:
                    FileOperator.write_code_to_file(abs_path, code_part)
            except Exception as e:
                print(f"解析AI回复时出错: {e}")
        print("应用完成！")

    def delete_file(self, abs_path):
        try:
            if os.path.exists(abs_path):
                os.remove(abs_path)
                print(f"已删除文件: {abs_path}")
            else:
                print(f"文件不存在，无法删除: {abs_path}")
        except Exception as e:
            print(f"删除文件时出错: {e}")

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
