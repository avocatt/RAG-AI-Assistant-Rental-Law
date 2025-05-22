# TBK Kira Hukuku Asistanı

Türk Borçlar Kanunu'nun Konut ve Çatılı İşyeri Kiraları bölümü hakkında sorularınızı yanıtlayan bir AI asistanı.

## Kurulum

1. Gerekli paketleri kurun:
   ```
   pip install -r requirements.txt
   ```

2. `.env` dosyası oluşturun ve gerekli değişkenleri tanımlayın:
   ```
   OPENAI_API_KEY="your_openai_api_key_here"
   DEMO_PASSWORD="your_secret_demo_password_here"
   ```

3. Vektör veritabanını oluşturun:
   ```
   python ingest_data.py
   ```

## Çalıştırma

1. Backend'i başlatın:
   ```
   uvicorn main:app --reload
   ```

2. Yeni bir terminal açın ve frontend'i başlatın:
   ```
   streamlit run app_ui.py
   ```

3. Tarayıcınızda `http://localhost:8501` adresine giderek uygulamayı kullanabilirsiniz.

## Demo Güvenliği

Uygulama, iki güvenlik katmanı kullanır:

1. Frontend'e erişim için şifre koruması (`.env` dosyasındaki `DEMO_PASSWORD` değeri)
2. Backend'de OpenAI API anahtarının güvenli bir şekilde yönetimi

## Dağıtım (Deployment) Notları

Uygulamayı dağıtırken:

1. Frontend ve backend ayrı servislerde dağıtılmalıdır
2. Her iki servis için de `.env` dosyası yerine platformun çevre değişkenleri/secrets yönetimini kullanın
3. `app_ui.py` içindeki `FASTAPI_URL` değişkenini backend'in yeni URL'si ile güncelleyin
4. Güvenli erişim için platform düzeyinde IP kısıtlamaları veya benzeri ek güvenlik önlemlerini etkinleştirin

## Lisans

Bu uygulama sadece eğitim amaçlıdır ve hukuki tavsiye içermez. 