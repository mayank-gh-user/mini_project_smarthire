from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from skill_extractor import process_resume
from job_matcher import match_jobs
import pandas as pd

app = Flask(__name__)
# Enable CORS for cross-origin requests from the frontend
CORS(app)

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
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    # This will serve style.css, script.js, upload.html, results.html etc.
    if os.path.exists(path):
        return send_from_directory('.', path)
    return jsonify({"error": "Resource not found"}), 404

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
            
            # Match jobs based on extracted skills
            matched_jobs = match_jobs(skills, 'jobs.csv')
            
            return jsonify({
                'message': 'File processed successfully',
                'extracted_skills': skills,
                'matched_jobs': matched_jobs
            }), 200
            
        except Exception as e:
            # Handle possible errors during processing
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500
    else:
        return jsonify({'error': 'Invalid file type. Only PDF is allowed.'}), 400

@app.route('/jobs', methods=['GET'])
def get_jobs():
    try:
        # Load jobs from CSV
        df = pd.read_csv('jobs.csv')
        df = df.fillna('') # Handle any NaN values
        
        # Convert to a list of dicts for JSON response
        jobs_list = df.to_dict('records')
        return jsonify({'jobs': jobs_list}), 200
        
    except Exception as e:
        return jsonify({'error': f'Error retrieving jobs: {str(e)}'}), 500

if __name__ == '__main__':
    # Run the application
    app.run(debug=True, port=5000)
