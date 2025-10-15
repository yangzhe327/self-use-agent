"""
AI命令处理模块
"""

import json
import os
from typing import Dict, Any
from services.ai_interactor import AIInteractor
from services.file_operator import FileOperator


class AICommands:
    """处理AI相关命令的类"""
    
    def __init__(self, ai_interactor: AIInteractor, project_path: str, analyzer):
        self.ai = ai_interactor
        self.project_path = project_path
        self.analyzer = analyzer
        self.project_info: Dict[str, Any] = {}

    def analyze_failure_reason(self, message: str) -> str:
        """分析项目无法运行的原因"""
        # 准备项目信息供AI分析
        project_info = self.analyzer.analyze()
        project_context = json.dumps(project_info, ensure_ascii=False, indent=2)
        
        # 使用ReAct策略分析失败原因
        analysis_prompt = (
            f"项目无法运行，错误信息是：{message}\n"
            f"项目结构信息：\n{project_context}\n"
            "请使用ReAct策略分析项目无法运行的具体原因，并判断是否因为缺少依赖导致。\n"
            "请按照以下格式进行推理和行动：\n"
            "Thought: 分析错误信息和项目结构，确定可能的原因\n"
            "Action: analyze_project_issues()\n"
            "Observation: 根据分析结果，确定具体原因\n"
            "Final Answer: 如果是缺少依赖导致的，请回复'依赖问题'；如果是其他原因，请给出详细解释。\n"
            "只输出分析结果，不要输出其他内容。"
        )
        
        analysis_result = self.ai.ask_with_react(analysis_prompt)
        return analysis_result.strip()

    def modify_project(self, user_requirement: str) -> None:
        """
        根据用户需求修改项目
        """
        self.project_info = self.analyzer.analyze()
        
        # 使用ReAct策略生成文件列表
        react_prompt = self._generate_react_prompt_for_file_list(user_requirement)
        ai_file_list = self.ai.ask_with_react(react_prompt)
        
        file_paths = [line.strip() for line in ai_file_list.split('\n') if line.strip()]
        file_contents = []
        for path in file_paths:
            abs_path = os.path.join(self.project_path, path)
            content = FileOperator.read_file(abs_path, self.project_path)
            if content:
                file_contents.append(f"---file-start---\n{path}\n---code-start---\n{content}\n---code-end---\n---file-end---")
            else:
                file_contents.append(f"---file-start---\n{path}\n---code-start---\n(文件不存在，请生成新文件内容)\n---code-end---\n---file-end---")
        files_info = '\n'.join(file_contents)
        format_tip = (
            "请严格按照如下格式回复：\n"
            "每个需要修改或删除或新增的文件用如下格式分隔：\n"
            "---file-start---\n文件路径（如 src/App.jsx）\n---code-start---\n代码内容（完整替换该文件内容）\n---code-end---\n---file-end---\n"
            "如需删除文件，请在 ---code-start--- 和 ---code-end--- 之间填写delete。\n"
            "如有多个文件，重复上述结构。不要输出多余内容。\n"
            "代码必须遵循以下要求：\n"
            "1. 切记不要修改原代码逻辑，除非用户明确要求。\n"
            "2. 必须遵循当前项目的设计语言和风格。\n"
            "3. table请使用material-react-table。\n"
            "4. 组件请使用material-ui中的组件。\n"
            "5. 尽量不添加新的第三方库进项目，除非用户明确要求。"
        )
        full_prompt = (
            f"以下项目中需要修改/新增的文件及其内容（如有），{files_info}\n 请根据用户需求“{user_requirement}”给出每个文件的完整新内容。遵循以下规则：\n{format_tip}"
        )
        
        # 使用ReAct策略生成文件修改内容
        react_modify_prompt = self._generate_react_prompt_for_modifications(full_prompt)
        ai_response = self.ai.ask_with_react(react_modify_prompt)
        
        print("建议需要修改的文件：")
        print(ai_file_list)
        apply = input("是否将上述修改应用到项目？(y/n)：").strip().lower()
        if apply == 'y':
            self.apply_ai_changes(ai_response)
        else:
            print("已跳过自动应用修改。")
            # 用户拒绝应用修改时，清除相关的两次对话历史（文件列表请求+具体内容请求）
            self.ai.remove_last_interaction()  # 清除具体内容请求的对话历史
            self.ai.remove_last_interaction()  # 清除文件列表请求的对话历史

    def _generate_react_prompt_for_file_list(self, user_requirement: str) -> str:
        """
        生成用于ReAct策略的文件列表生成提示
        """
        react_prompt = (
            f"根据用户需求生成需要修改的文件列表。请使用ReAct策略来思考和行动。\n"
            f"用户需求：{user_requirement}\n"
            f"当前项目信息：{json.dumps(self.project_info, ensure_ascii=False, indent=2)}\n\n"
            f"请按照以下格式进行推理和行动：\n"
            f"Thought: 分析用户需求和项目结构，确定需要修改哪些文件。如果需要了解特定文件的内容以做出判断，可以使用read_file操作。\n"
            f"Action: analyze_project()  # 可用的Action包括: analyze_project(), read_file(\"文件路径\"), write_file(\"文件路径\", \"文件内容\")\n"
            f"Observation: 根据分析结果，列出需要修改或删除或新增的文件路径\n"
            f"Final Answer: 只输出文件路径列表，每行一个文件路径（如 src/App.jsx），只输出文件路径列表，不输出其他内容\n\n"
            f"重要提示：\n"
            f"1. 在Thought阶段，仔细分析用户需求，考虑哪些文件可能需要修改\n"
            f"2. 如果需要查看特定文件的内容以判断是否需要修改，请使用read_file操作\n"
            f"3. 只有在充分分析后，才给出最终的文件列表\n"
            f"4. 不要包含你不确定是否需要修改的文件"
        )
        return react_prompt

    def _generate_react_prompt_for_modifications(self, full_prompt: str) -> str:
        """
        生成用于ReAct策略的文件修改内容生成提示
        """
        react_prompt = (
            f"根据用户需求和文件内容生成具体的修改方案。请使用ReAct策略来思考和行动。\n"
            f"任务描述：{full_prompt}\n\n"
            f"请按照以下格式进行推理和行动：\n"
            f"Thought: 分析用户需求和当前文件内容，确定如何修改。如果需要查看其他相关文件以确保修改的一致性，可以使用read_file操作。\n"
            f"Action: analyze_project()  # 可用的Action包括: analyze_project(), read_file(\"文件路径\"), write_file(\"文件路径\", \"文件内容\")\n"
            f"Observation: 根据分析结果，生成符合要求的代码修改方案\n"
            f"Final Answer: 严格按照指定格式输出文件修改内容\n\n"
            f"重要提示：\n"
            f"1. 在Thought阶段，仔细分析用户需求和提供的文件内容\n"
            f"2. 如果需要查看其他相关文件以确保修改的一致性，请使用read_file操作\n"
            f"3. 确保生成的代码符合项目的现有风格和结构"
        )
        return react_prompt

    def apply_ai_changes(self, ai_response: str) -> None:
        """
        应用AI生成的修改到项目
        """
        print("正在应用建议到项目...")
        files = ai_response.split('---file-start---')
        files_changed = False
        structure_changed = False
        
        for file_block in files:
            file_block = file_block.strip()
            if not file_block:
                continue
            try:
                # 安全地分割文件块，避免索引越界
                parts = file_block.split('---code-start---')
                if len(parts) < 2:
                    print(f"警告：文件块格式不正确，跳过处理: {file_block[:50]}...")
                    continue
                    
                path_part = parts[0].strip()
                code_parts = parts[1].split('---code-end---')
                if len(code_parts) < 1:
                    print(f"警告：文件块缺少代码结束标记，跳过处理: {path_part[:50]}...")
                    continue
                    
                code_part = code_parts[0].strip()
                rel_path = path_part.split('\n')[0].strip()
                abs_path = os.path.join(self.project_path, rel_path)
                
                # 判断操作类型
                if code_part.lower().strip() == "delete":
                    # 删除文件操作
                    if os.path.exists(abs_path):
                        os.remove(abs_path)
                        structure_changed = True  # 结构发生变化
                        files_changed = True
                        print(f"已删除文件: {abs_path}")
                    else:
                        print(f"文件不存在，无法删除: {abs_path}")
                else:
                    # 创建或修改文件操作
                    old_exists = os.path.exists(abs_path)
                    if FileOperator.write_code_to_file(abs_path, code_part, self.project_path):
                        files_changed = True
                        
                        # 如果是新创建的文件，则结构发生变化
                        if not old_exists:
                            structure_changed = True
                    else:
                        print(f"写入文件失败: {abs_path}")
                        
            except Exception as e:
                print(f"解析回复时出错: {e}")
        
        # 只有在文件结构发生变化时才重新分析项目
        if structure_changed:
            print("检测到文件结构变更，重新分析项目结构...")
            self.project_info = self.analyzer.analyze()
        elif files_changed:
            print("文件内容已更新。")
            
        print("应用完成！")



