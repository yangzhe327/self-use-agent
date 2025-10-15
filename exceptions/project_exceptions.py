"""
项目自定义异常类
"""

class ProjectBaseException(Exception):
    """项目基础异常类"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ConfigurationError(ProjectBaseException):
    """配置错误异常"""
    def __init__(self, message: str):
        super().__init__(f"配置错误: {message}")


class FileOperationError(ProjectBaseException):
    """文件操作错误异常"""
    def __init__(self, message: str):
        super().__init__(f"文件操作错误: {message}")


class AIInteractionError(ProjectBaseException):
    """AI交互错误异常"""
    def __init__(self, message: str):
        super().__init__(f"AI交互错误: {message}")


class ProjectAnalysisError(ProjectBaseException):
    """项目分析错误异常"""
    def __init__(self, message: str):
        super().__init__(f"项目分析错误: {message}")