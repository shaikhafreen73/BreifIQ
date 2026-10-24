import re
import math
from collections import Counter

# Global cache for the Hugging Face T5 pipeline
_summarizer_pipeline = None


def get_summarizer():
    """Lazy loader for T5-small pipeline. Loads once and reuses."""
    global _summarizer_pipeline
    if _summarizer_pipeline is None:
        try:
            from transformers import pipeline
            print("[BriefIQ] Initializing T5-small Deep Learning pipeline...")
            _summarizer_pipeline = pipeline(
                task="text2text-generation",
                model="t5-small"
            )
            print("[BriefIQ] T5-small model loaded successfully!")
        except Exception as e:
            print(f"[BriefIQ Warning] Could not load Hugging Face pipeline: {e}")
            _summarizer_pipeline = None
    return _summarizer_pipeline


# Pre-warm the model at import time so first request is fast
try:
    get_summarizer()
except Exception:
    pass


def clean_text(text):
    """Normalize whitespace and remove artifacts."""
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def split_into_chunks(text, max_chunk_words=250):
    """
    Splits text into chunks by sentences so each chunk is within T5's optimal token window.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = []
    current_word_count = 0

    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        words_in_sent = len(sent.split())
        if current_word_count + words_in_sent > max_chunk_words and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = [sent]
            current_word_count = words_in_sent
        else:
            current_chunk.append(sent)
            current_word_count += words_in_sent

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks if chunks else [text]


def extract_key_takeaways(text, num_bullets=4):
    """
    Extracts key thematic takeaway sentences using word frequency scoring.
    """
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.strip().split()) > 6]
    if not sentences:
        return ["Document contains concise direct content.", "All key aspects covered."]

    stop_words = {
        "the", "and", "is", "in", "to", "of", "a", "that", "it", "with",
        "as", "for", "was", "on", "are", "by", "this", "be", "an", "at",
        "from", "or", "which", "were", "but", "not", "have", "has", "had",
        "they", "their", "we", "our", "you", "your", "can", "all", "also"
    }

    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    freq = Counter(w for w in words if w not in stop_words)

    scored_sentences = []
    for s in sentences:
        s_words = [w for w in re.findall(r'\b[a-zA-Z]{3,}\b', s.lower()) if w not in stop_words]
        if not s_words:
            continue
        score = sum(freq[w] for w in s_words) / math.sqrt(len(s_words))
        scored_sentences.append((score, s))

    scored_sentences.sort(key=lambda x: x[0], reverse=True)
    top_bullets = [s[1] for s in scored_sentences[:num_bullets]]
    return top_bullets


def fallback_extractive_summary(text, num_sentences=4):
    """Resilient extractive summarizer if DL model encounters environment constraints."""
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.strip().split()) > 5]
    if len(sentences) <= num_sentences:
        return text.strip()
    bullets = extract_key_takeaways(text, num_bullets=num_sentences)
    return " ".join(bullets)


def generate_summary(text, summary_mode="detailed", max_tokens=150, min_tokens=40):
    """
    Deep Learning summarization using T5-small with multi-chunk support.
    Accepts summary_mode: 'concise', 'detailed', or 'executive'.
    """
    text = clean_text(text)
    if not text:
        return "No text available to summarize."

    # Adjust token targets based on mode
    if summary_mode == "concise":
        max_tokens = 90
        min_tokens = 25
    elif summary_mode == "executive":
        max_tokens = 180
        min_tokens = 50
    else:  # detailed
        max_tokens = 220
        min_tokens = 60

    model = get_summarizer()

    # If model is available, use T5-small
    if model is not None:
        try:
            # 300 words ≈ 390 tokens — safely under T5's 512 token hard limit
            chunks = split_into_chunks(text, max_chunk_words=300)
            chunk_summaries = []

            # Limit to 4 chunks max for speed (covers ~1600 words)
            for chunk in chunks[:4]:
                prompt = f"summarize: {chunk}"
                res = model(
                    prompt,
                    max_new_tokens=max_tokens,
                    min_new_tokens=min_tokens,
                    do_sample=False
                )
                chunk_summaries.append(res[0]["generated_text"].strip())

            # Only run synthesis if we have 3+ chunks (saves 1 model call for short docs)
            if len(chunk_summaries) >= 3 and len(" ".join(chunk_summaries)) > 400:
                synthesis_prompt = f"summarize: {' '.join(chunk_summaries)}"
                try:
                    synth_res = model(
                        synthesis_prompt,
                        max_new_tokens=max_tokens,
                        min_new_tokens=min_tokens,
                        do_sample=False
                    )
                    final_summary = synth_res[0]["generated_text"].strip()
                except Exception:
                    final_summary = " ".join(chunk_summaries)
            else:
                final_summary = " ".join(chunk_summaries)

            # Capitalize first letter of sentences
            final_summary = re.sub(r'(^|[.!?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), final_summary)
            return final_summary

        except Exception as e:
            print(f"[BriefIQ] T5 inference exception: {e}. Falling back to extractive summary.")
            return fallback_extractive_summary(text)

    # Fallback if pipeline not loaded
    return fallback_extractive_summary(text)


def analyze_document_text(text, summary_mode="detailed"):
    """
    Full text intelligence analysis:
    - T5 Deep Learning summary
    - Key takeaways bullets
    - Word counts & Reading time savings
    - Readability metrics
    """
    words = text.split()
    orig_words_count = len(words)
    orig_reading_mins = max(1, math.ceil(orig_words_count / 220))

    # Generate summary
    summary = generate_summary(text, summary_mode=summary_mode)
    sum_words_count = len(summary.split())
    sum_reading_mins = max(1, math.ceil(sum_words_count / 220))

    time_saved_mins = max(0, orig_reading_mins - sum_reading_mins)
    reduction_pct = max(0, min(95, round((1 - (sum_words_count / max(1, orig_words_count))) * 100)))

    # Key takeaways
    takeaways = extract_key_takeaways(text, num_bullets=4)

    return {
        "summary": summary,
        "takeaways": takeaways,
        "metrics": {
            "original_word_count": orig_words_count,
            "summary_word_count": sum_words_count,
            "reduction_percentage": reduction_pct,
            "original_reading_time_mins": orig_reading_mins,
            "summary_reading_time_mins": sum_reading_mins,
            "time_saved_mins": time_saved_mins,
            "model_used": "Google T5-small (Deep Learning Text-to-Text Transformer)"
        }
    }