# Movies API 2025 🎬

## 📘 Project Description

A high-performance, asynchronous REST API built with **FastAPI** (Python 3.10+). This project manages a movie database with actors' relations, 
featuring strict data validation and automated code quality tools.

---
## 🚀 Key Features

- **Asynchronous Database:** Powered by `aiosqlite` with WAL (Write-Ahead Logging) mode for enhanced concurrency.
- **Modular Architecture:** Organized using FastAPI Routers (Movies, Actors, Calculator, Geocode).
- **Strict Validation:** Data integrity ensured by **Pydantic v2** with custom field validators.
- **Security:** Built-in protection against special characters and data injections in API schemas.
- **Developer Friendly:** Automated formatting, linting, and type checking.

---

## 📂 Project Structure
├── main.py              # App entry point & Router registration  
├── routers/             # API Endpoints (Movies, Actors, etc.)  
├── database/            # Async connection & DB session logic  
├── schemas/             # Pydantic models & validation rules  
├── sql_queries/         # Raw SQL migration scripts  
├── tests/               # Unit and Integration tests  
├── exceptions           # Custom business exceptions (e.g., ActorNotFoundError)  
├── .coveragerc          # Coverage configuration  
└── .gitignore           # Ignored files (movies.db, .venv, .DS_Store)  


## 🛠 Tech Stack

- **Framework:** [FastAPI](fastapi.tiangolo.com)
- **Database:** SQLite (via [aiosqlite](aiosqlite.omnilib.dev))
- **Validation:** [Pydantic v2](docs.pydantic.dev)
- **Server:** [Uvicorn](www.uvicorn.org)
- **Code Quality:** Black, Flake8, Mypy, Coverage.py

---

## 📦 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone github.com
   cd MoviesAPI

## 🧪 Unit Testing

The project includes an extensive set of **unit tests** using [pytest](https://docs.pytest.org/).  
This is a comprehensive suite of asynchronous integration tests that verify the full CRUD lifecycle using pytest and direct database assertions. 
It leverages parameterized testing to efficiently validate edge cases, including input sanitization for XSS/SQL Injection and strict Pydantic schema enforcement. 
By utilizing a unified testing pattern, the suite ensures high code coverage and maintainability across multiple API endpoints and HTTP methods.

Run tests with:
```
pytest
```

If you want to generate data to a coverage report:
```
coverage run -m pytest
```
and generate console report
```
coverage report
```
or html report
```
coverage html
```
---
  
## 💻 Installation & Usage
### 1. Clone the repository
```
git clone https://github.com/bartoszkordek/MovieDBREST.git
cd MovieDBREST
```
### 2. Create and activate a virtual environment (optional but recommended)
```
python3 -m venv venv
source venv/bin/activate      # macOS/Linux
venv\Scripts\activate         # Windows
```
  
### 3. Install dependencies  

Before installing dependencies, make sure your virtual environment is activated.
```
pip install -r requirements.txt
```  
To uninstall all dependencies listed in `requirements.txt`, run:
```
pip uninstall -r requirements.txt -y
```
To list all installed packages, use:
```
pip freeze
```
You can also update your `requirements.txt` file with the current environment’s packages by running:
```
pip freeze > requirements.txt
```

Initialize the database:
(Optional: If you need to update database schema, the original schema attached in repo `movies-original.db`)
```
python sql_script_runner.py
```
  
### 4. Run unit tests
```
pytest
```
  
##  🖥 Running the Application
You can start the development server using the FastAPI CLI:
```
fastapi dev main.py
```
Alternatively, use Uvicorn directly:
```
uvicorn main:app --reload
```
---

## 📖 API Documentation
Once the server is running, the interactive documentation is available at:
**Swagger UI**: http://127.0.0.1:8000/docs

---

## 👤 Author
Bartosz Kordek
🐙 [GitHub profile](https://github.com/bartoszkordek/)

---

## 🪪 License
This project is released under the MIT License.
