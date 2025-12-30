import os
import glob
from pypdf import PdfReader
from docx import Document
from models.rag import RagEngine

# --- CONFIGURATION ---
DOCS_FOLDER = "knowledge_docs"  # Put your files here
CHUNK_SIZE = 500  # Characters per chunk (adjust based on your needs)


def read_pdf(file_path):
    text = ""
    try:
        reader = PdfReader(file_path)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error reading PDF {file_path}: {e}")
    return text


def read_docx(file_path):
    text = ""
    try:
        doc = Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        print(f"Error reading DOCX {file_path}: {e}")
    return text


def chunk_text(text, chunk_size=CHUNK_SIZE):
    """Splits long text into smaller chunks for better search results."""
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]


def process_documents():
    # 1. Ensure folder exists
    if not os.path.exists(DOCS_FOLDER):
        os.makedirs(DOCS_FOLDER)
        print(f"Created folder '{DOCS_FOLDER}'. Please put your PDF/DOCX files there and run this script again.")
        return

    all_chunks = []
    all_ids = []

    # 2. Find all files
    files = glob.glob(os.path.join(DOCS_FOLDER, "*.*"))
    print(f"Found {len(files)} files in '{DOCS_FOLDER}'...")

    doc_counter = 0

    for file_path in files:
        filename = os.path.basename(file_path)
        print(f"Processing: {filename}")

        raw_text = ""
        if filename.lower().endswith(".pdf"):
            raw_text = read_pdf(file_path)
        elif filename.lower().endswith(".docx"):
            raw_text = read_docx(file_path)
        else:
            print(f"Skipping unsupported file: {filename}")
            continue

        if not raw_text.strip():
            print(f"Warning: No text found in {filename}")
            continue

        # 3. Chunk the text
        chunks = chunk_text(raw_text)

        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            # Create a unique ID: filename_chunkIndex
            # We sanitize the filename to ensure valid IDs
            safe_name = "".join([c for c in filename if c.isalnum()])
            all_ids.append(f"{safe_name}_{i}")

        doc_counter += 1

    # 4. Feed to ChromaDB
    if all_chunks:
        print(f"Uploading {len(all_chunks)} text chunks to ChromaDB...")
        RagEngine.add_knowledge(all_chunks, all_ids)
        print("✅ Success! Knowledge base updated.")
    else:
        print("No valid text found to upload.")


if __name__ == "__main__":
    process_documents()