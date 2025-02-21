import logging
import sys

def configure_logging(name: str = __name__) -> logging.Logger:
    """Конфигурация единой системы логирования"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Один файловый обработчик на всё приложение
    file_handler = logging.FileHandler('ai_assistant.log')
    file_handler.setFormatter(formatter)
    
    # Консольный вывод только для Streamlit
    stream_handler = logging.StreamHandler(sys.stdout if 'streamlit' in sys.modules else sys.stderr)
    stream_handler.setFormatter(formatter)

    # Очистка старых обработчиков
    if logger.hasHandlers():
        logger.handlers.clear()

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    
    return logger 