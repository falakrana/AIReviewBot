import requests
import zipfile
import os
import shutil

def create_sample_zip():
    project_dir = "tests/sample_project"
    zip_path = "tests/sample_project.zip"
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(project_dir):
            for file in files:
                zipf.write(os.path.join(root, file), 
                           os.path.relpath(os.path.join(root, file), project_dir))
    return zip_path

def test_analyze():
    zip_path = create_sample_zip()
    url = "http://localhost:8000/api/v1/analyze"
    
    files = {'file': open(zip_path, 'rb')}
    
    try:
        print("Sending request to /analyze...")
        response = requests.post(url, files=files)
        
        if response.status_code == 200:
            print("Successfully received response!")
            data = response.json()
            print(f"Session ID: {data['session_id']}")
            for result in data['results']:
                print(f"\nFile: {result['file']}")
                print(f"Summary: {result['summary']}")
                print(f"Details count: {len(result['details'])}")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Failed to connect: {e}")

if __name__ == "__main__":
    test_analyze()
