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

    def ask(self, prompt):
        dashscope.api_key = self.api_key
        self.messages.append({"role": "user", "content": prompt})
        response = dashscope.Generation.call(
            model="qwen3-coder-plus",
            messages=self.messages,
            stream=True,
            result_format='message'  # 添加result_format参数
        )

        content = ""
        for resp in response:
            if resp.status_code == 200 and hasattr(resp, 'output') and 'choices' in resp.output:
                delta = resp.output['choices'][0]['message'].get('content', '')
                # print(delta, end='', flush=True)
                content += delta
            else:
                # 处理可能的错误情况
                print(f"Error in response: {resp}")
        print()
        self.messages.append({"role": "assistant", "content": content.strip()})
        return content.strip()
    
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
            
            # 检查是否包含Action
            action_match = re.search(r'Action:\s*(\w+)\((.*?)\)', content)
            if action_match:
                action = action_match.group(1)
                action_input = action_match.group(2).strip('\"')
                
                # 执行Action并获取Observation
                observation = self.execute_action(action, action_input)
                
                # 将Observation添加到对话中
                observation_message = f"Observation: {observation}"
                print
                self.messages.append({"role": "user", "content": observation_message})
                
                iteration += 1
            else:
                # 没有更多Action，返回最终答案
                return content.strip()
        
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
                # 简单处理，按逗号分割，但保留引号内的逗号
                import csv
                from io import StringIO
                # 使用 csv 模块来处理可能带引号的参数
                reader = csv.reader(StringIO(action_input), delimiter=',', quotechar='"')
                args = next(reader, [])
                # 去除参数两边的空格
                args = [arg.strip() for arg in args]
            
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