import dashscope
import os
import json
import re

class AIInteractor:
    def __init__(self, api_key):
        self.api_key = api_key
        self.messages = []
        self.agent = None  # 添加对 agent 的引用

    def set_agent(self, agent):
        """设置 agent 引用，以便调用实际的 action"""
        self.agent = agent
    def ask_with_react(self, prompt):
        """
        使用ReAct策略与AI交互
        """
        dashscope.api_key = self.api_key
        self.messages.append({"role": "user", "content": prompt})
        
        max_iterations = 5
        iteration = 0
        
        while iteration < max_iterations:
            response = dashscope.Generation.call(
                model="qwen3-coder-plus",
                messages=self.messages,
                stream=True,
                result_format='message'
            )

            content = ""
            for resp in response:
                if resp.status_code == 200 and hasattr(resp, 'output') and 'choices' in resp.output:
                    delta = resp.output['choices'][0]['message'].get('content', '')
                    content += delta
                else:
                    print(f"Error in response: {resp}")
            
            self.messages.append({"role": "assistant", "content": content.strip()})
            
            # 检查是否包含Final Answer，如果包含则直接返回最终答案
            final_answer_match = re.search(r'Final Answer:\s*(.*)', content, re.DOTALL)
            if final_answer_match:
                # 提取Final Answer后的内容作为最终结果
                final_answer = final_answer_match.group(1).strip()
                return final_answer
            
            # 检查是否包含Action
            action_match = re.search(r'Action:\s*(\w+)\((.*?)\)', content)
            if action_match:
                action = action_match.group(1)
                action_input = action_match.group(2).strip('\"')
                
                # 执行Action并获取Observation
                observation = self.execute_action(action, action_input)
                
                # 将Observation添加到对话中
                observation_message = f"Observation: {observation}"
                print(observation_message)  # 添加打印以便调试
                self.messages.append({"role": "user", "content": observation_message})
                
                iteration += 1
            else:
                # 没有更多Action，检查是否包含Final Answer行，如果有则提取其后的内容
                # 这种情况是为了处理AI可能没有严格按照格式但在最后一行给出了答案的情况
                lines = content.strip().split('\n')
                final_answer_found = False
                final_answer_lines = []
                
                for line in lines:
                    if line.startswith('Final Answer:'):
                        final_answer_found = True
                        # 提取"Final Answer:"后的内容（如果有）
                        possible_answer = line[13:].strip()  # 13是"Final Answer:"的长度
                        if possible_answer:
                            final_answer_lines.append(possible_answer)
                    elif final_answer_found:
                        # 在找到Final Answer行后，所有后续行都视为答案的一部分
                        final_answer_lines.append(line)
                
                if final_answer_found:
                    final_answer = '\n'.join(final_answer_lines).strip()
                    return final_answer
                
                # 如果连Final Answer行都没有，记录警告并尝试从内容中提取有用信息
                print("警告：AI响应没有遵循ReAct格式，既没有Action也没有Final Answer标识")
                
                # 尝试从内容中提取可能的文件列表（针对文件列表生成场景）
                # 这是一种启发式方法，尝试从非标准格式中提取有用信息
                potential_files = []
                for line in lines:
                    # 简单启发式检查是否像文件路径
                    if line.strip() and ('/' in line or '\\' in line) and '.' in line and not line.startswith(('Thought:', 'Action:', 'Observation:')):
                        potential_files.append(line.strip())
                
                if potential_files:
                    print("从非标准格式中提取到可能的文件列表")
                    return '\n'.join(potential_files)
                else:
                    # 如果无法提取到有用信息，返回整个内容
                    print("无法从非标准格式中提取有用信息，返回完整内容")
                    return content.strip()
        
        # 达到最大迭代次数后，尝试提取Final Answer
        final_answer_match = re.search(r'Final Answer:\s*(.*)', content, re.DOTALL)
        if final_answer_match:
            final_answer = final_answer_match.group(1).strip()
            return final_answer
        else:
            # 如果没有找到Final Answer，尝试其他方式提取答案
            lines = content.strip().split('\n')
            final_answer_found = False
            final_answer_lines = []
            
            for line in lines:
                if line.startswith('Final Answer:'):
                    final_answer_found = True
                    possible_answer = line[13:].strip()
                    if possible_answer:
                        final_answer_lines.append(possible_answer)
                elif final_answer_found:
                    final_answer_lines.append(line)
            
            if final_answer_found:
                final_answer = '\n'.join(final_answer_lines).strip()
                return final_answer
            
            # 最后的备选方案：发出警告并返回整个内容
            print("警告：达到最大迭代次数但未找到Final Answer标识，返回完整内容")
            return content.strip()

    def execute_action(self, action, action_input):
        """
        执行特定的Action并返回结果
        """
        # 如果有 agent 引用，则调用 agent 中的实际 action 实现
        if self.agent:
            # 解析参数
            args = []
            if action_input:
                # 尝试解析参数，支持带引号的参数
                try:
                    import csv
                    from io import StringIO
                    # 使用 csv 模块来处理可能带引号的参数
                    reader = csv.reader(StringIO(action_input), delimiter=',', quotechar='"')
                    # 获取所有行的参数并合并（通常只有一行）
                    for row in reader:
                        args.extend([arg.strip() for arg in row])
                except Exception as e:
                    # 如果CSV解析失败，使用简单的逗号分割
                    print(f"参数解析警告: CSV解析失败，使用简单分割: {e}")
                    args = [arg.strip() for arg in action_input.split(',')]
            
            # 调用 agent 中的实际 action 实现
            try:
                result = self.agent._execute_action(action, args)
                return result
            except Exception as e:
                return f"执行 {action} 操作时出错: {str(e)}"
        else:
            # 如果没有 agent 引用，则返回模拟的响应
            return f"执行了 {action} 操作，输入为: {action_input}"
    
    def remove_last_interaction(self):
        """
        移除最近一次的用户提问和AI回答，用于用户拒绝AI建议的场景
        """
        if len(self.messages) >= 2:
            # 移除最后两条消息（AI的回答和用户的提问）
            self.messages.pop()  # AI的回答
            self.messages.pop()  # 用户的提问