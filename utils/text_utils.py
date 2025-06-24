import re
from typing import List, Dict, Set, Tuple
# Import the new LLM-based anonymizer
from services.llm_client import anonymize_text_with_llm

def anonymize_text_content(text: str) -> str:
    """
    Anonymizes resume text by removing PII using an LLM.
    This function replaces the previous regex-based approach for better accuracy
    and to resolve persistent errors.
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Call the new, more reliable LLM-based anonymization function.
    # This is the only change in this file.
    return anonymize_text_with_llm(text)


# --- ALL OTHER FUNCTIONS IN THIS FILE REMAIN UNCHANGED ---
# They are kept here to ensure the screener functionality is not affected.

def clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text

def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    import string
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    words = text.split()
    keywords = [word for word in words if len(word) >= min_length]
    return keywords

def calculate_keyword_frequency(text: str, min_length: int = 3) -> Dict[str, int]:
    keywords = extract_keywords(text, min_length)
    frequencies = {}
    for keyword in keywords:
        frequencies[keyword] = frequencies.get(keyword, 0) + 1
    return frequencies

def calculate_keyword_overlap(text1: str, text2: str, min_length: int = 3) -> Tuple[Set[str], float]:
    keywords1 = set(extract_keywords(text1, min_length))
    keywords2 = set(extract_keywords(text2, min_length))
    common_keywords = keywords1.intersection(keywords2)
    if not keywords1 or not keywords2:
        overlap_percentage = 0.0
    else:
        overlap_percentage = len(common_keywords) / max(len(keywords1), len(keywords2)) * 100
    return common_keywords, overlap_percentage

def extract_emails(text: str) -> List[str]:
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return re.findall(email_pattern, text)

def extract_phone_numbers(text: str) -> List[str]:
    phone_pattern = r'(?:\+\d{1,3}[-.\s]?)?(?:$$\d{3}$$)?[-.\s]?\d{3}[-.\s]?\d{4}'
    return re.findall(phone_pattern, text)

def extract_urls(text: str) -> List[str]:
    url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
    return re.findall(url_pattern, text)

def truncate_text(text: str, max_length: int, add_ellipsis: bool = True) -> str:
    if len(text) <= max_length:
        return text
    truncated = text[:max_length]
    if add_ellipsis:
        truncated += "..."
    return truncated

def split_into_sentences(text: str) -> List[str]:
    sentence_pattern = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s'
    sentences = re.split(sentence_pattern, text)
    return [s.strip() for s in sentences if s.strip()]

def highlight_keywords(text: str, keywords: List[str], case_sensitive: bool = False) -> str:
    if not keywords:
        return text
    sorted_keywords = sorted(keywords, key=len, reverse=True)
    flags = 0 if case_sensitive else re.IGNORECASE
    pattern = '|'.join(re.escape(kw) for kw in sorted_keywords)
    return re.sub(pattern, lambda m: f"**{m.group(0)}**", text, flags=flags)
