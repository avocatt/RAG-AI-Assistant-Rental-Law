import os
import json
from dotenv import load_dotenv
import chromadb
from openai import OpenAI

# Assuming legal_parser.py is in the same directory or accessible
from legal_parser import parse_legal_text

# --- Configuration ---
TEXT_FILE_PATH = "source_data/TBK_Konut_ve_Catili_Isyeri_Kiralari.txt"
# PARSED_ARTICLES_JSON_PATH = "parsed_articles.json" # Output of parser, not directly used by ingest if parsing on the fly
# Directory where ChromaDB will store its data
CHROMA_DB_PATH = "./chroma_db_store"
CHROMA_COLLECTION_NAME = "tbk_kira_articles"
# Standard OpenAI embedding model
EMBEDDING_MODEL_NAME = "text-embedding-ada-002"

# --- Helper Functions ---


def get_OPENAI_API_KEY():
    load_dotenv()  # Load environment variables from .env file
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found in .env file or environment variables. Please create a .env file with OPENAI_API_KEY=\"your_key_here\".")
    return api_key

# --- Main Ingestion Logic ---


def main():
    print("Starting data ingestion process...")

    # 1. Load API Key
    OPENAI_API_KEY = get_OPENAI_API_KEY()

    # 2. Parse legal text
    print(f"Parsing legal text from: {TEXT_FILE_PATH}")
    articles_data = parse_legal_text(TEXT_FILE_PATH)
    if not articles_data:
        print("No articles parsed from the text file. Exiting.")
        return
    print(f"Successfully parsed {len(articles_data)} articles.")

    # Prepare data for ChromaDB
    documents_to_store = []
    metadatas_to_store = []
    ids_to_store = []

    for i, article in enumerate(articles_data):
        if not article.get('text') or not article.get('text').strip():
            print(
                f"Warning: Article {article.get('article_number', 'Unknown')} has empty text. Skipping.")
            continue

        documents_to_store.append(article['text'])
        metadatas_to_store.append({
            "article_number": str(article['article_number']),  # Ensure string
            "article_header": str(article['article_header'])  # Ensure string
        })
        # Use article number as a unique ID. Ensure it's a string.
        ids_to_store.append(str(article['article_number']))

    if not documents_to_store:
        print("No valid documents to add to ChromaDB after filtering. Exiting.")
        return

    # 3. Setup ChromaDB client and collection
    print(f"Setting up ChromaDB persistent client at: {CHROMA_DB_PATH}")
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

    # Embedding function using standard OpenAI API
    from chromadb.utils import embedding_functions

    # Configure OpenAI embedding function with standard settings
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=OPENAI_API_KEY,
        model_name=EMBEDDING_MODEL_NAME
    )

    print(
        f"Attempting to get or create ChromaDB collection: '{CHROMA_COLLECTION_NAME}'")

    # To ensure the collection uses the correct embedding function,
    # it's often safer to delete and recreate if it exists
    try:
        print(
            f"Checking if collection '{CHROMA_COLLECTION_NAME}' already exists...")
        chroma_client.delete_collection(name=CHROMA_COLLECTION_NAME)
        print(
            f"Collection '{CHROMA_COLLECTION_NAME}' existed and was deleted to ensure a fresh start with the correct embedding function.")
    except Exception as e:
        print(
            f"Collection '{CHROMA_COLLECTION_NAME}' either did not exist or another error occurred during deletion attempt: {e}. Proceeding to create.")
        pass

    collection = chroma_client.get_or_create_collection(
        name=CHROMA_COLLECTION_NAME,
        embedding_function=openai_ef
    )
    print(f"Collection '{CHROMA_COLLECTION_NAME}' is ready.")

    # 4. Add documents to ChromaDB
    print(
        f"Adding {len(documents_to_store)} documents to collection '{CHROMA_COLLECTION_NAME}'...")

    collection.add(
        documents=documents_to_store,
        metadatas=metadatas_to_store,
        ids=ids_to_store
    )
    print("Documents added to ChromaDB successfully.")

    # 5. Verification (optional but recommended)
    count = collection.count()
    print(
        f"Verification: Collection '{CHROMA_COLLECTION_NAME}' now contains {count} documents.")
    if count > 0 and count <= 5:  # Peek if few documents, to see structure
        print("Sample of first few documents in the collection (structure check):")
        sample_results = collection.peek(limit=5)  # Peek a few items
        print(json.dumps(sample_results, indent=2, ensure_ascii=False))
    elif count == 0 and len(documents_to_store) > 0:
        print("Error: Documents were prepared but the collection count is 0. Check for issues during add.")

    print("Data ingestion process complete.")


if __name__ == "__main__":
    # This ensures that .env is loaded when the script is run directly
    # and get_OPENAI_API_KEY() can access the environment variables.
    load_dotenv()
    main()
