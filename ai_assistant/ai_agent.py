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
        # Заменить вызов Perplexity на общий HTTP-запрос
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": "sonar",
                "messages": [{"role": "user", "content": query}]
            }
        )
        return response.json()["choices"][0]["message"]["content"]
    
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
    [Workflow: Thought-Action-Observation]
    
    1. Thought (Размышление):
       - Анализ запроса пользователя
       - Определение необходимых действий
       - Оценка имеющейся информации
       - Формулировка гипотез
    
    2. Action (Действие):
       - Использование доступных инструментов
       - Поиск дополнительной информации
       - Формирование промежуточных ответов
       - Применение найденных решений
    
    3. Observation (Наблюдение):
       - Анализ результатов действий
       - Оценка полученной информации
       - Формирование финального ответа
       - Планирование следующих шагов
    """
    
    EXAMPLES = """
    [Пример диалога с Thought-Action-Observation]
    
    Пользователь: "Я постоянно волнуюсь перед выступлениями"
    
    Thought: Пользователь испытывает тревогу перед публичными выступлениями. Нужно понять причины тревоги и найти подходящие техники. Возможно, потребуется поиск специфических методик.
    
    Action: Использую поиск для получения информации о современных методах работы с тревогой перед выступлениями.
    ТРЕБУЕТСЯ_ПОИСК: эффективные методы преодоления страха публичных выступлений, современные исследования
    
    Observation: Получена информация о техниках дыхания, визуализации и подготовки. Преобразую в эмпатичный ответ.
    
    Ассистент: "Я слышу, как сильно вас беспокоят эти выступления. Это действительно может быть очень тревожно. Давайте поговорим о том, что именно вызывает наибольшее волнение? Часто, когда мы лучше понимаем свои триггеры, становится легче с ними работать..."
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
        """Обработка пользовательского запроса с использованием workflow thought-action-observation"""
        if not user_input.strip():
            raise ValidationError("Пользовательский запрос не может быть пустым")
            
        self.logger.info(f"Получен новый запрос: {user_input[:100]}...")
        
        try:
            # Формируем контекст с историей
            messages = self._prepare_context(user_input)
            
            # Thought: Первичный анализ запроса
            thought_prompt = f"""
            [Текущий запрос]
            {user_input}
            
            [Инструкция]
            1. Проанализируй запрос пользователя
            2. Определи, достаточно ли информации для ответа
            3. Сформулируй план действий
            4. Укажи, нужен ли поиск дополнительной информации
            
            Формат ответа:
            Thought: [твой анализ ситуации]
            Action: [планируемое действие]
            ТРЕБУЕТСЯ_ПОИСК: [поисковый запрос, если нужен]
            """
            
            messages.append({"role": "user", "content": thought_prompt})
            
            # Получаем размышление модели
            for attempt in range(self.MAX_RETRIES):
                try:
                    thought_response = self._call_llm(messages)
                    break
                except APIError as e:
                    if attempt == self.MAX_RETRIES - 1:
                        raise
                    self.logger.warning(f"Попытка {attempt + 1} не удалась: {str(e)}")
                    time.sleep(self.RETRY_DELAY)
            
            # Action: Выполняем необходимые действия
            if "ТРЕБУЕТСЯ_ПОИСК:" in thought_response:
                search_results = self._handle_search_request(
                    user_input, thought_response, messages
                )
                
                # Observation: Анализируем результаты
                observation_prompt = f"""
                [Результаты поиска]
                {search_results}
                
                [Инструкция]
                Проанализируй результаты поиска и сформируй ответ, следуя workflow:
                
                1. Thought: Проанализируй полученную информацию, выдели ключевые моменты
                
                2. Action: Опиши, как ты используешь найденную информацию
                
                3. Observation: Сформируй финальный ответ для пользователя, следуя правилам:
                   - Используй естественный, разговорный стиль
                   - Проявляй эмпатию и поддержку
                   - Не упоминай источники информации
                   - Избегай формальных списков
                   - Добавь личные наблюдения
                   - Задай уточняющие вопросы
                
                Помни: пользователь не должен видеть этапы Thought и Action, только финальный эмпатичный ответ.
                """
                
                messages.append({"role": "user", "content": observation_prompt})
                final_response = self._call_llm(messages)
            else:
                final_response = thought_response
            
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
        thought_response: str,
        messages: List[Dict[str, str]]
    ) -> str:
        """Обработка запроса, требующего поиска информации"""
        try:
            search_query = self._extract_search_query(thought_response)
            self.logger.info(f"Выполняю поиск: {search_query[:100]}...")
            
            search_results = self.tools["search"].execute(search_query)
            self.logger.info(f"Получены результаты поиска длиной {len(search_results)} символов")
            
            # Формируем специальный промпт для обработки результатов поиска
            observation_prompt = f"""
            [Результаты поиска]
            {search_results}
            
            [Инструкция]
            Проанализируй результаты поиска и сформируй ответ, следуя workflow:
            
            1. Thought: Проанализируй полученную информацию, выдели ключевые моменты
            
            2. Action: Опиши, как ты используешь найденную информацию
            
            3. Observation: Сформируй финальный ответ для пользователя, следуя правилам:
               - Используй естественный, разговорный стиль
               - Проявляй эмпатию и поддержку
               - Не упоминай источники информации
               - Избегай формальных списков
               - Добавь личные наблюдения
               - Задай уточняющие вопросы
            
            Помни: пользователь не должен видеть этапы Thought и Action, только финальный эмпатичный ответ.
            """
            
            # Обновляем контекст
            messages.extend([
                {"role": "assistant", "content": thought_response},
                {"role": "user", "content": observation_prompt}
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
                    # Добавляем специальные инструкции для формата ответа и workflow
                    content = f"""{msg["content"]}
                    
                    [Workflow: Thought-Action-Observation]
                    При обработке каждого запроса следуй этапам:
                    
                    1. Thought (внутренний диалог):
                    - Анализируй запрос пользователя
                    - Определяй необходимые действия
                    - Формулируй гипотезы
                    Формат: "Thought: [твой анализ]"
                    
                    2. Action (действие):
                    - Если нужен поиск: "ТРЕБУЕТСЯ_ПОИСК: [запрос]"
                    - Если не нужен поиск: "Action: [прямой ответ]"
                    
                    3. Observation (анализ):
                    - Анализируй результаты действий
                    - Формируй финальный ответ
                    Формат: "Observation: [анализ результатов]"
                    
                    [Формат ответа для пользователя]
                    1. Используй естественный, разговорный стиль
                    2. Избегай формальных списков и структур
                    3. Общайся от первого лица
                    4. Проявляй эмпатию и поддержку
                    5. Не используй маркеры и нумерацию
                    6. Не упоминай источники информации
                    7. Пиши как если бы это был живой диалог
                    
                    [Пример правильного ответа]
                    Thought: Пользователь испытывает тревогу перед выступлениями. Нужно понять причины и найти методы работы с тревогой.
                    
                    Action: ТРЕБУЕТСЯ_ПОИСК: современные методы работы с тревогой перед публичными выступлениями
                    
                    Observation: Получены данные о техниках дыхания, визуализации и подготовки. Формирую эмпатичный ответ.
                    
                    "Я понимаю, как волнительно выступать перед публикой. Давайте поговорим о том, что именно вызывает наибольшее беспокойство? Я знаю несколько действенных техник, которые могли бы вам помочь..."
                    """
                    claude_messages.append({"role": "system", "content": content})
                else:
                    claude_messages.append({"role": msg["role"], "content": msg["content"]})
            
            response = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20240620",
                messages=claude_messages,
                temperature=0.7,
                max_tokens=1200
            )
            
            result = response.content[0].text
            self.logger.info("Получен ответ длиной %d символов", len(result))
            
            # Обрабатываем внутренний диалог
            if "Thought:" in result and "Action:" in result:
                self.logger.debug("Обнаружен внутренний диалог в ответе")
                # Извлекаем финальный ответ после Observation
                parts = result.split("Observation:")
                if len(parts) > 1:
                    final_response = parts[1].strip()
                    # Убираем кавычки, если они есть
                    final_response = re.sub(r'^"|"$', '', final_response)
                    return final_response
                
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
