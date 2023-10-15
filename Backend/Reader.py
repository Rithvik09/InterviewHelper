from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import spacy
import openai
import pdfplumber
from collections import Counter
import re

nlp = spacy.load('en_core_web_sm')
openai.api_key = ""

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploaded_resumes'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def extract_skills(text):
    skills = []
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ in ["ORG", "PRODUCT", "LANGUAGE", "EDU", "WORK_OF_ART"]:
            skills.append(ent.text)
    
    for token in doc:
        if token.dep_ in ["dobj", "pobj", "attr"] and token.pos_ not in ["DET", "PRON", "CONJ"]:
            skills.append(token.text)
    
    skill_section_pattern = re.compile(r'(?i)(\bskills?:\s*[^:\n]+)')
    matches = skill_section_pattern.findall(text)
    for match in matches:
        skills_list = match.split(":")[1].split(", ")
        skills.extend(skills_list)
        
    return list(Counter(skills))

def get_context(text, skill, window=5):
    words = text.split()
    if skill not in words:
        return ""
    index = words.index(skill)
    start = max(0, index - window)
    end = min(len(words), index + window + 1)
    context = " ".join(words[start:end])
    return context

def generate_questions(skills, resume_text):
    questions = []
    for skill in skills:
        try:
            context = get_context(resume_text, skill)
            response = openai.Completion.create(
                engine="text-davinci-002",
                prompt=f"Based on the context '{context}', what questions would you ask in an interview if their resume talks about '{skill}'?",
                max_tokens=100
            )
            questions.append(response.choices[0].text.strip())
        except Exception as e:
            print(f"Failed to generate question for skill {skill}. Error: {e}")
    return questions

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
        questions = generate_questions(skills, resume_text)
        all_questions[file.filename] = questions

    return jsonify(all_questions), 200

if __name__ == '__main__':
    app.run(port=5000)
