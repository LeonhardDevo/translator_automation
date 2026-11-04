import os

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest-0123456789abcdef")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_translation_app.db")
