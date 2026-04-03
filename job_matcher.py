import pandas as pd

def match_jobs(user_skills, jobs_csv_path='jobs.csv'):
    try:
        df = pd.read_csv(jobs_csv_path)
    except Exception as e:
        print(f"Error reading {jobs_csv_path}: {e}")
        return []

    user_skills_lower = set([skill.lower() for skill in user_skills])
    
    matched_jobs = []
    
    for index, row in df.iterrows():
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
                'Job ID': row.get('Job ID', index),
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
