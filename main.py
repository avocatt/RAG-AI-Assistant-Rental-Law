import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import chromadb
from openai import OpenAI
import uvicorn

# --- Configuration ---
load_dotenv()  # Load environment variables from .env file

CHROMA_DB_PATH = "./chroma_db_store"
CHROMA_COLLECTION_NAME = "tbk_kira_articles"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Used by Chroma's OpenAIEmbeddingFunction
EMBEDDING_MODEL_NAME = "text-embedding-ada-002"
LLM_MODEL_NAME = "gpt-3.5-turbo"  # Or "gpt-4o"
TOP_K_RESULTS = 3

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Türk Borçlar Kanunu - Kira Hukuku Asistanı",
    description="TBK Konut ve Çatılı İşyeri Kiraları maddeleri hakkında soruları yanıtlar.",
    version="0.1.0"
)

# --- Pydantic Models ---


class QueryRequest(BaseModel):
    query_text: str


class QueryResponse(BaseModel):
    answer: str
    retrieved_sources: list[dict]  # To show what was used


# --- Global Clients (Initialize on startup) ---
chroma_client = None
openai_client = None
db_collection = None


@app.on_event("startup")
async def startup_event():
    global chroma_client, openai_client, db_collection

    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY not found. Please set it in your .env file.")

    print("Initializing ChromaDB client...")
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

    from chromadb.utils import embedding_functions
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=OPENAI_API_KEY,
        model_name=EMBEDDING_MODEL_NAME
    )

    try:
        db_collection = chroma_client.get_collection(
            name=CHROMA_COLLECTION_NAME,
            embedding_function=openai_ef  # Provide EF for query embedding consistency
        )
        print(
            f"Successfully connected to ChromaDB collection: '{CHROMA_COLLECTION_NAME}' with {db_collection.count()} items.")
    except Exception as e:
        print(f"Error connecting to ChromaDB collection: {e}")
        # Depending on the error, you might want to prevent app startup
        # For now, we'll let it try, but queries will fail.
        # A more robust app might try to create_collection if get fails and it's expected.
        # However, ingestion is a separate step, so collection should exist.
        raise RuntimeError(
            f"Could not get ChromaDB collection '{CHROMA_COLLECTION_NAME}'. Ensure it was created by ingest_data.py. Error: {e}")

    print("Initializing OpenAI client for LLM...")
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    print("Initialization complete.")


def construct_llm_prompt(query: str, retrieved_chunks: list[dict]) -> str:
    if not retrieved_chunks:
        return f"""Sen Türk Borçlar Kanunu'nun Konut ve Çatılı İşyeri Kiraları bölümü hakkında uzman bir hukuk asistanısın.
Görevin, kullanıcının sorusunu yanıtlamaktır. Ancak, bu soruyla ilgili spesifik bir metin bulunamadı.
Lütfen genel bilginle veya soruyu yanıtlayamayacağını belirterek cevap ver.

SORU:
{query}

CEVAP:
"""

    context_str = ""
    for i, chunk_info in enumerate(retrieved_chunks):
        article_num = chunk_info['metadata'].get(
            'article_number', 'Bilinmeyen Madde')
        article_header = chunk_info['metadata'].get(
            'article_header', 'Başlık Yok')
        text = chunk_info['document']

        context_str += f"METİN {i+1} ({article_num} - Başlık: {article_header}):\n"
        context_str += f"{text}\n---\n"

    prompt_template = f"""Sen Türk Borçlar Kanunu'nun Konut ve Çatılı İşyeri Kiraları bölümü hakkında uzman bir hukuk asistanısın.
Görevin, kullanıcının sorusunu SADECE aşağıda sağlanan METİNLERİ kullanarak yanıtlamaktır.
Cevabını oluştururken, bilgiyi hangi maddeden (MADDE numarası) ve metinden (METİN Numarası) aldığını belirt. Örneğin: "(Kaynak: METİN 1, MADDE 339)".
Eğer sağlanan metinlerde sorunun cevabı yoksa, "Sağlanan bilgiler arasında bu soruya kesin bir cevap bulamadım." şeklinde yanıt ver.
Cevabın açık, anlaşılır ve Türkçe olmalıdır. Yorum yapma veya metinlerin dışında bilgi ekleme.

METİNLER:
{context_str}
SORU:
{query}

CEVAP:
"""
    return prompt_template

# --- API Endpoints ---


@app.post("/query", response_model=QueryResponse)
async def handle_query(request: QueryRequest):
    global db_collection, openai_client

    if not db_collection:
        raise HTTPException(
            status_code=503, detail="ChromaDB collection not available. Server may be initializing or encountered an error.")
    if not openai_client:
        raise HTTPException(
            status_code=503, detail="OpenAI client not available.")

    user_query = request.query_text
    print(f"Received query: {user_query}")

    try:
        # 1. Retrieve relevant documents from ChromaDB
        # The collection's embedding function will handle embedding the query_text
        results = db_collection.query(
            query_texts=[user_query],
            n_results=TOP_K_RESULTS,
            include=['documents', 'metadatas']  # Ensure metadatas are included
        )

        retrieved_docs = []
        if results and results.get('documents') and results.get('metadatas'):
            for i in range(len(results['documents'][0])):
                retrieved_docs.append({
                    "document": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i]
                })

        print(f"Retrieved {len(retrieved_docs)} documents from ChromaDB.")
        if not retrieved_docs:
            print("No relevant documents found in ChromaDB for the query.")
            # Fallback or inform user, here we'll let the LLM handle it via prompt

        # 2. Construct prompt for LLM
        prompt = construct_llm_prompt(user_query, retrieved_docs)
        # print(f"\nConstructed LLM Prompt:\n{prompt}\n") # For debugging

        # 3. Call LLM
        print(f"Sending prompt to LLM model: {LLM_MODEL_NAME}")
        chat_completion = openai_client.chat.completions.create(
            model=LLM_MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful legal assistant specialized in Turkish Rental Law for residential and roofed workplaces."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3  # Adjust for more factual/creative responses
        )

        answer = chat_completion.choices[0].message.content.strip()
        print(f"LLM Answer: {answer}")

        return QueryResponse(answer=answer, retrieved_sources=retrieved_docs)

    except RuntimeError as e:  # Catch specific runtime errors like API key issues
        print(f"Runtime error during query processing: {e}")
        raise HTTPException(
            status_code=500, detail=f"An internal error occurred: {str(e)}")
    except Exception as e:
        print(f"Unexpected error during query processing: {e}")
        # Log the full traceback for debugging
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    print("Starting Uvicorn server for FastAPI app...")
    # Make sure .env is loaded for this direct run context as well
    # load_dotenv() # Already called at the top
    # OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") # Re-check if running main directly and startup hasn't run
    # if not OPENAI_API_KEY:
    #    print("Warning: OPENAI_API_KEY not found for direct run. Startup event will handle it if run via uvicorn command.")

    uvicorn.run(app, host="0.0.0.0", port=8000)
    # To run from terminal: uvicorn main:app --reload
