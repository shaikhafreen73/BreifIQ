import fitz  # PyMuPDF
import os


def extract_text_and_meta(pdf_path):
    """
    Extracts text and metadata from PDF using PyMuPDF (fitz).
    Returns a dict with text, page_count, metadata, and word_count.
    """
    doc = fitz.open(pdf_path)
    pages_text = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        if text.strip():
            pages_text.append(text.strip())

    total_pages = len(doc)
    metadata = doc.metadata or {}
    doc.close()

    full_text = "\n\n".join(pages_text)
    words = full_text.split()
    word_count = len(words)

    return {
        "text": full_text,
        "page_count": total_pages,
        "word_count": word_count,
        "title": metadata.get("title") or os.path.basename(pdf_path),
        "author": metadata.get("author") or "Unknown"
    }


def extract_text(pdf_path):
    """Backwards-compatible text extractor for existing calls."""
    data = extract_text_and_meta(pdf_path)
    return data["text"]