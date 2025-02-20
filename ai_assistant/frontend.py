import streamlit as st
import time
from ai_assistant.ai_agent import PerplexityAgentCore
import os
from dotenv import load_dotenv

# Настройка стилей
def set_custom_style():
    st.markdown("""
    <style>
        .stChatInput { 
            position: fixed; 
            bottom: 20px; 
            width: 70%; 
        }
        .stApp { 
            max-width: 1200px; 
            margin: 0 auto; 
        }
        .message-user {
            padding: 15px;
            border-radius: 20px 20px 3px 20px;
            background: #2b313e;
            margin: 5px;
            color: white;
            max-width: 80%;
            float: right;
        }
        .message-assistant {
            padding: 15px;
            border-radius: 20px 20px 20px 3px;
            background: #1a1c24;
            margin: 5px;
            color: white;
            max-width: 80%;
            float: left;
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
        @keyframes blink {
            0% {opacity: 1;}
            50% {opacity: 0;}
            100% {opacity: 1;}
        }
        .typing-cursor {
            animation: blink 1s infinite;
            color: #666;
        }
    </style>
    """, unsafe_allow_html=True)

def main():
    set_custom_style()
    load_dotenv()
    
    # Инициализация агента
    if "agent" not in st.session_state:
        st.session_state.agent = PerplexityAgentCore(
            api_key=os.getenv("PERPLEXITY_API_KEY")
        )

    # Заголовок
    st.title("🦉 AI Agent")
    st.caption("Ваш персональный психотерапевт)")

    # История чата
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Чем могу помочь?"}
        ]

    # Отображение истории сообщений
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(f'<div class="message-{message["role"]}">{message["content"]}</div>', 
                       unsafe_allow_html=True)

    # Обработка ввода пользователя
    if prompt := st.chat_input("Напишите ваше сообщение..."):
        # Добавляем сообщение пользователя
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(f'<div class="message-user">{prompt}</div>', 
                       unsafe_allow_html=True)

        # Генерируем ответ
        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""
            
            # Индикатор загрузки
            with placeholder.container():
                st.markdown('<div class="loading-dots">Обработка</div>', 
                           unsafe_allow_html=True)
            
            # Получаем ответ от агента
            try:
                full_response = st.session_state.agent.process_query(prompt)
            except Exception as e:
                full_response = f"⚠️ Ошибка: {str(e)}"
            
            # Заменяем индикатор загрузки на ответ
            placeholder.empty()
            current_message = ""
            typing_cursor = '<span class="typing-cursor">|</span>'
            
            # Добавляем CSS-анимацию курсора
            st.markdown("""
            <style>
                @keyframes blink {
                    0% {opacity: 1;}
                    50% {opacity: 0;}
                    100% {opacity: 1;}
                }
                .typing-cursor {
                    animation: blink 1s infinite;
                    color: #666;
                }
            </style>
            """, unsafe_allow_html=True)

            for char in full_response:
                current_message += char
                # Случайная задержка для естественности
                delay = 0.02 if char in ",.!? " else 0.03
                placeholder.markdown(
                    f'<div class="message-assistant">'
                    f'{current_message.replace("\n", "<br>")}'
                    f'{typing_cursor}</div>', 
                    unsafe_allow_html=True
                )
                time.sleep(delay)

            # Убираем курсор после завершения
            placeholder.markdown(
                f'<div class="message-assistant">{full_response}</div>', 
                unsafe_allow_html=True
            )
        
        st.session_state.messages.append({"role": "assistant", "content": full_response})

if __name__ == "__main__":
    main()
