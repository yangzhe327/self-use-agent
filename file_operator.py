import os

class FileOperator:
    @staticmethod
    def write_code_to_file(file_path, code):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)
        print(f"已写入文件: {file_path}")

    @staticmethod
    def read_file(file_path):
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
