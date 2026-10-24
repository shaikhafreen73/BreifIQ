import os
import docx
from pdf_reader import extract_text_and_meta


def is_tabular_file(filename):
    """Checks if the file is a structured dataset file."""
    ext = os.path.splitext(filename)[1].lower()
    return ext in [".csv", ".xlsx", ".xls", ".tsv"]


def process_document(filepath):
    """
    Extracts text and metadata from any supported document format:
    - PDF (.pdf)
    - Word (.docx)
    - Plain Text / Markdown / Code / Logs (.txt, .md, .log, .rtf, .json, .html, .py, etc.)
    Returns dict with keys: text, title, page_or_section_count, word_count, file_type
    """
    ext = os.path.splitext(filepath)[1].lower()
    filename = os.path.basename(filepath)

    if ext == ".pdf":
        meta = extract_text_and_meta(filepath)
        return {
            "text": meta["text"],
            "title": meta.get("title") or filename,
            "page_count": meta.get("page_count", 1),
            "word_count": meta.get("word_count", 0),
            "file_type": "PDF Document"
        }

    elif ext == ".docx":
        doc = docx.Document(filepath)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        full_text = "\n\n".join(paragraphs)
        words = full_text.split()
        return {
            "text": full_text,
            "title": filename,
            "page_count": max(1, len(paragraphs) // 5),
            "word_count": len(words),
            "file_type": "Word Document (.docx)"
        }

    else:
        # Generic text / markdown / code / log reader
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252", "iso-8859-1"]
        full_text = ""
        for enc in encodings:
            try:
                with open(filepath, "r", encoding=enc, errors="ignore") as f:
                    full_text = f.read()
                break
            except Exception:
                continue

        words = full_text.split()
        line_count = len(full_text.splitlines())
        return {
            "text": full_text,
            "title": filename,
            "page_count": max(1, line_count // 45),
            "word_count": len(words),
            "file_type": f"{ext.replace('.', '').upper() or 'Text'} Document"
        }
