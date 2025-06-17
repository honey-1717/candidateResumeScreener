import os
import secrets

# Application settings
SECRET_KEY = secrets.token_hex(16)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'data')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'doc'}

# API settings
GOOGLE_API_KEY ="AIzaSyC6KeNHx0RGMmKgX9G09UC6maAlV42dcM4"

# Gemini API settings
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent"
GEMINI_MODEL = "gemini-2.0-flash"

# Application configuration
MAX_CRITERIA = 8  # Maximum number of criteria to generate
PRIORITY_SCALE = 10  # 1-10 scale for priorities
MAX_RESUME_SIZE = 16 * 1024 * 1024  # 16MB max upload size

# File paths
DEFAULT_OUTPUT_DIR = os.path.join(UPLOAD_FOLDER, "results")
DEFAULT_JOB_DESCRIPTIONS_DIR = os.path.join(UPLOAD_FOLDER, "job_descriptions")
DEFAULT_RESUMES_DIR = os.path.join(UPLOAD_FOLDER, "resumes")

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FILE = os.path.join(BASE_DIR, "app.log")

# Debug mode (set to False in production)
DEBUG = True
