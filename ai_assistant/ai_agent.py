import requests
import json
import logging
from typing import Dict, Any, Optional
#from duckduckgo_search import DDGS
import os
from pathlib import Path
from perplexity import Perplexity
import re
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
    TRUSTED_SOURCES = ["who.int", "nimh.nih.gov", "apa.org", "mayoclinic.org"]
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def execute(self, query: str) -> str:
        client = Perplexity(api_key=self.api_key)
        response = client.chat.completions.create(
            model="sonar",  # Единая модель для всего
            messages=[{"role": "user", "content": query}]
        )
        return response.choices[0].message.content

class PerplexityAgentCore:
    """Центральный 'мозг' агента на базе Perplexity API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.search_tool = SearchTool(api_key)
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.system_prompt = self._load_system_prompt()  # Новая переменная

    def process_query(self, user_input: str) -> str:
        """Основной цикл обработки запроса"""
        try:
            messages = self.system_prompt.copy()  # Используем сохраненный промпт
            messages.append({"role": "user", "content": user_input})
            
            initial_response = self._call_llm(messages=messages)
            
            if "ТРЕБУЕТСЯ_ПОИСК" in initial_response:
                search_query = self._extract_search_query(initial_response)
                search_results = self.search_tool.execute(search_query)
                
                messages = self.system_prompt + [
                    {"role": "user", "content": user_input},
                    {"role": "assistant", "content": initial_response},
                    {"role": "user", "content": f"Результаты: {search_results}"}
                ]
                
                return self._call_llm(messages=messages)
            
            return initial_response
            
        except Exception as e:
            self.logger.error(f"Processing error: {str(e)}")
            return f"Произошла ошибка при обработке запроса: {str(e)}"

    def _load_system_prompt(self) -> list:
        """Загружает промпт один раз при инициализации"""
        try:
            with open(SYSTEM_PROMPT_PATH, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                return [{"role": "system", "content": content}]
        except Exception as e:
            self.logger.error(f"Ошибка загрузки промпта: {e}")
            return [{"role": "system", "content": "Базовый промпт..."}]

    def _call_llm(self, messages: list) -> str:
        """Вызов API Perplexity через официальный клиент"""
        try:
            client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.perplexity.ai"
            )
            
            response = client.chat.completions.create(
                model="sonar",
                messages=messages,
                temperature=0.7,
                max_tokens=800,
                presence_penalty=0.5
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"API error: {str(e)}")
            raise RuntimeError(f"Ошибка API: {str(e)}")

    def _extract_search_query(self, response: str) -> str:
        """Извлекает поисковый запрос из ответа LLM"""
        if "ТРЕБУЕТСЯ_ПОИСК:" not in response:
            raise ValueError("Неверный формат поискового запроса")
        return response.split("ТРЕБУЕТСЯ_ПОИСК:")[1].strip()

    def _postprocess_response(self, raw_response: str) -> str:
        """Очистка ответа от технических артефактов"""
        # Удаление всех технических артефактов
        cleaned = re.sub(r'(?:\[.*?\]|\(.*?\)|\{.*?\})', '', raw_response)
        cleaned = re.sub(r'[🔍📌🛠🌱💬]', '', cleaned)
        cleaned = re.sub(r'\d+\.\s', '\n- ', cleaned)  # Единый стиль списков
        return '\n'.join([p.strip() for p in cleaned.split('\n') if p.strip() and not p.startswith('Источник')])
