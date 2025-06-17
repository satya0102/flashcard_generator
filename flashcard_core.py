import io
import os
import json
import pandas as pd
from PyPDF2 import PdfReader
from transformers import T5Tokenizer, T5ForConditionalGeneration

def load_t5_model():
    """Loads the T5 model and tokenizer."""
    try:
        tokenizer = T5Tokenizer.from_pretrained("t5-small")
        model = T5ForConditionalGeneration.from_pretrained("t5-small")
        return tokenizer, model
    except Exception as e:
        print(f"Error loading model: {e}")
        print("Please ensure you have installed the 'transformers', 'torch', and 'PyPDF2' libraries.")
        return None, None

tokenizer, model = load_t5_model()

def extract_text_from_file(file_object, file_type):
    """Extract text from file-like object based on type"""
    if file_type == "application/pdf":
        try:
            pdf_reader = PdfReader(io.BytesIO(file_object.read()))
            text = ''.join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
            return text if text else None
        except Exception as e:
            print(f"PDF Error: {str(e)}")
            return None
    elif file_type == "text/plain":
        try:
            return file_object.read().decode('utf-8')
        except Exception as e:
            print(f"Text Error: {str(e)}")
            return None
    else:
        print(f"Unsupported file type: {file_type}")
        return None
    
def generate_flashcards_t5(text, subject=None):
    """Generate flashcards using a local T5 model"""
    if model is None or tokenizer is None:
        return None, "Model or tokenizer not loaded."

    if not text or len(text) < 100:
        return None, "Input text too short (minimum 100 characters required)"

    prompt_text = (
    f"Create 4 to 5 flashcards from the following {subject.lower() if subject != 'General' else ''} content. "
    f"Each flashcard should consist of a well-formed question and a concise, informative answer. "
    f"Use the format:\nQ: [question]\nA: [answer]\n\nContent:\n{text[:4000]}"
    )

    try:
        inputs = tokenizer(prompt_text, return_tensors="pt", max_length=512, truncation=True)

        outputs = model.generate(inputs["input_ids"], max_new_tokens=512, num_beams=4, early_stopping=True)
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return parse_flashcards(generated_text), None
    except Exception as e:
        return None, f"Model Generation Error: {str(e)}"

def parse_flashcards(text):
    """Parse Q/A pairs from generated text"""
    cards = []
    current_q = None

    lines = text.split('\n')
    # Handle single-line Q: A: pairs
    if ' Q:' in text and ' A:' in text and '\n' not in text.replace(' Q:', '').replace(' A:', ''):
         parts = text.split(' Q:')
         for part in parts:
             if ' A:' in part:
                 q_and_a = part.split(' A:', 1)
                 if len(q_and_a) == 2:
                     q = q_and_a[0].strip()
                     a = q_and_a[1].strip()
                     if q and a:
                         cards.append({'question': q, 'answer': a})
    else:
        # Parse line by line
        for line in lines:
            line = line.strip()
            if line.startswith('Q:'):
                current_q = line[2:].strip()
            elif line.startswith('A:') and current_q:
                answer = line[2:].strip()
                if current_q and answer:
                    cards.append({
                        'question': current_q,
                        'answer': answer
                    })
                current_q = None

    return cards