import os
from dotenv import load_dotenv
# Импортируем загрузчики для разных форматов
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec

# --- КОНФИГУРАЦИЯ ---
load_dotenv()  # Загружаем переменные из .env файла

INDEX_NAME = "hse-rules"
# Получаем абсолютный путь к файлу относительно корня проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILE_PATH = os.path.join(BASE_DIR, "src", "kb.docx")  # Теперь можно указывать и .docx, и .pdf


def get_loader_by_extension(file_path):
    """Определяет, какой загрузчик использовать, исходя из расширения и содержимого файла."""
    import subprocess

    # Проверяем реальный тип файла через команду file
    try:
        result = subprocess.run(['file', '--mime-type', '-b', file_path],
                              capture_output=True, text=True, check=True)
        mime_type = result.stdout.strip()
        print(f"   🔍 Определён MIME-тип: {mime_type}")
    except:
        mime_type = None

    # Если это текстовый файл (независимо от расширения)
    if mime_type and 'text' in mime_type:
        print("📝 Обнаружен текстовый файл (будет обработан как .txt).")
        return TextLoader(file_path, encoding='utf-8')
    elif file_path.endswith(".pdf"):
        print("📄 Обнаружен PDF файл.")
        return PyPDFLoader(file_path)
    elif file_path.endswith(".docx"):
        print("📝 Обнаружен Word файл.")
        return Docx2txtLoader(file_path)
    elif file_path.endswith(".txt"):
        print("📝 Обнаружен текстовый файл.")
        return TextLoader(file_path, encoding='utf-8')
    else:
        raise ValueError(f"❌ Формат файла {file_path} не поддерживается! Только .pdf, .docx или .txt")


def upload_file_to_pinecone():
    print(f"🚀 Начинаю обработку файла: {FILE_PATH}...")

    # Проверяем существование файла
    if not os.path.exists(FILE_PATH):
        print(f"   ❌ ОШИБКА: Файл не найден по пути: {FILE_PATH}")
        print(f"   📂 Текущая рабочая директория: {os.getcwd()}")
        print(f"   📂 Директория скрипта: {BASE_DIR}")
        return

    # 1. Выбираем правильный загрузчик
    try:
        loader = get_loader_by_extension(FILE_PATH)
        documents = loader.load()
        print(f"   Успешно прочитано страниц/секций: {len(documents)}")
    except Exception as e:
        print(f"   ❌ Ошибка чтения файла: {e}")
        return

    # 2. Режем на чанки (Всё так же, как и раньше)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    docs = text_splitter.split_documents(documents)
    print(f"   Нарезано на {len(docs)} фрагментов")

    # 3. Инициализируем Embeddings
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    # 4. Проверка индекса Pinecone
    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    existing_indexes = [i.name for i in pc.list_indexes()]

    if INDEX_NAME not in existing_indexes:
        print(f"📦 Создаю новый индекс {INDEX_NAME}...")
        pc.create_index(
            name=INDEX_NAME,
            dimension=1536,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )

    # 5. Загружаем в базу
    print("📡 Отправляю данные в Pinecone...")
    PineconeVectorStore.from_documents(
        documents=docs,
        embedding=embeddings,
        index_name=INDEX_NAME
    )
    print("✅ Успешно! База знаний обновлена.")


if __name__ == "__main__":
    upload_file_to_pinecone()