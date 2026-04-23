# AI Codebase Reviewer

An AI-powered codebase review system that analyzes uploaded project archives (.zip) using tree-sitter for parsing and Groq (Llama) for generating structured feedback on code quality. The application provides detailed insights on bugs, security issues, performance, and general suggestions.

## Features

- **Project Uploads**: Accepts `.zip` archives containing project source code.
- **Multi-language Support**: Parses Python, JavaScript, TypeScript, Java, C, and C++ files using `tree-sitter`.
- **Intelligent Chunking**: Intelligently chunks code by parsing functions and classes to stay within LLM context limits.
- **AI-Powered Analysis**: Utilizes Groq (Llama models) to identify bugs, security vulnerabilities, performance bottlenecks, and structural warnings.
- **Structured Feedback**: Returns granular JSON feedback aggregated per file.

## Tech Stack

- **Backend**: FastAPI, Python 3.12+
- **Parsing**: `tree-sitter`
- **AI Integration**: `groq` Python SDK
- **Dependency Management**: Poetry

## Prerequisites

- Python 3.12 or higher
- [Poetry](https://python-poetry.org/) installed
- Groq API Key

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/falakrana/AIReviewBot.git
   cd AIReviewBot
   ```

2. Install dependencies using Poetry:
   ```bash
   poetry install
   ```

3. Set up environment variables:
   Create a `.env` file in the root directory and add the following:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   MODEL_NAME=llama-3.1-8b-instant
   MAX_RETRIES=3
   RETRY_DELAY=2
   ```

## Usage

1. Start the FastAPI backend server:
   ```bash
   poetry run python ./backend/app/main.py
   ```
   By default, it will run on `http://127.0.0.1:8000`.

2. Test the API:
   Send a `POST` request to `/analyze` endpoint with a `.zip` file of your project:
   ```bash
   curl -X POST "http://127.0.0.1:8000/analyze" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@tests/sample_project.zip"
   ```

3. **API Documentation**:
   Visit `http://127.0.0.1:8000/docs` to view the interactive Swagger API documentation.

## Project Structure

- `backend/app/main.py`: Application entry point.
- `backend/app/routes/`: FastAPI controllers (e.g., `analyzer_controller.py`).
- `backend/app/services/`: Core business logic (`parser_service`, `chunking_service`, `analyzer_service`).
- `backend/app/models/`: Pydantic schemas for data validation.
- `backend/app/utils/`: Utility functions for file extraction and handling.
