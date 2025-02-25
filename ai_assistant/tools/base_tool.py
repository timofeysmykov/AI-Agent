import logging

class BaseTool:
    """Базовый класс для всех инструментов"""
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"{__name__}.{self.name}")
    
    def execute(self, *args, **kwargs) -> str:
        """Выполнить действие инструмента"""
        raise NotImplementedError("Метод execute должен быть реализован в подклассах") 