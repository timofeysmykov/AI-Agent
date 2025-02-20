import requests
import json
import logging
from typing import Dict, Any, Optional, List, Union
import os
from pathlib import Path
from perplexity import Perplexity
import re
from openai import OpenAI
from jinja2 import Template
from datetime import datetime
import traceback
import time
import anthropic

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

class PerplexitySearchTool(BaseTool):
    """Инструмент для поиска информации через Perplexity API"""
    
    TRUSTED_SOURCES = ["who.int", "nimh.nih.gov", "apa.org", "mayoclinic.org"]
    CACHE_EXPIRATION = 3600  # 1 час в секундах
    
    def __init__(self, api_key: str):
        super().__init__(
            name="perplexity_search",
            description="Поиск информации с использованием Perplexity AI"
        )
        if not api_key:
            raise ValidationError("API ключ не может быть пустым")
        self.api_key = api_key
        self.cache: Dict[str, Dict[str, Union[str, float]]] = {}
    
    def execute(self, query: str) -> str:
        """Выполняет поиск с кэшированием результатов"""
        if not query.strip():
            raise ValidationError("Поисковый запрос не может быть пустым")
            
        try:
            # Проверяем кэш
            cached_result = self._get_from_cache(query)
            if cached_result:
                self.logger.info(f"Найден кэшированный результат для запроса: {query}")
                return cached_result
            
            # Выполняем поиск
            client = Perplexity(api_key=self.api_key)
            response = client.chat.completions.create(
                model="sonar",
                messages=[{"role": "user", "content": query}],
                temperature=0.3
            )
            
            result = response.choices[0].message.content
            
            # Сохраняем в кэш
            self._add_to_cache(query, result)
            
            return result
            
        except Exception as e:
            error_msg = f"Ошибка при поиске: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            raise SearchError(error_msg)
    
    def _get_from_cache(self, query: str) -> Optional[str]:
        """Получает результат из кэша если он не устарел"""
        if query in self.cache:
            cache_time = self.cache[query]["timestamp"]
            if time.time() - cache_time < self.CACHE_EXPIRATION:
                return self.cache[query]["result"]
        return None
    
    def _add_to_cache(self, query: str, result: str) -> None:
        """Добавляет результат в кэш"""
        self.cache[query] = {
            "result": result,
            "timestamp": time.time()
        }
        # Очищаем старые записи
        self._cleanup_cache()
    
    def _cleanup_cache(self) -> None:
        """Удаляет устаревшие записи из кэша"""
        current_time = time.time()
        expired_queries = [
            query for query, data in self.cache.items()
            if current_time - data["timestamp"] > self.CACHE_EXPIRATION
        ]
        for query in expired_queries:
            del self.cache[query]

class PerplexityAgentCore:
    """Основной класс для обработки запросов через Claude API"""
    
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # секунды
    MAX_HISTORY_LENGTH = 10
    
    # Инструкции для системного промпта
    WORKFLOW_INSTRUCTIONS = """
    1. Анализ запроса пользователя
    2. Эмпатическое слушание
    3. Предложение конкретных техник
    4. Проверка понимания
    """
    
    EXAMPLES = """
    Пользователь: "Я постоянно волнуюсь перед выступлениями"
    Ассистент: "Понимаю, как это тревожно. Давайте разберем, что именно вызывает волнение..."
    
    Пользователь: "Не могу сосредоточиться на работе"
    Ассистент: "Сложно работать, когда внимание рассеивается. Что обычно помогает вам собраться?"
    """
    
    def __init__(self, claude_api_key: str, perplexity_api_key: str):
        if not claude_api_key:
            raise ValidationError("API ключ Claude не может быть пустым")
            
        self.claude_api_key = claude_api_key
        self.logger = logging.getLogger(__name__)
        
        # Инициализация инструментов
        self.tools = {
            "search": PerplexitySearchTool(perplexity_api_key)
        }
        
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
                
            # Добавляем описание доступных инструментов
            tools_description = "\n".join(
                f"- {name}: {tool.description}"
                for name, tool in self.tools.items()
            )
            
            full_prompt = f"""{base_prompt}

            [Доступные инструменты]
            {tools_description}
            
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
        """Обработка пользовательского запроса с ретраями и валидацией"""
        if not user_input.strip():
            raise ValidationError("Пользовательский запрос не может быть пустым")
            
        self.logger.info(f"Получен новый запрос: {user_input[:100]}...")
        
        try:
            # Формируем контекст с историей
            messages = self._prepare_context(user_input)
            
            # Первый вызов модели
            for attempt in range(self.MAX_RETRIES):
                try:
                    initial_response = self._call_llm(messages)
                    break
                except APIError as e:
                    if attempt == self.MAX_RETRIES - 1:
                        raise
                    self.logger.warning(f"Попытка {attempt + 1} не удалась: {str(e)}")
                    time.sleep(self.RETRY_DELAY)
            
            # Проверяем необходимость поиска
            if "ТРЕБУЕТСЯ_ПОИСК:" in initial_response:
                final_response = self._handle_search_request(
                    user_input, initial_response, messages
                )
            else:
                final_response = initial_response
            
            # Обновляем историю
            self._update_history(user_input, final_response)
            
            return self._postprocess_response(final_response)
            
        except Exception as e:
            error_msg = f"Ошибка при обработке запроса: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            raise AIAssistantError(error_msg)
    
    def _prepare_context(self, user_input: str) -> List[Dict[str, str]]:
        """Подготовка контекста с учетом истории"""
        context = self.system_messages.copy()
        
        # Добавляем последние сообщения из истории
        if self.message_history:
            context.extend(self.message_history[-self.MAX_HISTORY_LENGTH:])
            
        context.append({"role": "user", "content": user_input})
        return context
    
    def _handle_search_request(
        self, 
        user_input: str, 
        initial_response: str,
        messages: List[Dict[str, str]]
    ) -> str:
        """Обработка запроса, требующего поиска информации"""
        try:
            search_query = self._extract_search_query(initial_response)
            search_results = self.tools["search"].execute(search_query)
            
            # Обновляем контекст
            messages.extend([
                {"role": "assistant", "content": initial_response},
                {"role": "user", "content": f"Результаты поиска: {search_results}"}
            ])
            
            return self._call_llm(messages)
            
        except Exception as e:
            error_msg = f"Ошибка при обработке поискового запроса: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            raise SearchError(error_msg)
    
    def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        """Вызов Claude с обработкой ошибок"""
        try:
            # Проверяем наличие системного промпта
            has_system_message = any(msg["role"] == "system" for msg in messages)
            if not has_system_message:
                self.logger.warning("Системный промпт отсутствует в сообщениях!")
                messages = self.system_messages + messages
            
            self.logger.info("Отправка запроса к Claude API с %d сообщениями", len(messages))
            self.logger.debug("Первые 200 символов системного промпта: %s", 
                          messages[0]["content"][:200] + "..." if messages else "Нет системного промпта")
            
            # Конвертируем сообщения в формат Claude
            claude_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    claude_messages.append({"role": "system", "content": msg["content"]})
                elif msg["role"] == "user":
                    claude_messages.append({"role": "user", "content": msg["content"]})
                elif msg["role"] == "assistant":
                    claude_messages.append({"role": "assistant", "content": msg["content"]})
            
            response = self.claude_client.messages.create(
                model="claude-3-haiku-20240307",
                messages=claude_messages,
                temperature=0.3,
                max_tokens=1200
            )
            
            result = response.content[0].text
            self.logger.info("Получен ответ длиной %d символов", len(result))
            
            return result
            
        except Exception as e:
            error_msg = f"Ошибка при вызове Claude API: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            raise APIError(error_msg)
    
    def _extract_search_query(self, response: str) -> str:
        """Извлечение поискового запроса с валидацией"""
        try:
            if "ТРЕБУЕТСЯ_ПОИСК:" not in response:
                raise ValidationError("Неверный формат поискового запроса")
                
            query = response.split("ТРЕБУЕТСЯ_ПОИСК:")[1].strip()
            if not query:
                raise ValidationError("Пустой поисковый запрос")
                
            return query
            
        except Exception as e:
            error_msg = f"Ошибка при извлечении поискового запроса: {str(e)}"
            self.logger.error(error_msg)
            raise ValidationError(error_msg)
    
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
