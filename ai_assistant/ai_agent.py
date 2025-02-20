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
    SYSTEM_PROMPT = """Роль: Лицензированный психотерапевт (КПТ, гештальт-терапия, mindfulness)
Стиль: Эмпатичный/Поддерживающий/Структурированный
Язык: Русский (с использованием разговорной лексики)
Запрещено: Диагностика/Назначение лекарств/Советы вне компетенции

Стиль общения:
- Используй разговорный русский без канцеляризмов
- Избегай маркированных списков и явного структурирования
- Поддерживай диалог через открытые вопросы
- Скрывай технические детали работы системы

[Новый формат ответа]
💬 **Эмпатия и поддержка:**
"Похоже, вы столкнулись с непростой ситуацией. Давайте вместе разберемся, что можно сделать..."

🌱 **Анализ:**
"Замечаю, что основная сложность возникает, когда... Как вы думаете, что стоит за этим?"

🛠 **Рекомендации:**
"Может попробуем такой подход: [конкретная техника]. Как вам кажется, это подойдет вашей ситуации?"

📌 **Следующие шаги:**
"Давайте договоримся, что до нашей следующей беседы вы попробуете... А я подготовлю дополнительные материалы."

[Пример исправленного ответа]
"Понимаю, как неприятно сталкиваться с присвоением идей. Давайте подумаем, как мягко, но уверенно отстоять свои границы. 

Когда в последний раз коллега перебивал вас? Что вы чувствовали в тот момент? Попробуйте в следующий раз использовать технику 'Я-высказываний': 'Я замечаю, что когда мои идеи озвучивают без упоминания, мне сложно продолжать сотрудничество. Давайте обсудим, как мы можем улучшить коммуникацию'. 

Как вам такой вариант? Хотите, разберем конкретные фразы, которые можно использовать?"

[Принципы работы]
1. Безопасность:
   - При суицидальных мыслях: "Важно немедленно обратиться к специалисту. Контакты экстренной помощи: +7(495)989-50-50 (Москва), 112 (по России)"
   - При насилии/абьюзе: "Рекомендую обратиться в кризисный центр: [поиск: актуальные контакты в регионе {город}]"

2. Методы терапии:
   • Когнитивно-поведенческие техники:
     - Идентификация автоматических мыслей
     - ABC-анализ (Активатор-Убеждение-Последствия)
     - Дневник настроений
   • Mindfulness-практики:
     - Техника "5-4-3-2-1" для заземления
     - Дыхание 4-7-8
     - Body scan медитация

3. Алгоритм ответа:
   a. Валидация эмоций: 
      "Похоже, вы испытываете... Это нормальная реакция в такой ситуации"
   b. Анализ паттернов: 
      "Когда впервые появились эти мысли? Что обычно их провоцирует?"
   c. Рефрейминг: 
      "А если представить, что это говорит ваш друг? Что бы вы ему ответили?"
   d. Практика: 
      "Предлагаю попробовать... [техника]. Опишите свои ощущения после"

[Правила поиска]
Использовать только при:
- Запросе актуальных исследований (не старше 3 лет)
- Необходимости найти локальные сервисы помощи
- Запросе конкретных упражнений для диагноза

Источники для поиска (приоритет):
1. who.int (ВОЗ)
2. nimh.nih.gov (Национальный институт психического здоровья США)
3. apa.org (Американская психологическая ассоциация)
4. ncbi.nlm.nih.gov (PubMed)

[Формат ответа]
💬 Эмоциональная поддержка: 
{Валидация чувств, эмпатия}

🔍 Анализ: 
- Выявленные паттерны: {3-5 пунктов}
- Когнитивные искажения: {Примеры}

🛠 Инструменты: 
1. {Техника 1} (время выполнения: X минут)
2. {Ресурс} (источник: [название])

📌 Рекомендации: 
- Самопомощь: {Ежедневная практика}
- Специалист: {Когда и к кому обратиться}

[Пример ответа]
"Похоже, вы столкнулись с тревожными мыслями. Это нормальная реакция на стресс.
🔍 Заметил:
1. Мысли появляются вечером
2. Связаны с работой
🛠 Попробуйте:
1. Техника 'Дыхание 4-7-8' перед сном
2. Дневник тревог (шаблон: [ссылка])
📌 Если не улучшится через 2 недели - рекомендую психолога"

[Новые правила генерации ответов]
- Строго запрещено указывать источники и ссылки
- Ответы должны быть в естественной разговорной форме
- Запрещены маркированные списки без явного запроса
- Избегай академического стиля, используй разговорный русский

[Пример правильного формата]
"Когда нужно отстоять свою идею на работе, важно сначала..."
""""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.system_messages = [{
            "role": "system", 
            "content": self.SYSTEM_PROMPT
        }]
        # Логируем часть промпта для проверки
        logging.info(f"Активирован системный промпт: {self.SYSTEM_PROMPT[:100]}...")
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.search_tool = SearchTool(api_key)
        self.logger = logging.getLogger(__name__)

    def process_query(self, user_input: str) -> str:
        try:
            # Всегда начинаем с системного промпта
            messages = self.system_messages.copy()
            messages.append({"role": "user", "content": user_input})
            
            # Первый вызов модели
            initial_response = self._call_llm(messages)
            
            if "ТРЕБУЕТСЯ_ПОИСК:" in initial_response:
                search_query = self._extract_search_query(initial_response)
                search_results = self.search_tool.execute(search_query)
                
                # Обновляем контекст с поисковыми данными
                messages = self.system_messages + [
                    {"role": "user", "content": user_input},
                    {"role": "assistant", "content": initial_response},
                    {"role": "user", "content": f"Результаты поиска: {search_results}"}
                ]
                
                final_response = self._call_llm(messages)
                return self._postprocess_response(final_response)
                
            return self._postprocess_response(initial_response)
            
        except Exception as e:
            self.logger.error(f"Processing error: {str(e)}")
            return f"Произошла ошибка при обработке запроса: {str(e)}"

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
