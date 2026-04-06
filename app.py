from flask import Flask, request, jsonify, send_from_directory, render_template, redirect, url_for, flash, session
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from skill_extractor import process_resume
from job_matcher import match_jobs, match_candidates
import pandas as pd
from models import db, Company, Job, Resume, Application
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

app = Flask(__name__)
# Enable CORS for cross-origin requests from the frontend
CORS(app)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///smarthire.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev_key_for_mini_project' # In production, use a secure key

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Company.query.get(int(user_id))

with app.app_context():
    db.create_all()

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16 MB max

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Serve the frontend
@app.route('/')
def serve_index():
    return render_template('index.html')

@app.route('/upload-resume')
def upload_page():
    return render_template('upload.html')

@app.route('/results')
def results_page():
    # Retrieve matching results from session
    extracted_skills = session.get('extracted_skills', [])
    matched_jobs = session.get('matched_jobs', [])
    return render_template('results.html', extracted_skills=extracted_skills, matched_jobs=matched_jobs)



@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        try:
            file.save(filepath)
            
            # Extract skills from the uploaded PDF
            skills = process_resume(filepath)
            
            # Save resume and skills to the database for company viewing
            skills_str = "|".join(skills)
            new_resume = Resume(filename=filename, extracted_skills=skills_str)
            db.session.add(new_resume)
            db.session.commit()
            
            # Match jobs based on extracted skills (combining DB and CSV jobs)
            matched_jobs = match_jobs(skills) 
            
            # Store in session for the results page
            session['extracted_skills'] = skills
            session['matched_jobs'] = matched_jobs
            
            return jsonify({
                'message': 'File processed successfully',
                'extracted_skills': skills,
                'matched_jobs': matched_jobs,
                'redirect': url_for('results_page')
            }), 200
            
        except Exception as e:
            # Handle possible errors during processing
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500
    else:
        return jsonify({'error': 'Invalid file type. Only PDF is allowed.'}), 400

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        company_name = request.form.get('company_name')
        
        if Company.query.filter_by(username=username).first():
            return "Username already exists", 400
            
        new_company = Company(username=username, company_name=company_name)
        new_company.set_password(password)
        db.session.add(new_company)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        company = Company.query.filter_by(username=username).first()
        
        if company and company.check_password(password):
            login_user(company)
            return redirect(url_for('company_dashboard'))
        return "Invalid username or password", 401
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('serve_index'))

@app.route('/company/dashboard')
@login_required
def company_dashboard():
    jobs = Job.query.filter_by(company_id=current_user.id).all()
    return render_template('company_dashboard.html', jobs=jobs)

@app.route('/company/add-job', methods=['GET', 'POST'])
@login_required
def add_job():
    if request.method == 'POST':
        role = request.form.get('role')
        required_skills = request.form.get('required_skills')
        description = request.form.get('description')
        
        new_job = Job(
            company_id=current_user.id,
            role=role,
            required_skills=required_skills,
            description=description
        )
        db.session.add(new_job)
        db.session.commit()
        return redirect(url_for('company_dashboard'))
    return render_template('add_job.html')

@app.route('/company/job/<int:job_id>/candidates')
@login_required
def job_candidates(job_id):
    job = Job.query.get_or_404(job_id)
    if job.company_id != current_user.id:
        return "Unauthorized", 403
        
    resumes = Resume.query.all()
    # Convert DB resumes to list for matching
    resumes_list = [{
        'id': r.id,
        'filename': r.filename,
        'skills': r.extracted_skills.split('|')
    } for r in resumes]
    
    job_skills = [s.strip() for s in job.required_skills.split('|') if s.strip()]
    matched_candidates = match_candidates(job_skills, resumes_list)
    
    return render_template('job_candidates.html', job=job, candidates=matched_candidates)

@app.route('/apply', methods=['POST'])
def apply_job():
    data = request.get_json()
    job_id = data.get('job_id')
    name = data.get('name')
    email = data.get('email')
    
    # In a real app, we might get the latest uploaded resume from the session
    # or link it back to a specific candidate profile.
    # For now, we'll try to find the most recent resume uploaded.
    latest_resume = Resume.query.order_by(Resume.uploaded_at.desc()).first()
    resume_filename = latest_resume.filename if latest_resume else "None"

    try:
        new_app = Application(
            job_id=job_id,
            candidate_name=name,
            candidate_email=email,
            resume_filename=resume_filename
        )
        db.session.add(new_app)
        db.session.commit()
        
        # Simulate Email to Candidate
        print(f"\n[EMAIL SIMULATION] To: {email}")
        print(f"Subject: Application Success - {job_id}")
        print(f"Body: Dear {name}, your application for {job_id} has been received. Redirecting your details and resume ({resume_filename}) to the company.\n")
        
        # Simulate Email to Company (Recruiter)
        # We need to find the company associated with this job if it's a DB job
        company_name = "the hiring company"
        if job_id.startswith('db_'):
            actual_id = int(job_id.split('_')[1])
            job = db.session.get(Job, actual_id) # Safer get for newest SQLAlchemy
            if job:
                company_name = job.employer.company_name
        
        print(f"[EMAIL SIMULATION] To Recruiter at {company_name}")
        print(f"Subject: New Application: {name}")
        print(f"Body: You have received a new application for your job posting. Candidate {name} ({email}) has submitted their resume: {resume_filename}\n")
        
        return jsonify({'message': 'Application submitted successfully! Check your console/logs for simulated emails.'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/jobs', methods=['GET'])
def get_jobs():
    try:
        # Combine CSV jobs and DB jobs for backward compatibility
        db_jobs = Job.query.all()
        db_jobs_list = [{
            'Job ID': f"db_{j.id}",
            'Company': j.employer.company_name,
            'Role': j.role,
            'Required Skills': j.required_skills
        } for j in db_jobs]
        
        try:
            df = pd.read_csv('jobs.csv')
            csv_jobs = df.to_dict('records')
        except:
            csv_jobs = []
            
        return jsonify({'jobs': csv_jobs + db_jobs_list}), 200
        
    except Exception as e:
        return jsonify({'error': f'Error retrieving jobs: {str(e)}'}), 500

if __name__ == '__main__':
    # Run the application
    app.run(debug=True, port=5000)
