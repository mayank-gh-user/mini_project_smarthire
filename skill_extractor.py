import pdfplumber
import nltk
from nltk.corpus import stopwords
import string
import re

# We download stopwords if they aren't available locally
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

TECH_SKILLS = [
    "python", "java", "c++", "c#", "javascript", "typescript", "ruby", "php", "swift", "objective-c",
    "go", "rust", "kotlin", "scala", "html", "css", "sql", "nosql", "mongodb", "mysql", "postgresql",
    "oracle", "redis", "cassandra", "react", "angular", "vue.js", "node.js", "express", "django", "flask",
    "spring boot", "ruby on rails", "asp.net", "aws", "azure", "google cloud platform", "docker", "kubernetes",
    "jenkins", "git", "github", "gitlab", "jira", "agile", "scrum", "machine learning", "deep learning",
    "artificial intelligence", "data science", "data analytics", "pandas", "numpy", "scikit-learn", "tensorflow",
    "keras", "pytorch", "hadoop", "spark", "tableau", "power bi", "linux", "unix", "bash", "shell scripting",
    "rest api", "graphql", "microservices", "cybersecurity", "blockchain", "ui/ux", "figma", "adobe xd"
]

def extract_text_from_pdf(pdf_file_path):
    text = ""
    try:
        with pdfplumber.open(pdf_file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text

def preprocess_text(text):
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    text = re.sub(r'\s+', ' ', text).strip()
    
    words = text.split()
    try:
        stop_words = set(stopwords.words('english'))
        filtered_words = [word for word in words if word not in stop_words]
        return " ".join(filtered_words)
    except Exception:
        # Fallback if stopwords fail to load
        return " ".join(words)

def extract_skills(text):
    lower_text = text.lower()
    extracted = set()
    for skill in TECH_SKILLS:
        # Add word boundaries to avoid partial matches like 'go' in 'good'
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, lower_text):
            extracted.add(skill)
            
    return list(extracted)

def process_resume(pdf_file_path):
    text = extract_text_from_pdf(pdf_file_path)
    if not text:
        return []
    
    # Preprocessing is optional for rule-based matching, but good for standardization
    preprocessed = preprocess_text(text)
    
    # We can match on either original text or preprocessed. Let's match on original text
    # because preprocessing removes punctuation which might be part of the skill (like "c++", ".net").
    skills = extract_skills(text)
    return skills
