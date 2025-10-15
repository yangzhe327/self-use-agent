"""
AI交互模块
"""

import dashscope
import json
import re
import time
from typing import List, Dict, Any, Optional
from services.config import Config
from exceptions.project_exceptions import AIInteractionError


class AIInteractor:
    def __init__(self, api_key: Optional[str] = None):
        self.config = Config()
        if api_key:
            self.config.api_key = api_key
        self.messages: List[Dict[str, str]] = []
        self.agent = None  # 添加对 agent 的引用

    def set_agent(self, agent):
        """设置 agent 引用，以便调用实际的 action"""
        self.agent = agent

    def ask_with_react(self, prompt: str) -> str:
        """
        使用ReAct策略与AI交互
        """
        try:
            dashscope.api_key = self.config.api_key
            self.messages.append({"role": "user", "content": prompt})
            
            max_iterations = 10
            iteration = 0
            
            while iteration < max_iterations:
                try:
                    response = dashscope.Generation.call(
                        model=self.config.model_name,
                        messages=self.messages,
                        stream=True,
                        result_format='message'
                    )

                    content = ""
                    for resp in response:
                        if resp.status_code == 200 and hasattr(resp, 'output') and resp.output and 'choices' in resp.output:
                            if resp.output['choices'] and len(resp.output['choices']) > 0:
                                choice = resp.output['choices'][0]
                                if 'message' in choice and choice['message']:
                                    delta = choice['message'].get('content', '')
                                    if delta:
                                        content += delta
                        elif resp.status_code != 200:
                            raise AIInteractionError(
                                f"API调用失败: status_code={resp.status_code}, "
                                f"code={getattr(resp, 'code', 'N/A')}, "
                                f"message={getattr(resp, 'message', 'N/A')}"
                            )
                    
                    self.messages.append({"role": "assistant", "content": content.strip()})
                    
                    # 检查是否包含Final Answer，如果包含则直接返回最终答案
                    final_answer_match = re.search(r'Final Answer:\s*(.*)', content, re.DOTALL)
                    if final_answer_match:
                        # 提取Final Answer后的内容作为最终结果
                        final_answer = final_answer_match.group(1).strip()
                        return final_answer
                    
                    # 检查是否包含Action，支持多种格式如 "Action: FUNCTION(args)" 或 "Action: FUNCTION (args)"
                    action_match = re.search(r'Action:\s*(\w+)\s*\((.*?)\)', content, re.IGNORECASE)
                    if action_match:
                        action = action_match.group(1)
                        action_input = action_match.group(2).strip('\"')
                        
                        # 执行Action并获取Observation
                        observation = self.execute_action(action, action_input)
                        
                        # 将Observation添加到对话中
                        observation_message = f"Observation: {observation}"
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
                            # 增强的启发式检查是否像文件路径或有效结果
                            cleaned_line = line.strip()
                            if (cleaned_line and 
                                # 检查是否包含路径分隔符和扩展名，或者看起来像是一个合理的答案
                                (('.' in cleaned_line and ('/' in cleaned_line or '\\' in cleaned_line)) or 
                                 # 或者是不以特定ReAct关键字开头的有效内容
                                 not cleaned_line.startswith(('Thought:', 'Action:', 'Observation:', 'Final Answer:')) and 
                                 len(cleaned_line) > 0)):
                                potential_files.append(cleaned_line)
                        
                        if potential_files:
                            print("从非标准格式中提取到可能的文件列表")
                            return '\n'.join(potential_files)
                        else:
                            # 如果无法提取到有用信息，返回整个内容
                            print("无法从非标准格式中提取有用信息，返回完整内容")
                            return content.strip()
                
                except Exception as e:
                    print(f"调用AI接口时出错: {str(e)}")
                    # 实现重试机制
                    if iteration < self.config.max_retries - 1:
                        wait_time = 2 ** iteration  # 指数退避
                        print(f"等待 {wait_time} 秒后重试...")
                        time.sleep(wait_time)
                        iteration += 1
                        continue
                    else:
                        raise AIInteractionError(f"AI接口调用失败，已重试 {self.config.max_retries} 次: {str(e)}")
            
            # 达到最大迭代次数后，尝试提取Final Answer
            final_content = self.messages[-1]["content"] if self.messages else ""
            final_answer_match = re.search(r'Final Answer:\s*(.*)', final_content, re.DOTALL)
            if final_answer_match:
                final_answer = final_answer_match.group(1).strip()
                return final_answer
            else:
                # 如果没有找到Final Answer，尝试其他方式提取答案
                lines = final_content.strip().split('\n')
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
                return final_content.strip()
        
        except Exception as e:
            raise AIInteractionError(f"AI交互失败: {str(e)}")

    def execute_action(self, action: str, action_input: str) -> str:
        """
        执行特定的Action并返回结果
        """
        # 如果有 agent 引用，则调用 agent 中的实际 action 实现
        if self.agent:
            # 解析参数
            args: List[str] = []
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