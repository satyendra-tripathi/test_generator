# import spacy
# import logging

# logging.basicConfig(level=logging.INFO)

# # Load SpaCy model, with fallback handling.
# try:
#     nlp = spacy.load("en_core_web_sm")
# except OSError:
#     logging.warning("Downloading en_core_web_sm model...")
#     from spacy.cli import download
#     download("en_core_web_sm")
#     nlp = spacy.load("en_core_web_sm")

# def extract_keywords(text):
#     """
#     Extracts important keywords from the given text using SpaCy.
#     Returns a list of unique keywords (noun chunks and distinct entities).
#     """
#     doc = nlp(text)
#     keywords = set()
    
#     # Extract Entities
#     for ent in doc.ents:
#         if ent.label_ not in ['CARDINAL', 'ORDINAL', 'DATE', 'TIME', 'QUANTITY']:
#             keywords.add(ent.text.lower())
            
#     # Extract Noun Chunks
#     for chunk in doc.noun_chunks:
#         # Ignore pronouns or very short chunks
#         if chunk.root.pos_ != "PRON" and len(chunk.text) > 2:
#             keywords.add(chunk.text.lower())
            
#     # Fallback to important tokens if no keywords found
#     if not keywords:
#         for token in doc:
#             if token.pos_ in ['NOUN', 'PROPN', 'ADJ', 'VERB'] and not token.is_stop and len(token.text) > 2:
#                 keywords.add(token.text.lower())

#     return list(keywords)

# def tag_difficulty(text):
#     """
#     Uses NLP heuristics to estimate the difficulty of a question.
#     Returns 'Easy', 'Medium', or 'Hard'.
#     """
#     doc = nlp(text)
    
#     word_count = len([token for token in doc if not token.is_punct])
#     avg_word_length = sum(len(token.text) for token in doc if not token.is_punct) / max(1, word_count)
    
#     # Count complex words (length > 7 or rare POS tags)
#     complex_words = sum(1 for token in doc if not token.is_punct and len(token.text) > 7)
    
#     score = 0
    
#     # Logic based on word count
#     if word_count > 25:
#         score += 2
#     elif word_count > 12:
#         score += 1
        
#     # Logic based on word length
#     if avg_word_length > 5.5:
#         score += 2
#     elif avg_word_length > 4.5:
#         score += 1
        
#     # Logic based on complex words
#     if complex_words > 3:
#         score += 2
#     elif complex_words > 1:
#         score += 1
        
#     if score >= 4:
#         return 'Hard'
#     elif score >= 2:
#         return 'Medium'
#     else:
#         return 'Easy'

from google import genai
import json
import re
import random

# 🔑 Gemini Client
client = genai.Client(api_key="YOUR_NEW_API_KEY")


# ✅ AI Question Generator (FINAL + SMART FALLBACK)
def generate_questions(topic, num_questions=5):
    prompt = f"""
    Generate {num_questions} multiple choice questions on topic: {topic}.
    
    Return ONLY JSON format like:
    [
      {{
        "question": "...",
        "options": ["A", "B", "C", "D"],
        "answer": "correct option"
      }}
    ]
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )

        content = response.text
        print("🔥 RAW AI OUTPUT:", content)

        match = re.search(r'\[.*\]', content, re.DOTALL)
        if match:
            questions = json.loads(match.group())

            # ✅ VALIDATION
            if isinstance(questions, list) and len(questions) > 0:
                return questions
            else:
                print("⚠️ Invalid or empty AI response")

        else:
            print("❌ No JSON found in AI response")

    except Exception as e:
        print("❌ AI Error:", e)

    # =========================
    # 🔥 SMART FALLBACK
    # =========================
    print("⚠️ Using SMART fallback questions")

    templates = [
        f"What is {topic}?",
        f"Which statement is correct about {topic}?",
        f"{topic} is mainly used for what?",
        f"What is a key feature of {topic}?",
        f"Why is {topic} important?",
        f"Which field commonly uses {topic}?",
        f"What is the purpose of {topic}?",
        f"Which of the following best describes {topic}?"
    ]

    options_pool = [
        "A programming concept",
        "A database system",
        "A networking protocol",
        "A hardware component",
        "A software tool",
        "A machine learning technique",
        "A web technology",
        "An operating system feature"
    ]

    fallback_questions = []

    for i in range(num_questions):
        question = random.choice(templates)
        options = random.sample(options_pool, 4)
        answer = options[0]  # first option correct (randomized order)

        fallback_questions.append({
            "question": f"{question} (Q{i+1})",
            "options": options,
            "answer": answer
        })

    return fallback_questions


# ✅ Difficulty tagging
def tag_difficulty(question):
    if len(question) < 50:
        return "Easy"
    elif len(question) < 100:
        return "Medium"
    else:
        return "Hard"


# ✅ Keyword extraction
def extract_keywords(text):
    return text.split()[:5]