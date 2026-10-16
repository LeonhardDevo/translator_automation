import pytest
from pathlib import Path
from app.utils.safe_translator import SafeTranslator

def test_safe_translator_security_rejection():
    code = "import os\nos.system(\"echo hacked\")"
    translator = SafeTranslator(api_keys=["fake-key"])
    output_path = Path("test_output.docx")
    success, error = translator._execute_code_safely(code, output_path)
    assert success is False
    assert "Import statements are not allowed" in error

def test_safe_translator_security_open_rejection():
    code = "with open(\"/etc/passwd\", \"r\") as f:\n    pass"
    translator = SafeTranslator(api_keys=["fake-key"])
    output_path = Path("test_output.docx")
    success, error = translator._execute_code_safely(code, output_path)
    assert success is False
    assert "Dangerous function call" in error
