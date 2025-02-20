import streamlit as st
import time
from ai_assistant.ai_agent import PerplexityAgentCore, AIAssistantError
import os
from dotenv import load_dotenv
import logging
from typing import Optional
import traceback

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('frontend.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Константы
MAX_RETRIES = 3
RETRY_DELAY = 1
ERROR_MESSAGES = {
    "claude_api_key_missing": "⚠️ API ключ Claude не найден. Пожалуйста, проверьте файл .env",
    "perplexity_api_key_missing": "⚠️ API ключ Perplexity не найден. Пожалуйста, проверьте файл .env",
    "general_error": "⚠️ Произошла ошибка: {}",
    "rate_limit": "⚠️ Превышен лимит запросов. Пожалуйста, подождите немного.",
    "network_error": "⚠️ Проблема с сетевым подключением. Попробуйте позже.",
}

# Настройка стилей
def set_custom_style():
    st.markdown("""
    <style>
        .stChatInput { 
            position: fixed; 
            bottom: 20px; 
            width: 70%; 
            border-radius: 20px;
            border: 2px solid #2b313e;
        }
        .stApp { 
            max-width: 1200px; 
            margin: 0 auto;
            background: #1a1c24;
        }
        .message-user {
            padding: 15px;
            border-radius: 20px 20px 3px 20px;
            background: #2b313e;
            margin: 5px;
            color: white;
            max-width: 80%;
            float: right;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        .message-assistant {
            padding: 15px;
            border-radius: 20px 20px 20px 3px;
            background: #1a1c24;
            margin: 5px;
            color: white;
            max-width: 80%;
            float: left;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        .loading-dots::after {
            content: '.';
            animation: dots 1s steps(5, end) infinite;
        }
        @keyframes dots {
            0%, 20% { 
                color: rgba(0,0,0,0); 
                text-shadow: .25em 0 0 rgba(0,0,0,0), .5em 0 0 rgba(0,0,0,0);
            }
            40% { 
                color: white; 
                text-shadow: .25em 0 0 rgba(0,0,0,0), .5em 0 0 rgba(0,0,0,0);
            }
            60% { 
                text-shadow: .25em 0 0 white, .5em 0 0 rgba(0,0,0,0);
            }
            80%, 100% { 
                text-shadow: .25em 0 0 white, .5em 0 0 white;
            }
        }
        .typing-cursor {
            animation: blink 1s infinite;
            color: #666;
        }
        .error-message {
            color: #ff4b4b;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            background: rgba(255,75,75,0.1);
        }
        .success-message {
            color: #00ff00;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            background: rgba(0,255,0,0.1);
        }
    </style>
    """, unsafe_allow_html=True)

def initialize_agent() -> Optional[PerplexityAgentCore]:
    """Инициализация агента с обработкой ошибок"""
    try:
        claude_api_key = os.getenv("CLAUDE_API_KEY")
        perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
        
        if not claude_api_key:
            st.error(ERROR_MESSAGES["claude_api_key_missing"])
            return None
            
        if not perplexity_api_key:
            st.error(ERROR_MESSAGES["perplexity_api_key_missing"])
            return None
            
        return PerplexityAgentCore(
            claude_api_key=claude_api_key,
            perplexity_api_key=perplexity_api_key
        )
        
    except Exception as e:
        logger.error(f"Ошибка инициализации агента: {str(e)}")
        logger.error(traceback.format_exc())
        st.error(ERROR_MESSAGES["general_error"].format(str(e)))
        return None

def display_message(role: str, content: str):
    """Отображение сообщения с анимацией"""
    with st.chat_message(role):
        st.markdown(
            f'<div class="message-{role}">{content}</div>', 
            unsafe_allow_html=True
        )

def process_user_input(agent: PerplexityAgentCore, prompt: str) -> Optional[str]:
    """Обработка пользовательского ввода с ретраями"""
    for attempt in range(MAX_RETRIES):
        try:
            return agent.process_query(prompt)
        except Exception as e:
            if "rate limit" in str(e).lower():
                if attempt == MAX_RETRIES - 1:
                    st.error(ERROR_MESSAGES["rate_limit"])
                    return None
                time.sleep(RETRY_DELAY * (attempt + 1))
            elif "network" in str(e).lower():
                st.error(ERROR_MESSAGES["network_error"])
                return None
            else:
                logger.error(f"Ошибка обработки запроса: {str(e)}")
                logger.error(traceback.format_exc())
                st.error(ERROR_MESSAGES["general_error"].format(str(e)))
                return None

def animate_response(placeholder, response: str):
    """Анимация печати ответа"""
    current_message = ""
    typing_cursor = '<span class="typing-cursor">|</span>'
    
    for char in response:
        current_message += char
        delay = 0.02 if char in ",.!? " else 0.03
        placeholder.markdown(
            f'<div class="message-assistant">'
            f'{current_message.replace("\n", "<br>")}'
            f'{typing_cursor}</div>', 
            unsafe_allow_html=True
        )
        time.sleep(delay)
    
    placeholder.markdown(
        f'<div class="message-assistant">{response}</div>', 
        unsafe_allow_html=True
    )

def main():
    """Основная функция приложения"""
    try:
        set_custom_style()
        load_dotenv()
        
        st.title("🦉 AI Assistant")
        st.caption("Ваш персональный помощник")
        
        # Инициализация состояния
        if "agent" not in st.session_state:
            st.session_state.agent = initialize_agent()
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {"role": "assistant", "content": "Чем могу помочь?"}
            ]
        
        # Проверка инициализации агента
        if not st.session_state.agent:
            st.error("Не удалось инициализировать ассистента")
            return
        
        # Отображение истории сообщений
        for message in st.session_state.messages:
            display_message(message["role"], message["content"])
        
        # Обработка ввода пользователя
        if prompt := st.chat_input("Напишите ваше сообщение..."):
            # Добавляем и отображаем сообщение пользователя
            st.session_state.messages.append({"role": "user", "content": prompt})
            display_message("user", prompt)
            
            # Генерируем ответ
            with st.chat_message("assistant"):
                placeholder = st.empty()
                
                # Индикатор загрузки
                with placeholder.container():
                    st.markdown(
                        '<div class="loading-dots">Обработка</div>', 
                        unsafe_allow_html=True
                    )
                
                # Получаем и анимируем ответ
                response = process_user_input(st.session_state.agent, prompt)
                if response:
                    placeholder.empty()
                    animate_response(placeholder, response)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": response}
                    )
                    
    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}")
        logger.error(traceback.format_exc())
        st.error(ERROR_MESSAGES["general_error"].format(str(e)))

if __name__ == "__main__":
    main()
