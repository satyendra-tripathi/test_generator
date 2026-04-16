import spacy
import logging

logging.basicConfig(level=logging.INFO)

# Load SpaCy model, with fallback handling.
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logging.warning("Downloading en_core_web_sm model...")
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

def extract_keywords(text):
    """
    Extracts important keywords from the given text using SpaCy.
    Returns a list of unique keywords (noun chunks and distinct entities).
    """
    doc = nlp(text)
    keywords = set()
    
    # Extract Entities
    for ent in doc.ents:
        if ent.label_ not in ['CARDINAL', 'ORDINAL', 'DATE', 'TIME', 'QUANTITY']:
            keywords.add(ent.text.lower())
            
    # Extract Noun Chunks
    for chunk in doc.noun_chunks:
        # Ignore pronouns or very short chunks
        if chunk.root.pos_ != "PRON" and len(chunk.text) > 2:
            keywords.add(chunk.text.lower())
            
    # Fallback to important tokens if no keywords found
    if not keywords:
        for token in doc:
            if token.pos_ in ['NOUN', 'PROPN', 'ADJ', 'VERB'] and not token.is_stop and len(token.text) > 2:
                keywords.add(token.text.lower())

    return list(keywords)

def tag_difficulty(text):
    """
    Uses NLP heuristics to estimate the difficulty of a question.
    Returns 'Easy', 'Medium', or 'Hard'.
    """
    doc = nlp(text)
    
    word_count = len([token for token in doc if not token.is_punct])
    avg_word_length = sum(len(token.text) for token in doc if not token.is_punct) / max(1, word_count)
    
    # Count complex words (length > 7 or rare POS tags)
    complex_words = sum(1 for token in doc if not token.is_punct and len(token.text) > 7)
    
    score = 0
    
    # Logic based on word count
    if word_count > 25:
        score += 2
    elif word_count > 12:
        score += 1
        
    # Logic based on word length
    if avg_word_length > 5.5:
        score += 2
    elif avg_word_length > 4.5:
        score += 1
        
    # Logic based on complex words
    if complex_words > 3:
        score += 2
    elif complex_words > 1:
        score += 1
        
    if score >= 4:
        return 'Hard'
    elif score >= 2:
        return 'Medium'
    else:
        return 'Easy'

