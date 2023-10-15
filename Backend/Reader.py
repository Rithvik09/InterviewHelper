from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import spacy
import openai
import pdfplumber
from collections import Counter
import re

app = Flask(__name__)
CORS(app)

nlp = spacy.load('en_core_web_sm')
openai.api_key = ""

UPLOAD_FOLDER = 'uploaded_resumes'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        return ''.join(page.extract_text() or "" for page in pdf.pages)

def extract_skills(text):
    doc = nlp(text)
    skills = [ent.text for ent in doc.ents if ent.label_ in ["ORG", "PRODUCT", "LANGUAGE", "EDU", "WORK_OF_ART"]]
    skills.extend([token.text for token in doc if token.dep_ in ["dobj", "pobj", "attr"] and token.pos_ not in ["DET", "PRON", "CONJ"]])
    skills.extend([match.split(":")[1].split(", ") for match in re.findall(r'(?i)(\bskills?:\s*[^:\n]+)', text)])
    return list(Counter(skills))

def get_context(text, skill, window=5):
    words = text.split()
    if skill in words:
        index = words.index(skill)
        return ' '.join(words[max(0, index-window) : min(len(words), index+window+1)])
    return ""

def generate_questions_for_skill(skill, resume_text):
    context = get_context(resume_text, skill)
    try:
        response = openai.Completion.create(
            engine="text-davinci-002",
            prompt=f"Based on the context '{context}', generate a question about '{skill}'.",
            max_tokens=100
        )
        return response.choices[0].text.strip()
    except Exception:
        return None

@app.route('/generate_questions', methods=['POST'])
def generate_questions_endpoint():
    if 'resumes' not in request.files:
        return jsonify({"error": "No file part"}), 400

    uploaded_files = request.files.getlist("resumes")
    all_questions = {}

    for file in uploaded_files:
        filename = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(file.filename))
        file.save(filename)
        resume_text = extract_text_from_pdf(filename)
        skills = extract_skills(resume_text)
        questions = [generate_questions_for_skill(skill, resume_text) for skill in skills]
        all_questions[file.filename] = [q for q in questions if q]

    return jsonify(all_questions), 200

if __name__ == '__main__':
    app.run(port=5000)
