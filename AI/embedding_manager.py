import json
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
cache_dir = os.path.join(BASE_DIR, "embeddings_data")

embeddings = HuggingFaceEmbeddings(
    model_name="intfloat/multilingual-e5-large",
    model_kwargs={'device': 'cuda'},
    encode_kwargs={'normalize_embeddings': True},
    cache_folder=cache_dir
)


def embedding_db(embeddings: HuggingFaceEmbeddings, json_data_path: str, path: str):
    """
    Создает базу эмбеддингов на основе данных из JSON.
    Каждый документ включает заголовки site и endpoint и соответствующий текст.
    """
    with open(json_data_path, 'r', encoding='utf-8') as f:
        parsed_data = json.load(f)

    # Создаю чанки не по длине, а по заголовкам
    documents = []
    for entry in parsed_data:
        if 'text' in entry:
            header = f"site: {entry.get('site', '').strip()}\nendpoint: {entry.get('endpoint', '').strip()}\n"
            for key, value in entry['text'].items():
                doc = header + f"{key}: {value.strip()}"
                documents.append(doc)

    # Если документы получились слишком длинными, их можно разбить по логическим разделителям
    chunk_size = 500
    chunk_overlap = chunk_size // 20
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " "]
    )
    chunks = text_splitter.create_documents(documents)

    db = FAISS.from_documents(chunks, embeddings)

    db.save_local(path)


async def load_embedded_data(path_f: str, embeddings: HuggingFaceEmbeddings):
    from langchain_community.vectorstores import FAISS
    db = FAISS.load_local(path_f, embeddings, allow_dangerous_deserialization=True)
    return db

async def find_similarity(db, message: str):
    return db.similarity_search(message, k=5)


# Запуск создания эмбеддингов
if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.abspath(os.path.join(script_dir, ".."))
    file_path = os.path.join(parent_dir, "AI", "embeddings_data", "json_data/")

    path_json = file_path + "MMCS_data.json"
    embedding_db(embeddings, path_json, cache_dir)

    path_json = file_path + "SFEDU_data.json"
    embedding_db(embeddings, path_json, cache_dir)