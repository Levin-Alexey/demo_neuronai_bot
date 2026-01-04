from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

# --- КОНФИГУРАЦИЯ ---
load_dotenv()  # Загружаем переменные из .env файла
INDEX_NAME = "hse-rules"


def test_search():
    print("🔎 Тестируем поиск по базе...")

    # 1. Подключаемся к эмбеддингам (ВАЖНО: модель должна быть та же!)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    # 2. Подключаемся к базе
    vectorstore = PineconeVectorStore(
        index_name=INDEX_NAME,
        embedding=embeddings
    )

    # 3. Задаем вопрос (которого нет в тексте дословно, но есть по смыслу)
    query = "Можно ли работать на стремянке без страховки?"
    print(f"❓ Вопрос: {query}")

    # 4. Ищем 2 самых похожих куска
    results = vectorstore.similarity_search(query, k=2)

    print(f"\n✅ Найдено совпадений: {len(results)}\n")

    for i, res in enumerate(results):
        print(f"--- [Результат {i + 1}] ---")
        print(res.page_content)
        print("-----------------------\n")


if __name__ == "__main__":
    test_search()