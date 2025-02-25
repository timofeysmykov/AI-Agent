import os
import asyncio
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from .ai_agent import ClaudeAgentCore

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация Flask-приложения
app = Flask(__name__)
CORS(app)  # Разрешаем Cross-Origin запросы

@app.route('/api/chat', methods=['POST'])
def chat_endpoint():
    try:
        logger.info("Получен запрос к /api/chat")
        
        # Инициализация Claude Agent внутри эндпоинта
        claude_api_key = os.getenv('CLAUDE_API_KEY')
        perplexity_api_key = os.getenv('PERPLEXITY_API_KEY')
        
        logger.info(f"API ключи: Claude - {'Установлен' if claude_api_key else 'Отсутствует'}, Perplexity - {'Установлен' if perplexity_api_key else 'Отсутствует'}")

        data = request.json
        logger.info(f"Получены данные: {data}")
        
        message = data.get('message')
        
        if not message:
            logger.warning("Получен пустой запрос")
            return jsonify({"error": "Сообщение не может быть пустым"}), 400
        
        logger.info(f"Обрабатываем сообщение: {message[:50]}...")
        
        # Инициализация агента
        agent = ClaudeAgentCore(
            claude_api_key=claude_api_key, 
            perplexity_api_key=perplexity_api_key
        )
        
        # Синхронный запуск асинхронной функции
        result = asyncio.run(agent.process_query(message))
        
        logger.info(f"Получен ответ длиной {len(result)} символов")
        
        timestamp = os.getenv('TIMESTAMP', '')
        
        return jsonify({
            "response": result,
            "timestamp": timestamp
        })
    
    except Exception as e:
        logger.error(f"Ошибка в обработке запроса: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

def run_server(host='0.0.0.0', port=5000):
    app.run(host=host, port=port, debug=True)

if __name__ == '__main__':
    run_server() 