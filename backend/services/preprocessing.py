import re
import nltk
from nltk.tokenize import sent_tokenize

# Download punkt_tab at module level (with error handling)
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab', quiet=True)


def clean_text(text: str) -> tuple[str, list[str]]:
    """Clean article text. Returns (cleaned_text, list_of_cleaning_steps_applied)."""
    steps = []
    
    # Remove HTML tags
    cleaned = re.sub(r'<[^>]+>', '', text)
    if cleaned != text:
        steps.append("Removed HTML tags")
    
    # Normalize unicode
    import unicodedata
    original = cleaned
    cleaned = unicodedata.normalize('NFKD', cleaned)
    if cleaned != original:
        steps.append("Normalized unicode")
    
    # Remove URLs
    original = cleaned
    cleaned = re.sub(r'https?://\S+|www\.\S+', '', cleaned)
    if cleaned != original:
        steps.append("Removed URLs")
    
    # Remove email addresses
    original = cleaned
    cleaned = re.sub(r'\S+@\S+\.\S+', '', cleaned)
    if cleaned != original:
        steps.append("Removed email addresses")
    
    # Normalize whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    steps.append("Normalized whitespace")
    
    # Remove leading/trailing quotes that wrap entire article
    if cleaned.startswith('"') and cleaned.endswith('"'):
        cleaned = cleaned[1:-1].strip()
        steps.append("Removed wrapping quotes")
    
    return cleaned, steps


def compute_article_stats(text: str) -> dict:
    """Compute statistics about the article text."""
    words = text.split()
    sentences = sent_tokenize(text)
    # Rough token estimate: ~1.3 tokens per word for English
    estimated_tokens = int(len(words) * 1.3)
    
    return {
        "char_count": len(text),
        "word_count": len(words),
        "sentence_count": len(sentences),
        "estimated_tokens": estimated_tokens,
    }


def chunk_text(
    text: str,
    max_tokens: int,
    tokenizer=None,
) -> list[str]:
    """Split text into chunks that fit within the model's token limit.
    
    Uses sentence boundaries to avoid splitting mid-sentence.
    If a tokenizer is provided, uses it for exact token counting.
    Otherwise uses the rough estimate of 1.3 tokens per word.
    """
    sentences = sent_tokenize(text)
    
    if not sentences:
        return [text] if text.strip() else []
    
    chunks = []
    current_chunk_sentences = []
    current_token_count = 0
    
    for sentence in sentences:
        if tokenizer is not None:
            sentence_tokens = len(tokenizer.encode(sentence, add_special_tokens=False))
        else:
            sentence_tokens = int(len(sentence.split()) * 1.3)
        
        # If a single sentence exceeds max_tokens, it gets its own chunk
        # (the model will truncate it, but we don't silently drop it)
        if sentence_tokens >= max_tokens:
            if current_chunk_sentences:
                chunks.append(" ".join(current_chunk_sentences))
                current_chunk_sentences = []
                current_token_count = 0
            chunks.append(sentence)
            continue
        
        if current_token_count + sentence_tokens > max_tokens:
            # Start a new chunk
            chunks.append(" ".join(current_chunk_sentences))
            current_chunk_sentences = [sentence]
            current_token_count = sentence_tokens
        else:
            current_chunk_sentences.append(sentence)
            current_token_count += sentence_tokens
    
    if current_chunk_sentences:
        chunks.append(" ".join(current_chunk_sentences))
    
    return chunks


def preprocess_article(text: str) -> dict:
    """Full preprocessing pipeline. Returns dict with cleaned text, stats, and metadata."""
    original_length = len(text)
    cleaned_text, cleaning_steps = clean_text(text)
    stats = compute_article_stats(cleaned_text)
    
    return {
        "cleaned_text": cleaned_text,
        "original_length": original_length,
        "cleaned_length": len(cleaned_text),
        "cleaning_steps": cleaning_steps,
        "stats": stats,
    }
