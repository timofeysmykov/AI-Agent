import requests
import json
import logging
from typing import Dict, Any, Optional
#from duckduckgo_search import DDGS
import os
from pathlib import Path
from openai import OpenAI

# Добавляем константу после импортов
SYSTEM_PROMPT_PATH = Path(__file__).parent / "prompts" / "system_instruction.txt"

# class SearchTool:
#     """Инструмент для поиска информации через DuckDuckGo"""
#     def __init__(self):
#         self.client = DDGS()
#         self.logger = logging.getLogger(__name__)
    
#     def execute(self, query: str) -> str:
#         """Выполняет поиск и возвращает форматированные результаты"""
#         try:
#             results = [r for r in self.client.text(query, max_results=20)]
#             return self._format_results(results)
#         except Exception as e:
#             self.logger.error(f"Search error: {e}")
#             return "Не удалось получить результаты поиска"

#     def _format_results(self, results: list) -> str:
#         """Форматирует результаты поиска"""
#         return "\n".join([f"🔍 Результат {i+1}: {r['title']}\nURL: {r['href']}\n{r['body']}\n" 
#                         for i, r in enumerate(results)])

class SearchTool:
    """Заглушка для поискового инструмента (Perplexity имеет встроенный поиск)"""
    def execute(self, query: str) -> str:
        return "Perplexity автоматически использует актуальные данные из сети"

class PerplexityAgentCore:
    """Центральный 'мозг' агента на базе Perplexity API"""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.search_tool = SearchTool()
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
    
    def process_query(self, user_input: str) -> str:
        """Основной цикл обработки запроса"""
        try:
            # Создаем список сообщений
            messages = self._create_system_prompt()
            
            # Добавляем сообщение пользователя
            messages.append({"role": "user", "content": user_input})
            
            # Получаем ответ от модели
            initial_response = self._call_llm(messages=messages)
            
            # Проверяем необходимость поиска
            if "ТРЕБУЕТСЯ_ПОИСК" in initial_response:
                search_query = self._extract_search_query(initial_response)
                # Добавляем поисковый запрос к сообщениям
                messages.append({"role": "assistant", "content": initial_response})
                messages.append({"role": "user", "content": f"Поисковый запрос: {search_query}"})
                return self._call_llm(messages=messages)
            
            return initial_response
            
        except Exception as e:
            self.logger.error(f"Processing error: {str(e)}")
            return f"Произошла ошибка при обработке запроса: {str(e)}"

    def _create_system_prompt(self) -> list:
        """Загружает системный промпт из файла"""
        try:
            with open(SYSTEM_PROMPT_PATH, 'r', encoding='utf-8') as f:
                prompt_content = f.read().strip()
            
            return [{
                "role": "system",
                "content": prompt_content
            }]
        
        except Exception as e:
            self.logger.error(f"Ошибка загрузки промпта: {e}")
            return [{
                "role": "system",
                "content": "Вы - интеллектуальный ассистент с доступом к интернету. Отвечайте точно и обоснованно."
            }]

    def _call_llm(self, messages: list) -> str:
        """Вызов API Perplexity через официальный клиент"""
        try:
            # Инициализация клиента с правильным base_url
            client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.perplexity.ai"
            )
            
            # Вызов API с актуальными параметрами
            response = client.chat.completions.create(
                model="sonar-pro",  # Или "sonar-7b"
                messages=messages,
                temperature=0.7,
                max_tokens=1024
            )
            
            # Получение текста ответа
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"API error: {str(e)}")
            raise RuntimeError(f"Ошибка API: {str(e)}")

    def _extract_search_query(self, response: str) -> str:
        """Извлекает поисковый запрос из ответа LLM"""
        return response.split("ТРЕБУЕТСЯ_ПОИСК:")[1].strip()

    def _generate_final_response(self, query: str, context: str) -> str:
        """Генерирует финальный ответ с использованием контекста"""
        return self._call_llm(
            messages=self._create_system_prompt() + [
                {"role": "user", "content": query},
                {"role": "assistant", "content": f"Контекст поиска:\n{context}"}
            ]
        )
