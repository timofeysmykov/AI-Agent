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
    TRUSTED_SOURCES = ["who.int", "nimh.nih.gov", "apa.org", "mayoclinic.org"]
    
    def __init__(self, api_key: str):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.perplexity.ai"
        )
    
    def execute(self, query: str) -> str:
        """Поиск через Perplexity API с фильтрацией источников"""
        try:
            response = self.client.chat.completions.create(
                model="sonar-pro-online",
                messages=[{
                    "role": "user",
                    "content": f"Поиск: {query}\nФильтры: сайты {', '.join(self.TRUSTED_SOURCES)}, данные за 2021-2024 гг."
                }],
                temperature=0.1,
                max_tokens=1024
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Ошибка поиска: {str(e)}")
            return "Не удалось получить актуальные данные"

class PerplexityAgentCore:
    """Центральный 'мозг' агента на базе Perplexity API"""
    THERAPY_METHODS = {
        "anxiety": "Техника дыхания 4-7-8...",
        "depression": "Дневник настроений..."
    }

    CRISIS_RESPONSE = """⚠️ Кризисная ситуация! 
    Немедленно свяжитесь со специалистом: +7(495)989-50-50 (Москва), 112 (по России)"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.search_tool = SearchTool(api_key=api_key)
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
    
    def process_query(self, user_input: str) -> str:
        if self._is_crisis_situation(user_input):
            return self.CRISIS_RESPONSE
        
        messages = self._create_system_prompt()
        messages.append({"role": "user", "content": user_input})
        
        try:
            initial_response = self._call_llm(messages)
            if "ТРЕБУЕТСЯ_ПОИСК" in initial_response:
                search_query = initial_response.split("ТРЕБУЕТСЯ_ПОИСК:")[1].strip()
                search_results = self.search_tool.execute(search_query)
                messages.append({
                    "role": "assistant", 
                    "content": f"Результаты поиска: {search_results}"
                })
                return self._call_llm(messages)
            return initial_response
        except Exception as e:
            self.logger.error(f"Ошибка: {str(e)}")
            return "Произошла внутренняя ошибка. Пожалуйста, попробуйте позже."

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
            # Вызов API с актуальными параметрами
            response = self.client.chat.completions.create(
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

    def _is_crisis_situation(self, text: str) -> bool:
        triggers = {"суицид", "умру", "убью себя", "не хочу жить", "насилие", "абьюз"}
        return any(trigger in text.lower() for trigger in triggers)
