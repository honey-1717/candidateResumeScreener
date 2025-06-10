import re
import string
from typing import List, Dict, Set, Tuple

def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace and normalizing
    
    Args:
        text (str): Text to clean
        
    Returns:
        str: Cleaned text
    """
    # Replace multiple whitespace with a single space
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text

def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    """
    Extract keywords from text
    
    Args:
        text (str): Text to extract keywords from
        min_length (int, optional): Minimum keyword length. Defaults to 3.
        
    Returns:
        list: List of keywords
    """
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    
    # Split into words
    words = text.split()
    
    # Filter by length
    keywords = [word for word in words if len(word) >= min_length]
    
    return keywords

def calculate_keyword_frequency(text: str, min_length: int = 3) -> Dict[str, int]:
    """
    Calculate keyword frequency in text
    
    Args:
        text (str): Text to analyze
        min_length (int, optional): Minimum keyword length. Defaults to 3.
        
    Returns:
        dict: Dictionary mapping keywords to frequencies
    """
    keywords = extract_keywords(text, min_length)
    
    # Calculate frequencies
    frequencies = {}
    for keyword in keywords:
        frequencies[keyword] = frequencies.get(keyword, 0) + 1
    
    return frequencies

def calculate_keyword_overlap(text1: str, text2: str, min_length: int = 3) -> Tuple[Set[str], float]:
    """
    Calculate keyword overlap between two texts
    
    Args:
        text1 (str): First text
        text2 (str): Second text
        min_length (int, optional): Minimum keyword length. Defaults to 3.
        
    Returns:
        tuple: (Set of common keywords, Overlap percentage)
    """
    keywords1 = set(extract_keywords(text1, min_length))
    keywords2 = set(extract_keywords(text2, min_length))
    
    common_keywords = keywords1.intersection(keywords2)
    
    # Calculate overlap percentage
    if not keywords1 or not keywords2:
        overlap_percentage = 0.0
    else:
        overlap_percentage = len(common_keywords) / max(len(keywords1), len(keywords2)) * 100
    
    return common_keywords, overlap_percentage

def extract_emails(text: str) -> List[str]:
    """
    Extract email addresses from text
    
    Args:
        text (str): Text to extract emails from
        
    Returns:
        list: List of email addresses
    """
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return re.findall(email_pattern, text)

def extract_phone_numbers(text: str) -> List[str]:
    """
    Extract phone numbers from text
    
    Args:
        text (str): Text to extract phone numbers from
        
    Returns:
        list: List of phone numbers
    """
    # This pattern matches various phone number formats
    phone_pattern = r'(?:\+\d{1,3}[-.\s]?)?(?:$$?\d{3}$$?[-.\s]?)?\d{3}[-.\s]?\d{4}'
    return re.findall(phone_pattern, text)

def extract_urls(text: str) -> List[str]:
    """
    Extract URLs from text
    
    Args:
        text (str): Text to extract URLs from
        
    Returns:
        list: List of URLs
    """
    url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
    return re.findall(url_pattern, text)

def truncate_text(text: str, max_length: int, add_ellipsis: bool = True) -> str:
    """
    Truncate text to a maximum length
    
    Args:
        text (str): Text to truncate
        max_length (int): Maximum length
        add_ellipsis (bool, optional): Whether to add ellipsis. Defaults to True.
        
    Returns:
        str: Truncated text
    """
    if len(text) <= max_length:
        return text
    
    truncated = text[:max_length]
    if add_ellipsis:
        truncated += "..."
    
    return truncated

def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences
    
    Args:
        text (str): Text to split
        
    Returns:
        list: List of sentences
    """
    # Simple sentence splitting - not perfect but works for most cases
    sentence_pattern = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s'
    sentences = re.split(sentence_pattern, text)
    return [s.strip() for s in sentences if s.strip()]

def highlight_keywords(text: str, keywords: List[str], case_sensitive: bool = False) -> str:
    """
    Highlight keywords in text by surrounding them with asterisks
    
    Args:
        text (str): Text to highlight keywords in
        keywords (list): List of keywords to highlight
        case_sensitive (bool, optional): Whether matching should be case-sensitive. Defaults to False.
        
    Returns:
        str: Text with highlighted keywords
    """
    if not keywords:
        return text
    
    # Sort keywords by length (longest first) to avoid partial matches
    sorted_keywords = sorted(keywords, key=len, reverse=True)
    
    # Create pattern for all keywords
    if case_sensitive:
        pattern = '|'.join(re.escape(kw) for kw in sorted_keywords)
    else:
        pattern = '|'.join(re.escape(kw) for kw in sorted_keywords)
        flags = re.IGNORECASE
    
    # Replace keywords with highlighted version
    if case_sensitive:
        return re.sub(pattern, lambda m: f"**{m.group(0)}**", text)
    else:
        return re.sub(pattern, lambda m: f"**{m.group(0)}**", text, flags=flags)
