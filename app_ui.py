import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()  # Load environment variables from .env file
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://127.0.0.1:8000/query")  # URL of your FastAPI backend
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD")
API_SECRET_KEY = os.getenv("API_SECRET_KEY")

# --- Password Protection Logic ---


def check_password():
    """Returns `True` if the user has entered the correct password."""
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if not DEMO_PASSWORD:  # Check if DEMO_PASSWORD is set at all
        st.error(
            "Uygulama şifresi yapılandırılmamış. Lütfen sistem yöneticisi ile iletişime geçin.")
        return False
    
    if not API_SECRET_KEY:  # Check if API_SECRET_KEY is set
        st.error(
            "API güvenlik anahtarı yapılandırılmamış. Lütfen sistem yöneticisi ile iletişime geçin.")
        return False

    if st.session_state.password_correct:
        return True

    # Show input for password
    password_placeholder = st.empty()
    password = password_placeholder.text_input(
        "Lütfen demo şifresini girin:", type="password")

    if not password:  # Don't proceed if password field is empty
        return False

    if password == DEMO_PASSWORD:
        st.session_state.password_correct = True
        password_placeholder.empty()  # Clear the password input
        st.rerun()  # Rerun to show the main app
        return True
    elif password:  # if password entered but incorrect
        st.error("Girilen şifre yanlış.")
        st.session_state.password_correct = False
        return False
    return False


# --- Streamlit App UI ---
st.set_page_config(page_title="TBK Kira Hukuku Asistanı", layout="wide")

if not check_password():
    st.stop()  # Do not render the rest of the app if password is not correct

# If password is correct, the rest of the app will render below:
st.title("⚖️ Türk Borçlar Kanunu - Kira Hukuku Asistanı")
st.caption("Konut ve Çatılı İşyeri Kiraları maddeleri hakkında sorularınızı sorun.")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message and message["sources"]:
            with st.expander("Bilgi Alınan Kaynaklar", expanded=False):
                for i, source in enumerate(message["sources"]):
                    st.markdown(f"""
                    **Kaynak {i+1}: {source['metadata'].get('article_number', 'Bilinmeyen Madde')} - {source['metadata'].get('article_header', 'Başlık Yok')}**
                    ```
                    {source['document'][:500]}... 
                    ```
                    """)  # Show a preview of the source

# React to user input
if user_query := st.chat_input("Sorunuzu buraya yazın..."):
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(user_query)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_query})

    # Call FastAPI backend
    try:
        payload = {"query_text": user_query}
        headers = {
            "X-API-Key": API_SECRET_KEY,
            "Content-Type": "application/json"
        }
        # Increased timeout for LLM
        response = requests.post(FASTAPI_URL, json=payload, headers=headers, timeout=120)
        response.raise_for_status()  # Raise an exception for HTTP errors

        response_data = response.json()
        answer = response_data.get(
            "answer", "Bir hata oluştu, cevap alınamadı.")
        retrieved_sources = response_data.get("retrieved_sources", [])

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            st.markdown(answer)
            if retrieved_sources:
                with st.expander("Yanıt Oluşturulurken Kullanılan Kaynaklar", expanded=False):
                    for i, source in enumerate(retrieved_sources):
                        st.markdown(f"""
                        **Kaynak {i+1}: {source['metadata'].get('article_number', 'Bilinmeyen Madde')} - {source['metadata'].get('article_header', 'Başlık Yok')}**
                        <details>
                            <summary>Metni Göster</summary>
                            <div style="white-space: pre-wrap; font-family: monospace; background-color: #f0f0f0; padding: 10px; border-radius: 5px; max-height: 200px; overflow-y: auto;">{source['document']}</div>
                        </details>
                        <hr style="margin: 5px 0;">
                        """, unsafe_allow_html=True)

        # Add assistant response to chat history
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "sources": retrieved_sources  # Store sources with the message
        })

    except requests.exceptions.RequestException as e:
        error_message = f"API'ye bağlanırken bir hata oluştu: {e}"
        st.error(error_message)
        st.session_state.messages.append(
            {"role": "assistant", "content": error_message, "sources": []})
    except Exception as e:
        error_message = f"Beklenmedik bir hata oluştu: {e}"
        st.error(error_message)
        st.session_state.messages.append(
            {"role": "assistant", "content": error_message, "sources": []})

# Add a button to clear chat history
if st.sidebar.button("Sohbet Geçmişini Temizle"):
    st.session_state.messages = []
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown(
    "Bu uygulama, Türk Borçlar Kanunu'nun Konut ve Çatılı İşyeri Kiraları bölümü hakkında bilgi vermek amacıyla geliştirilmiştir.")
st.sidebar.markdown("Sağlanan bilgiler hukuki tavsiye niteliğinde değildir.")
