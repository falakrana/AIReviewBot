# 🚀 AI Codebase Review System (MVP) - Setup Guide

Welcome to the backend implementation of your AI-based Codebase Review System. This MVP uses **FastAPI** for the API layer and **Tree-sitter** for intelligent code parsing.

## 🛠️ Prerequisites

Ensure you have Python 3.8+ installed. You will also need `pip`.

## 📦 Installation

1. **Install Poetry** (if not already installed):
   Follow instructions at [python-poetry.org](https://python-poetry.org/docs/#installation).

2. **Install Dependencies**:
   Run the following command to create a virtual environment and install dependencies:
   ```bash
   poetry install
   ```

3. **Tree-sitter Grammars**:
   The logic uses the `tree-sitter-python` and `tree-sitter-javascript` packages installed via Poetry.

## 🏃 Running the Application

Start the FastAPI server using `poetry run`:

```bash
poetry run python -m backend.app.main
```
The server will start at `http://localhost:8000`.

## 🧪 Testing the API

### 1. Simple Health Check
Visit `http://localhost:8000/` in your browser. You should see:
```json
{"message": "AI Codebase Review System API is running"}
```

### 2. Analyze a Project (ZIP Upload)
The main endpoint is `POST /api/v1/analyze`. It expects a ZIP file in the `file` field of a multi-part form.

#### Using Postman or cURL:
```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@sample_project.zip"
```

## 📁 Sample Project Structure
To test the system, create a ZIP file containing some `.py` or `.js` files. For example:

**example.py**:
```python
import os

def calculate_sum(a, b):
    # TODO: Add validation
    return a + b

class MyController:
    def process(self):
        try:
            print("Processing...")
        except:
            print("Error")
```

## 🧩 Module Breakdown
- **`main.py`**: Entry point, initializes FastAPI.
- **`analyzer_controller.py`**: Handles file uploads, extraction, and orchestrates the analysis flow.
- **`parser_service.py`**: The "brain" that uses Tree-sitter queries to extract functions and classes without regex or bulky ASTs.
- **`chunking_service.py`**: Splits the extracted data into manageable fragments for LLM analysis.
- **`analyzer_service.py`**: Mock service that simulates LLM logic to identify issues like bare excepts or long functions.
