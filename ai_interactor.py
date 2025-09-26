import dashscope
import os

class AIInteractor:
    def __init__(self, api_key):
        self.api_key = api_key
        self.messages = []

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