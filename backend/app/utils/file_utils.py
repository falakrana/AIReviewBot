import shutil
import zipfile
import os

def save_upload_file(upload_file, destination):
    with open(destination, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

def extract_zip(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

def cleanup_directory(directory_path):
    if os.path.exists(directory_path):
        shutil.rmtree(directory_path)
