import os
import logging
from typing import Dict, List, Optional
import httpx
from .base_tool import BaseTool

logger = logging.getLogger(__name__)

class PerplexitySearchTool(BaseTool):
    """Инструмент для поиска информации через Perplexity API"""
    
    def __init__(self, api_key: str):
        super().__init__(
            name="perplexity_search",
            description="Поиск актуальной информации через Perplexity API"
        )
        self.api_key = api_key
        self.base_url = "https://api.perplexity.ai"
    
    async def search(self, query: str) -> Dict:
        """
        Выполняет поиск информации через Perplexity API
        
        Args:
            query (str): Поисковый запрос
            
        Returns:
            Dict: Результаты поиска
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "pplx-7b-online",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a professional search assistant focused on finding the most recent and accurate information."
                            },
                            {
                                "role": "user",
                                "content": query
                            }
                        ],
                        "max_tokens": 2048,
                        "temperature": 0.3
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                self.logger.info(f"Успешно получен ответ от Perplexity API для запроса: {query[:100]}...")
                return result
                
        except Exception as e:
            error_msg = f"Ошибка при поиске через Perplexity API: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
    
    def format_search_results(self, results: Dict) -> str:
        """
        Форматирует результаты поиска в читаемый вид
        
        Args:
            results (Dict): Результаты поиска от API
            
        Returns:
            str: Отформатированный текст с результатами
        """
        try:
            content = results["choices"][0]["message"]["content"]
            
            # Форматируем ответ
            formatted = f"""
            [Результаты поиска]
            {content}
            """
            
            return formatted.strip()
            
        except Exception as e:
            error_msg = f"Ошибка при форматировании результатов поиска: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
    
    async def execute(self, query: str) -> str:
        """
        Выполняет поиск и возвращает отформатированные результаты
        
        Args:
            query (str): Поисковый запрос
            
        Returns:
            str: Отформатированные результаты поиска
        """
        try:
            results = await self.search(query)
            return self.format_search_results(results)
            
        except Exception as e:
            error_msg = f"Ошибка при выполнении поиска: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg) 