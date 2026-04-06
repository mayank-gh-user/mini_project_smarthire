import pandas as pd

def match_jobs(user_skills, jobs_csv_path='jobs.csv'):
    from models import Job # Import here to avoid circular dependencies
    
    # Load jobs from CSV
    try:
        df = pd.read_csv(jobs_csv_path)
        csv_jobs = df.to_dict('records')
    except Exception as e:
        print(f"Error reading {jobs_csv_path}: {e}")
        csv_jobs = []

    # Get jobs from Database
    try:
        db_jobs_raw = Job.query.all()
        db_jobs = [{
            'Job ID': f"db_{j.id}",
            'Company': j.employer.company_name,
            'Role': j.role,
            'Required Skills': j.required_skills
        } for j in db_jobs_raw]
    except Exception as e:
        print(f"Error reading from DB: {e}")
        db_jobs = []

    all_jobs = csv_jobs + db_jobs
    user_skills_lower = set([skill.lower() for skill in user_skills])
    matched_jobs = []
    
    for row in all_jobs:
        req_skills_str = str(row.get('Required Skills', ''))
        req_skills = [s.strip().lower() for s in req_skills_str.split('|') if s.strip()]
        
        if not req_skills:
            continue
            
        req_skills_set = set(req_skills)
        matched = user_skills_lower.intersection(req_skills_set)
        missing = req_skills_set.difference(user_skills_lower)
        
        match_score = (len(matched) / len(req_skills_set)) * 100
        
        if match_score >= 40:
            matched_jobs.append({
                'Job ID': row.get('Job ID', 'N/A'),
                'Company': row.get('Company', 'Unknown'),
                'Role': row.get('Role', 'Unknown'),
                'Match Score': round(match_score, 2),
                'Matched Skills': list(matched),
                'Missing Skills': list(missing),
                'Required Skills Original': req_skills_str
            })
            
    # Sort descending by Match Score
    matched_jobs = sorted(matched_jobs, key=lambda x: x['Match Score'], reverse=True)
    
    # Return top 5
    return matched_jobs[:5]
def match_candidates(job_skills, resumes_list):
    """
    Matches a specific job's requirements against all stored resumes.
    job_skills: list of skills (e.g., ['python', 'flask'])
    resumes_list: list of dicts with 'filename' and 'skills'
    """
    job_skills_lower = set([s.lower() for s in job_skills])
    if not job_skills_lower:
        return []
        
    matched_candidates = []
    
    for resume in resumes_list:
        res_skills_lower = set([s.lower() for s in resume.get('skills', [])])
        
        matched_skills = job_skills_lower.intersection(res_skills_lower)
        match_score = (len(matched_skills) / len(job_skills_lower)) * 100
        
        if match_score > 0:
            matched_candidates.append({
                'id': resume.get('id'),
                'filename': resume.get('filename'),
                'match_score': round(match_score, 2),
                'matched_skills': list(matched_skills)
            })
            
    # Sort by match score descending
    matched_candidates = sorted(matched_candidates, key=lambda x: x['match_score'], reverse=True)
    return matched_candidates
