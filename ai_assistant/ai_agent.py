import logging
from typing import Dict, Any, Optional, List, Union
import os
from pathlib import Path
import re
import traceback
import time
import anthropic
from enum import Enum

# Настройка логирования
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_assistant.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)

# Определяем пути к файлам
SYSTEM_PROMPT_PATH = Path(__file__).parent / "prompts" / "system_instruction.txt"

class AIAssistantError(Exception):
    """Базовый класс для исключений AI ассистента"""
    pass

class APIError(AIAssistantError):
    """Ошибки при работе с API"""
    pass

class SearchError(AIAssistantError):
    """Ошибки при поиске информации"""
    pass

class ValidationError(AIAssistantError):
    """Ошибки валидации данных"""
    pass

class BaseTool:
    """Базовый класс для всех инструментов"""
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"{__name__}.{self.name}")
    
    def execute(self, *args, **kwargs) -> str:
        """Выполнить действие инструмента"""
        raise NotImplementedError("Метод execute должен быть реализован в подклассах")

class ClaudeAgentCore:
    """Основной класс для обработки запросов через Claude API"""
    
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # секунды
    MAX_HISTORY_LENGTH = 10
    
    # Инструкции для системного промпта
    WORKFLOW_INSTRUCTIONS = """
    [Workflow: Thought-Action-Observation]
    
    1. Thought (Размышление):
       - Анализ запроса пользователя
       - Определение необходимых действий
       - Оценка имеющейся информации
       - Формулировка гипотез
    
    2. Action (Действие):
       - Формирование ответа
       - Применение найденных решений
       - Предложение конкретных шагов
    
    3. Observation (Наблюдение):
       - Анализ результатов
       - Оценка эффективности
       - Формирование финального ответа
       - Планирование следующих шагов
    """
    
    EXAMPLES = """
    [Пример диалога с Thought-Action-Observation]
    
    Пользователь: "Я постоянно волнуюсь перед выступлениями"
    
    Thought: Пользователь испытывает сильную тревогу перед публичными выступлениями. В его сообщении чувствуется беспокойство и неуверенность. Необходимо предложить конкретные техники для работы с тревогой и повышения уверенности.
    
    Action: Предлагаю следующие техники:
    1. Техника "5-4-3-2-1" для управления тревогой
    2. Метод предварительной подготовки и визуализации
    3. Дыхательные упражнения для снижения стресса
    4. Практика позитивных утверждений
    
    Observation: Я понимаю, как сильно вас беспокоят публичные выступления. Это абсолютно нормально испытывать такие чувства. Давайте разберем несколько эффективных техник, которые помогут вам чувствовать себя увереннее:

    1. Техника "5-4-3-2-1" для быстрого снижения тревоги:
       - Назовите 5 предметов, которые вы видите
       - 4 вещи, которые вы можете потрогать
       - 3 звука, которые слышите
       - 2 запаха, которые ощущаете
       - 1 вкус
       Это помогает "заземлиться" и вернуть контроль над тревожными мыслями.

    2. Метод подготовки и визуализации:
       - Заранее напишите план выступления
       - Представьте себе успешное выступление в деталях
       - Порепетируйте перед зеркалом или запишите себя на видео
       
    3. Дыхательное упражнение "4-7-8":
       - Вдох на 4 счета
       - Задержка на 7 счетов
       - Выдох на 8 счетов
       Повторяйте 4-5 раз перед выступлением.

    Давайте начнем с одной техники, которая покажется вам наиболее подходящей. Какая из них вызывает у вас наибольший интерес? Мы можем подробно разобрать её применение и постепенно добавлять другие методы.
    """
    
    def __init__(self, claude_api_key: str):
        if not claude_api_key:
            raise ValidationError("API ключ Claude не может быть пустым")
            
        self.claude_api_key = claude_api_key
        self.logger = logging.getLogger(__name__)
        
        # Загрузка системного промпта
        try:
            self.system_messages = self._initialize_system_messages()
        except Exception as e:
            error_msg = f"Ошибка при инициализации системных сообщений: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            raise AIAssistantError(error_msg)
            
        # История сообщений
        self.message_history: List[Dict[str, str]] = []
        
        # Инициализация клиента Claude
        self.claude_client = anthropic.Anthropic(api_key=claude_api_key)
    
    def _initialize_system_messages(self) -> List[Dict[str, str]]:
        """Инициализация системных сообщений с валидацией"""
        try:
            with open(SYSTEM_PROMPT_PATH, 'r', encoding='utf-8') as f:
                base_prompt = f.read().strip()
                
            if not base_prompt:
                raise ValidationError("Системный промпт не может быть пустым")
            
            full_prompt = f"""{base_prompt}
            
            [Workflow]
            {self.WORKFLOW_INSTRUCTIONS}
            [Примеры]
            {self.EXAMPLES}"""
            
            self.logger.info("Загружен системный промпт длиной %d символов", len(full_prompt))
            self.logger.debug("Системный промпт: %s", full_prompt[:200] + "...")
            
            return [{"role": "system", "content": full_prompt}]
            
        except FileNotFoundError:
            error_msg = f"Файл системного промпта не найден: {SYSTEM_PROMPT_PATH}"
            self.logger.error(error_msg)
            raise AIAssistantError(error_msg)
            
        except Exception as e:
            error_msg = f"Ошибка при чтении системного промпта: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            raise AIAssistantError(error_msg)
    
    def process_query(self, user_input: str) -> str:
        """Обработка пользовательского запроса с использованием workflow thought-action-observation"""
        if not user_input.strip():
            raise ValidationError("Пользовательский запрос не может быть пустым")
            
        self.logger.info(f"Получен новый запрос: {user_input[:100]}...")
        
        try:
            # Формируем контекст с историей
            messages = self._prepare_context(user_input)
            
            # Улучшенный промпт для анализа
            thought_prompt = f"""
            [Текущий запрос]
            {user_input}
            
            [Инструкция]
            1. Проанализируйте запрос пользователя, определите:
               - Основную проблему или потребность
               - Эмоциональное состояние
               - Контекст ситуации
               
            2. Подготовьте ответ, который должен:
               - Начинаться с искреннего признания чувств и опыта пользователя
               - Предлагать 2-3 конкретные, применимые техники или решения
               - Для каждой техники обязательно указывать:
                 * Подробную пошаговую инструкцию по выполнению
                 * Частоту и продолжительность применения
                 * Ожидаемый результат
               - Включать примеры из похожих ситуаций
               - Завершаться предложением конкретного первого шага
               
            3. Используйте естественный разговорный стиль:
               - Пишите простым языком, как если бы вы говорили с другом
               - Объединяйте связанные мысли в абзацы
               - Делайте плавные переходы между темами
               - Задавайте уточняющие вопросы
            
            Формат ответа:
            Thought: [ваш анализ ситуации и эмоционального состояния]
            Action: [план помощи и конкретные техники]
            Observation: [финальный ответ в естественном, разговорном стиле]
            """
            
            messages.append({"role": "user", "content": thought_prompt})
            
            # Получаем ответ модели
            for attempt in range(self.MAX_RETRIES):
                try:
                    response = self._call_llm(messages)
                    break
                except APIError as e:
                    if attempt == self.MAX_RETRIES - 1:
                        raise
                    self.logger.warning(f"Попытка {attempt + 1} не удалась: {str(e)}")
                    time.sleep(self.RETRY_DELAY)
            
            # Обновляем историю
            self._update_history(user_input, response)
            
            return self._postprocess_response(response)
            
        except Exception as e:
            error_msg = f"Ошибка при обработке запроса: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            raise AIAssistantError(error_msg)
    
    def _count_tokens(self, text: str) -> int:
        """Подсчет примерного количества токенов в тексте"""
        return len(text.split()) // 0.75

    def _prepare_context(self, user_input: str) -> List[Dict[str, str]]:
        """Подготовка контекста с учетом истории"""
        context = self.system_messages.copy()
        
        # Добавляем последние сообщения из истории
        if self.message_history:
            context.extend(self.message_history[-self.MAX_HISTORY_LENGTH:])
            
        context.append({"role": "user", "content": user_input})
        
        # Проверяем и обрезаем контекст по токенам
        MAX_TOKENS = 4000
        current_tokens = sum(self._count_tokens(m["content"]) for m in context)
        while current_tokens > MAX_TOKENS and len(context) > 1:
            context.pop(1)
            current_tokens = sum(self._count_tokens(m["content"]) for m in context)
            
        return context
    
    def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        """Вызов Claude с обработкой ошибок"""
        try:
            # Извлекаем системный промпт из сообщений
            system_message = next((msg["content"] for msg in messages if msg["role"] == "system"), None)
            # Фильтруем сообщения, оставляя только user и assistant
            chat_messages = [msg for msg in messages if msg["role"] != "system"]
            
            self.logger.info("Отправка запроса к Claude API с %d сообщениями", len(messages))
            self.logger.debug("Первые 200 символов системного промпта: %s", 
                          system_message[:200] + "..." if system_message else "Нет системного промпта")
            
            response = self.claude_client.messages.create(
                model="claude-3-haiku-20240307",
                system=system_message,
                messages=chat_messages,
                temperature=0.7,
                max_tokens=1200
            )
            
            result = response.content[0].text
            self.logger.info("Получен ответ длиной %d символов", len(result))
            
            # Обрабатываем внутренний диалог, сохраняя только финальный ответ
            if "Thought:" in result and "Action:" in result and "Observation:" in result:
                self.logger.debug("Обнаружен внутренний диалог в ответе")
                # Берем всё, что после последнего Observation:
                parts = result.rsplit("Observation:", 1)
                if len(parts) > 1:
                    final_response = parts[1].strip()
                    # Убираем кавычки в начале и конце, если они есть
                    final_response = re.sub(r'^["\']|["\']$', '', final_response)
                    # Улучшаем форматирование
                    final_response = self._improve_formatting(final_response)
                    return final_response
            
            return self._improve_formatting(result)
            
        except Exception as e:
            error_msg = f"Ошибка при вызове Claude API: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            raise APIError(error_msg)
    
    def _improve_formatting(self, text: str) -> str:
        """Улучшение форматирования текста"""
        # Убираем лишние пробелы и переносы строк
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Форматируем списки и абзацы
        text = re.sub(r'(\d+\.) ', r'\n\n\1 ', text)  # Нумерованные списки
        text = re.sub(r'([-•]) ', r'\n\1 ', text)     # Маркированные списки
        
        # Форматируем описания техник
        text = re.sub(r'([.!?]) (Техника|Метод|Упражнение)', r'\1\n\n\2', text)
        text = re.sub(r'(:)(\s+)', r'\1\n', text)  # Перенос после двоеточия в описании техники
        
        # Форматируем обычные предложения (объединяем в абзацы)
        text = re.sub(r'([.!?]) ([А-ЯA-Z][^.]*)([.!?]) ', r'\1 \2\3\n\n', text)
        
        # Убираем лишние переносы строк
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def _update_history(self, user_input: str, response: str) -> None:
        """Обновление истории сообщений"""
        self.message_history.append({"role": "user", "content": user_input})
        self.message_history.append({"role": "assistant", "content": response})
        
        # Ограничиваем размер истории
        if len(self.message_history) > self.MAX_HISTORY_LENGTH * 2:
            self.message_history = self.message_history[-self.MAX_HISTORY_LENGTH * 2:]
    
    def _postprocess_response(self, raw_response: str) -> str:
        """Постобработка ответа с валидацией"""
        if not raw_response:
            raise ValidationError("Получен пустой ответ от модели")
            
        # Удаление технических блоков
        cleaned = re.sub(r'```json\s*{.*?}\s*```', '', raw_response, flags=re.DOTALL)
        cleaned = re.sub(r'→\s*\w+:', '', cleaned)
        cleaned = cleaned.strip()
        
        if not cleaned:
            raise ValidationError("После обработки получен пустой ответ")
            
        return cleaned
