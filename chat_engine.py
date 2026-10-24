"""
BriefIQ Chat Engine
Extractive Q&A over stored document summaries using TF-IDF sentence ranking.
Works fully offline — no external API required.
"""

import re
import math
from collections import Counter


# ---------------------------------------------------------------------------
# Text Utilities
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> list[str]:
    """Lowercase word tokens, stripping punctuation."""
    return re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())


STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "to", "of", "in", "on",
    "at", "by", "for", "with", "about", "from", "into", "through",
    "and", "or", "but", "not", "so", "if", "as", "that", "this", "it",
    "he", "she", "they", "we", "you", "i", "me", "him", "her", "us",
    "my", "your", "his", "its", "our", "their", "what", "which", "who",
    "how", "when", "where", "why", "there", "here", "than", "then",
}


def _keywords(text: str) -> list[str]:
    return [t for t in _tokenize(text) if t not in STOP_WORDS]


# ---------------------------------------------------------------------------
# TF-IDF Sentence Ranking
# ---------------------------------------------------------------------------

def _split_sentences(text: str) -> list[str]:
    """Split text into sentences, filtering very short ones."""
    raw = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in raw if len(s.strip().split()) >= 4]


def _tfidf_scores(sentences: list[str], query_words: list[str]) -> list[float]:
    """Score each sentence by TF-IDF overlap with the query."""
    num_docs = len(sentences)
    if num_docs == 0:
        return []

    # IDF: how rare each query word is across sentences
    doc_freq: Counter = Counter()
    for sent in sentences:
        words_in_sent = set(_keywords(sent))
        for w in query_words:
            if w in words_in_sent:
                doc_freq[w] += 1

    idf = {
        w: math.log((num_docs + 1) / (doc_freq.get(w, 0) + 1)) + 1
        for w in query_words
    }

    scores = []
    for sent in sentences:
        sent_words = _keywords(sent)
        sent_counter = Counter(sent_words)
        total_words = max(len(sent_words), 1)
        score = 0.0
        for w in query_words:
            tf = sent_counter.get(w, 0) / total_words
            score += tf * idf.get(w, 0)
        # Length penalty: prefer medium-length sentences
        length_factor = 1.0 - abs(len(sent_words) - 20) / 60
        scores.append(score * max(length_factor, 0.5))

    return scores


# ---------------------------------------------------------------------------
# Main QA Function
# ---------------------------------------------------------------------------

# Canned responses for greetings / meta questions
_CANNED = {
    "hello": "Hi there! 👋 I'm your BriefIQ document assistant. Ask me anything about this document!",
    "hi": "Hello! Ask me a question about this document and I'll find the answer from its summary.",
    "hey": "Hey! I'm ready to help. What would you like to know about this document?",
    "thanks": "You're welcome! Feel free to ask more questions about the document.",
    "thank you": "Happy to help! Any other questions about this document?",
    "who are you": "I'm BriefIQ's built-in document assistant. I can answer questions based on the document's summary and content.",
    "what can you do": "I can answer questions about this document — key topics, findings, data, summaries, and more. Just ask!",
}


def answer_question(question: str, summary: str, context: str = "") -> dict:
    """
    Answer a question using the document's summary (+ optional full context).

    Returns:
        {
            "answer": str,
            "confidence": "high" | "medium" | "low",
            "source": "summary" | "context" | "canned" | "fallback"
        }
    """
    if not question or not question.strip():
        return {"answer": "Please ask a question!", "confidence": "low", "source": "fallback"}

    q_clean = question.strip().lower().rstrip("?!")

    # Check canned responses first
    for trigger, reply in _CANNED.items():
        if trigger in q_clean:
            return {"answer": reply, "confidence": "high", "source": "canned"}

    query_words = _keywords(question)
    if not query_words:
        return {
            "answer": "I couldn't understand that question. Could you rephrase it?",
            "confidence": "low",
            "source": "fallback"
        }

    # Build candidate pool: summary first, then full context
    full_text = summary
    if context and len(context) > len(summary):
        full_text = summary + " " + context[:3000]  # cap to avoid overload

    sentences = _split_sentences(full_text)

    if not sentences:
        return {
            "answer": "This document doesn't have enough text for me to answer that question.",
            "confidence": "low",
            "source": "fallback"
        }

    scores = _tfidf_scores(sentences, query_words)
    if not scores or max(scores) == 0:
        # No overlap found — give a fallback
        return {
            "answer": (
                f"I couldn't find specific information about \"{question.strip()}\" in this document. "
                "Try asking about the main topics, key findings, or summary of the document."
            ),
            "confidence": "low",
            "source": "fallback"
        }

    # Pick top 2 sentences
    ranked = sorted(zip(scores, sentences), reverse=True)
    best_score, best_sent = ranked[0]
    answer_parts = [best_sent]

    if len(ranked) > 1 and ranked[1][0] > best_score * 0.5:
        second_sent = ranked[1][1]
        if second_sent != best_sent:
            answer_parts.append(second_sent)

    answer = " ".join(answer_parts)

    # Capitalize first letter
    answer = answer[0].upper() + answer[1:] if answer else answer

    # Confidence based on score magnitude
    if best_score >= 0.15:
        confidence = "high"
    elif best_score >= 0.05:
        confidence = "medium"
    else:
        confidence = "low"

    source = "summary" if len(context) == 0 or full_text.startswith(summary) else "context"

    return {"answer": answer, "confidence": confidence, "source": source}
