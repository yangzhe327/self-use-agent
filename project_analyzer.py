import os
import json

class ProjectAnalyzer:
    def __init__(self, project_path):
        self.project_path = project_path
        self.project_info = {}

    def analyze(self):
        self.project_info['package'] = self.read_file('package.json')
        self.project_info['config'] = self.read_file('vite.config.js')
        self.project_info['app'] = self.read_file('src/App.jsx')
        self.project_info['main'] = self.read_file('src/pages/main.jsx')
        self.project_info['pages'] = self.find_files('src/pages', ['.js', '.jsx'])
        self.project_info['components'] = self.find_files('src/components', ['.js', '.jsx'])
        return self.project_info

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
