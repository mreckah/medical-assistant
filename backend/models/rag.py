import chromadb
from chromadb.utils import embedding_functions
import os

# Connect to the Docker container
chroma_client = chromadb.HttpClient(host='localhost', port=8000)

# Use a free, high-quality local embedding model
# This downloads a small model (~80MB) automatically on first run
emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# Get or Create the collection (like a table in SQL)
collection = chroma_client.get_or_create_collection(
    name="medical_knowledge",
    embedding_function=emb_fn
)

class RagEngine:
    @staticmethod
    def add_knowledge(text_chunks: list, ids: list):
        """Feeds new information into the brain."""
        collection.add(
            documents=text_chunks,
            ids=ids
        )
        print(f"Added {len(text_chunks)} documents to memory.")

    @staticmethod
    def search(query: str, n_results=3):
        """Retrieves the most relevant facts for a query."""
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        # Flatten the list of results
        if results["documents"]:
            return results["documents"][0]
        return []