import json
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer, util
from app.database import SessionLocal
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import declarative_base
from app.database import engine

# --- Database table for knowledge base ---
Base = declarative_base()

class KnowledgeBase(Base):
    __tablename__ = 'knowledge_base'
    id       = Column(Integer, primary_key=True)   # unique id
    category = Column(String)                       # career/interview/salary etc
    title    = Column(String)                       # document title
    content  = Column(Text)                         # document content

# --- Create table if not exists ---
Base.metadata.create_all(engine)

# --- Load sentence transformer model ---
model = SentenceTransformer('all-MiniLM-L6-v2')   # same model as career rec

# --- Knowledge base documents ---
KNOWLEDGE_BASE = [
    # Career Guides
    {"category": "career", "title": "How to become a Data Scientist",
     "content": "To become a Data Scientist: 1) Learn Python and SQL 2) Study statistics and mathematics 3) Learn machine learning with scikit-learn 4) Practice with real datasets on Kaggle 5) Learn data visualization with matplotlib and seaborn 6) Build 3-5 portfolio projects 7) Get certified in AWS or Azure 8) Apply for junior data analyst roles first. Average salary in India: 8-25 LPA. High demand in fintech, healthcare, e-commerce."},

    {"category": "career", "title": "How to become an ML Engineer",
     "content": "To become a Machine Learning Engineer: 1) Master Python, NumPy, Pandas 2) Learn ML algorithms deeply (regression, classification, clustering) 3) Study deep learning with TensorFlow or PyTorch 4) Learn MLOps tools: Docker, Kubernetes, MLflow 5) Practice on Kaggle competitions 6) Build end-to-end ML projects 7) Learn cloud ML services (AWS SageMaker, GCP Vertex AI) 8) Contribute to open source ML projects. Average salary in India: 10-30 LPA. Very high demand across all industries."},

    {"category": "career", "title": "How to become a Full Stack Developer",
     "content": "To become a Full Stack Developer: 1) Learn HTML, CSS, JavaScript 2) Master a frontend framework (React or Angular) 3) Learn backend with Node.js or Django or FastAPI 4) Learn databases: MySQL, PostgreSQL, MongoDB 5) Learn REST API development 6) Study Git and version control 7) Learn Docker for deployment 8) Build 3-5 full stack projects. Average salary in India: 5-22 LPA. High demand in startups and product companies."},

    {"category": "career", "title": "How to become a DevOps Engineer",
     "content": "To become a DevOps Engineer: 1) Learn Linux fundamentals 2) Master Git and version control 3) Learn CI/CD with Jenkins or GitHub Actions 4) Study Docker and Kubernetes 5) Learn cloud platforms (AWS, Azure, GCP) 6) Study infrastructure as code with Terraform 7) Learn monitoring tools (Prometheus, Grafana) 8) Get AWS or Kubernetes certifications. Average salary in India: 8-28 LPA. Very high demand in cloud-first companies."},

    {"category": "career", "title": "How to become a Cybersecurity Analyst",
     "content": "To become a Cybersecurity Analyst: 1) Learn networking fundamentals (TCP/IP, DNS, firewalls) 2) Study operating systems deeply (Linux, Windows) 3) Learn ethical hacking basics 4) Get CompTIA Security+ certification 5) Practice on HackTheBox or TryHackMe 6) Learn SIEM tools 7) Study incident response 8) Get CEH or CISSP certification. Average salary in India: 6-20 LPA. Very high demand due to increasing cyber threats."},

    {"category": "career", "title": "How to become a Cloud Engineer",
     "content": "To become a Cloud Engineer: 1) Learn Linux and networking 2) Study AWS or Azure or GCP fundamentals 3) Get cloud certifications (AWS Solutions Architect) 4) Learn infrastructure as code (Terraform, CloudFormation) 5) Study containerization (Docker, Kubernetes) 6) Learn monitoring and logging 7) Practice by building cloud projects 8) Learn cost optimization strategies. Average salary in India: 8-28 LPA. Excellent growth outlook."},

    # Skill Roadmaps
    {"category": "roadmap", "title": "Python learning roadmap",
     "content": "Python learning roadmap: Week 1-2: Basic syntax, variables, data types, loops, functions. Week 3-4: Object-oriented programming, file handling, modules. Month 2: Libraries: NumPy, Pandas, Matplotlib. Month 3: Web development with Flask or Django. Month 4: Data science with scikit-learn. Month 5-6: Deep learning with TensorFlow or PyTorch. Resources: freeCodeCamp Python course, Python.org documentation, Automate the Boring Stuff book. Practice: LeetCode easy problems, Kaggle notebooks."},

    {"category": "roadmap", "title": "Machine Learning learning roadmap",
     "content": "Machine Learning roadmap: Month 1: Python, NumPy, Pandas, Matplotlib. Month 2: Statistics and probability fundamentals. Month 3: Supervised learning (regression, classification). Month 4: Unsupervised learning (clustering, dimensionality reduction). Month 5: Deep learning basics (neural networks, CNNs). Month 6: NLP and computer vision. Month 7-8: MLOps, model deployment, Docker. Resources: Andrew Ng ML course on Coursera, fast.ai, Hands-on ML book by Aurelion Geron. Practice: Kaggle competitions, build 3 end-to-end projects."},

    {"category": "roadmap", "title": "Web Development learning roadmap",
     "content": "Web Development roadmap: Month 1: HTML, CSS, JavaScript basics. Month 2: React or Vue frontend framework. Month 3: Backend with Node.js or Python Django. Month 4: Databases SQL and NoSQL. Month 5: REST API design and development. Month 6: Docker, deployment, cloud basics. Resources: The Odin Project, freeCodeCamp, MDN Web Docs. Practice: Build a full stack project each month."},

    # Industry Trends
    {"category": "trends", "title": "AI and ML industry trends 2024",
     "content": "Top AI/ML trends: 1) Generative AI is the fastest growing field - prompt engineers earning 15-30 LPA 2) MLOps demand increased 300% - companies need engineers to deploy and monitor models 3) LLM fine-tuning skills are highly valued 4) Edge AI for IoT devices growing rapidly 5) AI in healthcare creating many opportunities 6) Responsible AI and ethics becoming important 7) Vector databases (Pinecone, Weaviate) are new skills to learn 8) AutoML reducing barrier to entry. India is becoming major AI hub with Google, Microsoft, Amazon expanding AI centers."},

    {"category": "trends", "title": "Cloud computing industry trends",
     "content": "Cloud computing trends: 1) Multi-cloud strategy adopted by 80% enterprises 2) Serverless computing growing fast 3) Cloud security skills highest paid 4) FinOps (cloud cost optimization) is new role 5) AWS still market leader but Azure growing fast in India due to Microsoft partnerships 6) Kubernetes becoming standard for all deployments 7) Platform engineering is emerging role 8) Cloud native development is new normal. Companies are migrating on-premise to cloud creating huge demand for cloud engineers in India."},

    {"category": "trends", "title": "Data Science industry trends",
     "content": "Data Science trends: 1) Data engineering is more in demand than data science currently 2) Real-time analytics replacing batch processing 3) DataOps practices becoming standard 4) Feature stores gaining adoption 5) Synthetic data generation for privacy 6) Causal AI beyond correlation 7) AutoML reducing manual model building 8) Data mesh architecture for large organizations. In India: fintech, edtech, healthtech hiring most data scientists. Startups offer equity, large companies offer stability."},

    # Certifications
    {"category": "certification", "title": "Top certifications for tech roles",
     "content": "Most valuable certifications in India 2024: Cloud: AWS Solutions Architect (highest ROI, 30-50% salary hike), Google Cloud Professional, Azure Administrator. Data: Google Data Analytics, IBM Data Science, Databricks. Security: CompTIA Security+, CEH, CISSP, OSCP. DevOps: Kubernetes CKA, AWS DevOps Professional, Terraform Associate. ML/AI: TensorFlow Developer, AWS ML Specialty, Google ML Engineer. Project Management: PMP, Scrum Master, SAFe Agile. Cost: AWS certs cost $150-300 USD. Preparation: 2-3 months of study. All available on Coursera, Udemy, official vendor sites."},

    # Company Information
    {"category": "company", "title": "Top tech companies hiring in India",
     "content": "Top tech companies hiring in India: Product companies (highest pay): Google, Microsoft, Amazon, Meta, Adobe, Uber, Flipkart, Swiggy, Razorpay. Service companies (volume hiring): TCS, Infosys, Wipro, HCL, Cognizant, Accenture, Capgemini. Startups (high growth, equity): Zepto, PhonePe, CRED, Meesho, BrowserStack, Postman. Salary ranges: FAANG India: 30-80 LPA. Product startups: 15-40 LPA. Service companies: 4-15 LPA. Interview difficulty: FAANG requires DSA preparation 3-6 months. Startups focus on practical projects. Service companies test basic programming."},

    {"category": "company", "title": "Amazon interview process",
     "content": "Amazon interview process: 1) Online Assessment: 2 coding problems (medium difficulty) + work simulation. 2) Phone Screen: 1 coding problem + 2 leadership principle questions. 3) Onsite (4-5 rounds): Each round has coding + leadership principles. Amazon Leadership Principles (LPs) to know: Customer Obsession, Ownership, Invent and Simplify, Are Right A Lot, Learn and Be Curious, Hire and Develop the Best, Insist on the Highest Standards, Think Big, Bias for Action, Frugality, Earn Trust, Dive Deep, Have Backbone, Deliver Results. Use STAR format for LP answers. DSA focus: Arrays, Trees, Graphs, Dynamic Programming."},

    {"category": "company", "title": "Google interview process",
     "content": "Google interview process: 1) Resume screening by recruiter. 2) Phone interview: 1-2 coding rounds (45 min each). 3) Onsite: 4-5 rounds including coding, system design, and Googleyness. Coding: LeetCode medium-hard, focus on optimal solutions, explain thought process. System Design: Design YouTube, Google Drive, URL shortener. Googleyness: Culture fit, leadership, teamwork. Preparation: 3-6 months of LeetCode practice, system design primer, mock interviews. Salary: SDE2 at Google India: 40-80 LPA including stocks. Tips: Communicate while coding, ask clarifying questions, start with brute force then optimize."},

    # Interview Questions - DSA
    {"category": "interview_dsa", "title": "Common DSA interview questions",
     "content": "Most common DSA questions in interviews: Arrays: Two Sum, Best Time to Buy Stock, Maximum Subarray (Kadane), Product of Array Except Self, Container With Most Water. Strings: Valid Anagram, Longest Substring Without Repeating Characters, Group Anagrams. Trees: Maximum Depth of Binary Tree, Invert Binary Tree, Lowest Common Ancestor, Binary Tree Level Order Traversal. Graphs: Number of Islands, Course Schedule, Clone Graph. Dynamic Programming: Climbing Stairs, House Robber, Coin Change, Longest Common Subsequence. Linked List: Reverse Linked List, Detect Cycle, Merge Two Sorted Lists. Practice on LeetCode: Do 100-150 problems before interviews."},

    # Interview Questions - HR
    {"category": "interview_hr", "title": "Common HR interview questions and answers",
     "content": "Common HR questions: 1) Tell me about yourself: Mention education, skills, projects, career goal in 2 minutes. 2) Why this company: Research company, mention specific product or culture. 3) Greatest strength: Pick relevant technical or leadership skill with example. 4) Greatest weakness: Mention real weakness but show improvement. 5) Where do you see yourself in 5 years: Show ambition aligned with company growth. 6) Why should we hire you: Connect your unique skills to role requirements. 7) Salary expectation: Research market rate, give range not fixed number. 8) Notice period: Be honest, mention if negotiable. Tips: Research company before interview, prepare 3-4 STAR stories, dress professionally."},

    # Interview Questions - ML
    {"category": "interview_ml", "title": "Common ML interview questions",
     "content": "Common ML interview questions: Basics: What is bias-variance tradeoff? Explain overfitting and underfitting. What is cross-validation? Difference between supervised and unsupervised learning? Algorithms: How does Random Forest work? Explain gradient boosting. What is SVM? When to use which algorithm? Deep Learning: What is backpropagation? Explain CNN architecture. What are activation functions? What is batch normalization? Practical: How do you handle imbalanced datasets? What is feature engineering? How do you evaluate a model? What metrics for classification vs regression? System Design: Design a recommendation system. Design a fraud detection system. How would you deploy an ML model to production? Prepare by implementing algorithms from scratch."},

    # Interview Questions - Python
    {"category": "interview_python", "title": "Common Python interview questions",
     "content": "Common Python interview questions: Basics: What is the difference between list and tuple? Explain Python decorators. What are generators? What is GIL? OOP: Explain inheritance in Python. What is polymorphism? What are dunder methods? What is MRO? Advanced: What is a closure? Explain list comprehension vs generator expression. What is the difference between deepcopy and copy? How does memory management work in Python? Libraries: How does Pandas handle missing values? What is vectorization in NumPy? Explain Pandas merge vs join. Practical: Write a decorator for timing functions. Implement a singleton pattern. Write a context manager. Tips: Practice on LeetCode with Python, know time complexity of Python operations."},

    # Salary Reports
    {"category": "salary", "title": "Indian tech salary report 2024",
     "content": "Indian tech salary report 2024: Entry level (0-2 years): Software Engineer 4-8 LPA, Data Analyst 3-6 LPA, DevOps 5-10 LPA. Mid level (3-5 years): Software Engineer 10-20 LPA, Data Scientist 10-18 LPA, ML Engineer 12-22 LPA. Senior level (6-10 years): Senior Engineer 20-35 LPA, Staff Engineer 30-50 LPA, Data Science Manager 25-40 LPA. Principal/Lead (10+ years): Principal Engineer 40-70 LPA, Engineering Manager 35-60 LPA, Director 60-100 LPA. Top paying companies: Google 40-80 LPA, Microsoft 30-60 LPA, Amazon 25-50 LPA, Flipkart 20-45 LPA. Cities: Bangalore highest paying, followed by Hyderabad, Pune, Chennai, Delhi NCR. Remote work increased salaries for tier-2 city candidates by 40-60%."},
]

# --- Embeddings cache ---
kb_embeddings = None
kb_texts = None

def build_kb_embeddings():
    global kb_embeddings, kb_texts
    # combine title + content for better matching
    kb_texts = [f"{doc['title']} {doc['content']}" for doc in KNOWLEDGE_BASE]
    kb_embeddings = model.encode(kb_texts, show_progress_bar=False)  # generate embeddings
    return kb_embeddings

# --- Search knowledge base for relevant documents ---
def search_knowledge_base(query: str, top_k: int = 3):
    global kb_embeddings, kb_texts

    if kb_embeddings is None:                          # build if not built yet
        build_kb_embeddings()

    # convert query to embedding
    query_embedding = model.encode([query])

    # calculate similarity with all documents
    similarities = util.cos_sim(query_embedding, kb_embeddings)[0]

    # get top k most similar documents
    top_indices = similarities.argsort(descending=True)[:top_k]

    results = []
    for idx in top_indices:
        idx = int(idx)
        results.append({
            "category": KNOWLEDGE_BASE[idx]['category'],
            "title":    KNOWLEDGE_BASE[idx]['title'],
            "content":  KNOWLEDGE_BASE[idx]['content'],
            "score":    round(float(similarities[idx]), 3)
        })

    return results

print("RAG system loaded successfully.")