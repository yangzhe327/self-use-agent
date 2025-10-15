"""
Project Custom Exception Classes
"""

class ProjectBaseException(Exception):
    """Project Base Exception Class"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ConfigurationError(ProjectBaseException):
    """Configuration Error Exception"""
    def __init__(self, message: str):
        super().__init__(f"Configuration error: {message}")


class FileOperationError(ProjectBaseException):
    """File Operation Error Exception"""
    def __init__(self, message: str):
        super().__init__(f"File operation error: {message}")


class AIInteractionError(ProjectBaseException):
    """AI Interaction Error Exception"""
    def __init__(self, message: str):
        super().__init__(f"AI interaction error: {message}")


class ProjectAnalysisError(ProjectBaseException):
    """Project Analysis Error Exception"""
    def __init__(self, message: str):
        super().__init__(f"Project analysis error: {message}")