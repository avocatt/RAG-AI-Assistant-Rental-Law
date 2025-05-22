# TBK Tenancy Law Assistant

An AI assistant that answers your questions about the Housing and Roofed Workplace Rentals section of the Turkish Code of Obligations (TBK).

This application provides a user interface to interact with an AI model knowledgeable about specific aspects of Turkish tenancy law.

## Setup

1.  **Install required packages:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Create a `.env` file** in the project root and define the necessary environment variables:
    ```env
    OPENAI_API_KEY="your_openai_api_key_here"
    DEMO_PASSWORD="your_secret_demo_password_here"
    ```
    *   `OPENAI_API_KEY`: Your API key for OpenAI services.
    *   `DEMO_PASSWORD`: A password to protect access to the demo frontend.

3.  **Create the vector database:**
    This step processes your source documents (presumably related to TBK tenancy law) and stores them in a format suitable for efficient retrieval by the AI.
    ```bash
    python ingest_data.py
    ```

## Running the Application

1.  **Start the backend server:**
    The backend handles the AI logic and API interactions.
    ```bash
    uvicorn main:app --reload
    ```
    The `--reload` flag enables auto-reloading when code changes, useful for development.

2.  **Start the frontend application:**
    Open a new terminal window and run:
    ```bash
    streamlit run app_ui.py
    ```

3.  **Access the application:**
    Open your web browser and navigate to `http://localhost:8501`. You will be prompted for the `DEMO_PASSWORD` you set in your `.env` file.

### Live Demo

You can access a live demo of the application here: [TBK Tenancy Law Assistant Demo](https://rag-ai-assistant-rental-law.streamlit.app/)

## Demo Security

The application implements two layers of security for this demo setup:

1.  **Frontend Password Protection:** Access to the Streamlit frontend is protected by the `DEMO_PASSWORD` defined in the `.env` file.
2.  **Secure API Key Management:** The OpenAI API key is managed securely on the backend and is not exposed to the frontend.

## Deployment Notes

When deploying this application to a production or shared environment:

1.  **Separate Services:** The frontend (Streamlit) and backend (FastAPI/Uvicorn) should be deployed as separate services.
2.  **Environment Variables:** For both services, use your deployment platform's environment variable or secrets management system instead of a `.env` file.
3.  **Update Backend URL:** Modify the `FASTAPI_URL` variable within `app_ui.py` to point to the deployed backend's URL.
4.  **Additional Security:** Implement platform-level security measures such as IP restrictions, firewalls, or authentication/authorization layers for secure access.

## Disclaimer

This application is for educational and demonstrative purposes only. It does not constitute legal advice. Always consult with a qualified legal professional for any legal matters.

---

# TBK Kira Hukuku Asistanı

Türk Borçlar Kanunu'nun Konut ve Çatılı İşyeri Kiraları bölümü hakkında sorularınızı yanıtlayan bir AI asistanı.

## Kurulum

1.  Gerekli paketleri kurun:
    ```bash
    pip install -r requirements.txt
    ```

2.  `.env` dosyası oluşturun ve gerekli değişkenleri tanımlayın:
    ```env
    OPENAI_API_KEY="your_openai_api_key_here"
    DEMO_PASSWORD="your_secret_demo_password_here"
    ```

3.  Vektör veritabanını oluşturun:
    ```bash
    python ingest_data.py
    ```

## Çalıştırma

1.  Backend'i başlatın:
    ```bash
    uvicorn main:app --reload
    ```

2.  Yeni bir terminal açın ve frontend'i başlatın:
    ```bash
    streamlit run app_ui.py
    ```

3.  Tarayıcınızda `http://localhost:8501` adresine giderek uygulamayı kullanabilirsiniz.

### Canlı Demo

Uygulamanın canlı demosuna buradan erişebilirsiniz: [TBK Kira Hukuku Asistanı Demo](https://rag-ai-assistant-rental-law.streamlit.app/)

## Demo Güvenliği

Uygulama, iki güvenlik katmanı kullanır:

1.  Frontend'e erişim için şifre koruması (`.env` dosyasındaki `DEMO_PASSWORD` değeri)
2.  Backend'de OpenAI API anahtarının güvenli bir şekilde yönetimi

## Dağıtım (Deployment) Notları

Uygulamayı dağıtırken:

1.  Frontend ve backend ayrı servislerde dağıtılmalıdır
2.  Her iki servis için de `.env` dosyası yerine platformun çevre değişkenleri/secrets yönetimini kullanın
3.  `app_ui.py` içindeki `FASTAPI_URL` değişkenini backend'in yeni URL'si ile güncelleyin
4.  Güvenli erişim için platform düzeyinde IP kısıtlamaları veya benzeri ek güvenlik önlemlerini etkinleştirin

## Lisans / Yasal Uyarı

Bu uygulama sadece eğitim amaçlıdır ve hukuki tavsiye içermez. Herhangi bir hukuki konuda daima nitelikli bir hukuk uzmanına danışın.