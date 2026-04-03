import json
import sys

def run_tests():
    try:
        from app import app
        app.testing = True
        client = app.test_client()

        print("Testing GET /jobs endpoint...")
        response = client.get('/jobs')
        
        if response.status_code == 200:
            data = json.loads(response.data)
            print(f"SUCCESS: Received 200 OK. Found {len(data['jobs'])} jobs.")
        else:
            print(f"FAIL: Expected 200 OK, got {response.status_code}")
            sys.exit(1)
            
        print("\nAll basic route tests passed. PDF Upload requires a valid PDF file for full testing.")
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
