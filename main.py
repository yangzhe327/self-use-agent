import os
import subprocess
import dashscope
import json

QWEN_API_KEY = os.getenv("DASHSCOPE_API_KEY", "YOUR_QWEN_API_KEY")

class UIProjectAgent:
    def __init__(self, project_path):
        self.project_path = project_path
        self.project_info = {}
        self.messages = []  # 用于存储上下文

    def analyze_project(self):
        # 遍历 src 目录，收集页面、组件、路由等信息
        # self.project_info['src_files'] = self.find_files('src', ['.js', '.jsx'])
        self.project_info['package'] = self.read_file('package.json')
        self.project_info['config'] = self.read_file('vite.config.js')
        self.project_info['app'] = self.read_file('src/App.jsx')
        self.project_info['main'] = self.read_file('src/pages/main.jsx')
        self.project_info['pages'] = self.find_files('src/pages', ['.js', '.jsx'])
        self.project_info['components'] = self.find_files('src/components', ['.js', '.jsx'])
        # 可扩展分析 package.json、路由、状态管理等
        # 初始化上下文，只在第一次分析时添加项目结构
        if not self.messages:
            self.messages.append({
                "role": "system",
                "content": f"当前项目结构：{json.dumps(self.project_info, ensure_ascii=False, indent=2)}"
            })
    
    def find_files(self, folder, exts):
        result = []
        abs_folder = os.path.join(self.project_path, folder)
        if not os.path.exists(abs_folder):
            return result
        for root, _, files in os.walk(abs_folder):
            for f in files:
                if any(f.endswith(ext) for ext in exts):
                    result.append(os.path.relpath(os.path.join(root, f), self.project_path))
        return result

    def read_file(self, rel_path):
        abs_path = os.path.join(self.project_path, rel_path)
        if os.path.exists(abs_path):
            with open(abs_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def ask_ai(self, prompt):
        dashscope.api_key = QWEN_API_KEY
        self.messages.append({"role": "user", "content": prompt})
        response = dashscope.Generation.call(
            model="qwen3-coder-plus",
            messages=self.messages,
            stream=True
        )
        content = ""
        for resp in response:
            if hasattr(resp, 'output') and 'choices' in resp.output:
                delta = resp.output['choices'][0]['message'].get('content', '')
                print(delta, end='', flush=True)
                content += delta
        print()
        self.messages.append({"role": "assistant", "content": content.strip()})
        return content.strip()

    def modify_project(self, user_requirement):
        # 分析项目结构（只在第一次会话时加入上下文）
        self.analyze_project()
        # 第一步：让AI只输出需要修改/新增的文件路径列表
        print("AI正在分析需要修改/新增的文件...")
        ai_file_list = self.ask_ai(f"请根据当前项目结构和如下需求，列出所有需要修改或新增的文件路径（如 src/App.jsx），只输出文件路径列表，不要输出其他内容：\n{user_requirement}")
        print("AI建议需要修改/新增的文件：")
        # 解析AI输出的文件路径
        print(ai_file_list)
        file_paths = [line.strip() for line in ai_file_list.split('\n') if line.strip()]
        # 第二步：自动读取这些文件内容（如有），再发给AI让其基于内容给出修改建议或新文件代码
        file_contents = []
        for path in file_paths:
            content = self.read_file(path)
            if content:
                file_contents.append(f"---file-start---\n{path}\n---code-start---\n{content}\n---code-end---\n---file-end---")
            else:
                file_contents.append(f"---file-start---\n{path}\n---code-start---\n(文件不存在，请生成新文件内容)\n---code-end---\n---file-end---")
        files_info = '\n'.join(file_contents)
        # 让AI基于文件内容和需求给出修改建议
        format_tip = (
            "请严格按照如下格式回复：\n"
            "每个需要修改的文件用如下格式分隔：\n"
            "---file-start---\n文件路径（如 src/App.jsx）\n---code-start---\n代码内容（完整替换该文件内容）\n---code-end---\n---file-end---\n"
            "如有多个文件，重复上述结构。不要输出多余内容。"
        )
        full_prompt = (
            f"以下是项目中需要修改/新增的文件及其内容（如有），请根据用户需求“{user_requirement}”给出每个文件的完整新内容，严格按格式输出：\n{files_info}\n{format_tip}"
        )
        print("\nAI建议的具体修改：")
        ai_response = self.ask_ai(full_prompt)
        # 询问用户是否应用到项目
        apply = input("是否将上述修改应用到项目？(y/n)：").strip().lower()
        if apply == 'y':
            self.apply_ai_changes(ai_response)
        else:
            print("已跳过自动应用修改。")

    def apply_ai_changes(self, ai_response):
        """
        解析AI回复的固定格式，自动写入相关文件。
        格式：
        ---file-start---
        文件路径
        ---code-start---
        代码内容
        ---code-end---
        ---file-end---
        """
        print("正在应用AI建议到项目...")
        files = ai_response.split('---file-start---')
        for file_block in files:
            file_block = file_block.strip()
            if not file_block:
                continue
            try:
                path_part = file_block.split('---code-start---')[0].strip()
                code_part = file_block.split('---code-start---')[1].split('---code-end---')[0].strip()
                file_path = self.resolve_file_path(path_part)
                self.write_code_to_file(file_path, code_part)
            except Exception as e:
                print(f"解析AI回复时出错: {e}")
        print("应用完成！")

    def resolve_file_path(self, file_info):
        # 只取第一行作为文件路径
        rel_path = file_info.split('\n')[0].strip()
        abs_path = os.path.join(self.project_path, rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        return abs_path

    def write_code_to_file(self, file_path, code):
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)
        print(f"已写入文件: {file_path}")

def main():
    project_path = input("请输入你的UI项目根目录路径：").strip()
    if not os.path.isdir(project_path):
        print("项目路径不存在！")
        return
    agent = UIProjectAgent(project_path=project_path)
    # 分析项目结构，初始化上下文
    agent.analyze_project()
    # 新增：询问AI如何安装和运行该项目
    print("\nAI建议的安装和运行方法：")
    install_prompt = "请根据当前项目结构，给出详细的安装和运行步骤（包括依赖安装、启动命令等），并说明注意事项。切记只做分析不要提出修改意见"
    agent.ask_ai(install_prompt)
    print("\n欢迎使用 UI 项目分析与自动修改 Agent，输入你的新需求，exit 退出。")
    while True:
        user_input = input("你的需求：")
        if user_input.strip().lower() == "exit":
            break
        agent.modify_project(user_input)

if __name__ == "__main__":
    main()
