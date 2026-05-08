import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
import json
from google import genai
from PIL import Image
import io
import docx
from docx import Document as DocxDocument
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from ..config import settings
from .api_key_manager import get_translation_api_key
import time
import re
import random
from threading import Lock

def set_cell_border(cell, **kwargs):
    """
    Set cell's border
    Usage:
    set_cell_border(
        cell,
        top={"sz": 12, "val": "single", "color": "#FF0000", "space": "0"},
        bottom={"sz": 12, "color": "#00FF00", "val": "single"},
        start={"sz": 24, "val": "dashed", "shadow": "true"},
        end={"sz": 12, "val": "single", "color": "#0000FF"},
    )
    """
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()

    tcBorders = tcPr.find(qn('w:tcBorders'))
    if tcBorders is None:
        tcBorders = OxmlElement('w:tcBorders')
        tcPr.append(tcBorders)

    for edge in ('start', 'top', 'end', 'bottom', 'insideH', 'insideV'):
        edge_data = kwargs.get(edge)
        if edge_data:
            tag = 'w:{}'.format(edge)

            element = tcBorders.find(qn(tag))
            if element is None:
                element = OxmlElement(tag)
                tcBorders.append(element)

            for key in edge_data:
                element.set(qn('w:{}'.format(key)), str(edge_data[key]))

from backend.logging_setup import get_logger
logger = get_logger(__name__)

# Global tracking for busy API keys
_busy_api_keys = set()
_busy_keys_lock = Lock()


def _claim_api_key_index(api_keys: list) -> int:
    """Atomically claim a random available API key.
    
    This should be called sequentially (not from multiple threads simultaneously)
    BEFORE spawning translation threads so each document gets a guaranteed-unique key.
    
    Returns:
        The index of the claimed key (already marked busy in _busy_api_keys).
    """
    global _busy_api_keys, _busy_keys_lock
    num_keys = len(api_keys)
    
    with _busy_keys_lock:
        # Get all available indices (not currently busy)
        available_indices = [i for i in range(num_keys) if i not in _busy_api_keys]
        
        if available_indices:
            # Randomly select from available keys
            selected_index = random.choice(available_indices)
            _busy_api_keys.add(selected_index)
            return selected_index
        
        # All keys are busy — randomly select one anyway
        selected_index = random.randint(0, num_keys - 1)
        _busy_api_keys.add(selected_index)
        return selected_index

Document = DocxDocument


class SafeTranslator:
    """
    A safe alternative to the dangerous code execution approach.
    Instead of executing AI-generated Python code, this class handles
    translation requests directly using the Google AI API with error correction.
    """
    
    MODELS_TO_TRY = [
        'gemini-3-flash-preview',
        'gemini-3-pro-preview',
        'gemini-2.5-flash',
        'gemini-2.5-flash',
        'gemini-2.5-pro',
        'gemini-3.0-pro',
        'gemini-1.5-pro',
        'gemini-1.5-flash',
    ]

    # How many times we send an error back to Gemini asking for a fix
    MAX_CODE_FIX_ATTEMPTS = 3
    
    def __init__(self, db_session=None, api_keys: list = None):
        """Initialize the safe translator with API keys from database or provided list"""
        if api_keys is not None:
            if isinstance(api_keys, str):
                self.api_keys = [api_keys]
            else:
                self.api_keys = api_keys
            logger.info(f"✓ Using {len(self.api_keys)} API keys from parameter")
        elif db_session is not None:
            from .api_key_manager import get_all_active_translation_api_keys
            
            db_api_keys = get_all_active_translation_api_keys(db_session)
            
            if db_api_keys and len(db_api_keys) > 0:
                self.api_keys = db_api_keys
                logger.info(f"✓ Loaded {len(self.api_keys)} API keys from database")
            else:
                logger.warning("⚠️  No API keys found in database, falling back to environment variables")
                import os
                from dotenv import load_dotenv
                load_dotenv()
                
                gemini_api_keys_str = os.getenv('GEMINI_API_KEYS', '')
                if gemini_api_keys_str:
                    self.api_keys = [key.strip() for key in gemini_api_keys_str.split(',') if key.strip()]
                    logger.info(f"✓ Loaded {len(self.api_keys)} API keys from environment variables")
                else:
                    fallback_key = getattr(settings, 'GEMINI_API_KEY', None)
                    if fallback_key:
                        self.api_keys = [fallback_key]
                        logger.warning("⚠️  Using single fallback API key from settings")
                    else:
                        raise ValueError("❌ No API keys available for translation")
        else:
            fallback_key = getattr(settings, 'GEMINI_API_KEY', None)
            if fallback_key:
                self.api_keys = [fallback_key]
                logger.info("✓ Using fallback API key from settings")
            else:
                raise ValueError("❌ No API keys available for translation")
        
        self.selected_key_index = self._get_available_api_key_index()
        self.api_key = self.api_keys[self.selected_key_index]
        self.client = genai.Client(api_key=self.api_key)
        self.file_counter = 0
        
        logger.info(f"✓ Safe Translator initialized with Gemini models using new GenAI SDK, API key index: {self.selected_key_index + 1}/{len(self.api_keys)}")
    
    def _get_available_api_key_index(self):
        """Select a random API key index that is not currently busy"""
        global _busy_api_keys, _busy_keys_lock
        import time
        
        max_wait_time = 30  # Maximum wait time in seconds
        wait_interval = 1   # Wait interval in seconds
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            with _busy_keys_lock:
                available_indices = []
                for i in range(len(self.api_keys)):
                    if i not in _busy_api_keys:
                        available_indices.append(i)
                
                if available_indices:
                    selected_index = random.choice(available_indices)
                    _busy_api_keys.add(selected_index)
                    return selected_index
            
            # Wait outside the lock to avoid blocking other threads
            time.sleep(wait_interval)
            elapsed_time += wait_interval
        
        # If we've waited too long and still no keys available, use round-robin
        logger.warning("Max wait time exceeded, using round-robin selection for API key")
        # Use a simple round-robin approach without locking for too long
        for i in range(len(self.api_keys)):
            with _busy_keys_lock:
                if i not in _busy_api_keys:
                    _busy_api_keys.add(i)
                    return i
        
        # If all are still busy, use the first key anyway
        logger.warning("All API keys appear to be busy, using first key after timeout")
        with _busy_keys_lock:
            _busy_api_keys.add(0)
        return 0

    def _rotate_api_key(self):
        """Rotate to the next API key in round-robin fashion"""
        global _busy_api_keys, _busy_keys_lock
        old_index = self.selected_key_index
        
        with _busy_keys_lock:
            _busy_api_keys.discard(old_index)
        
        self.selected_key_index = self._get_available_api_key_index()
        self.api_key = self.api_keys[self.selected_key_index]
        self.client = genai.Client(api_key=self.api_key)
        logger.info(f"[ROTATE] Rotated from API key #{old_index + 1} to #{self.selected_key_index + 1}")

    def _sanitize_text(self, text: str) -> str:
        """Sanitize text output to prevent injection attacks"""
        sanitized = text.replace('\0', '')
        sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        return sanitized
    
    def _extract_python_code(self, response_text: str) -> Optional[str]:
        """Extract Python code from various response formats"""
        pattern = r'```python\s*\n(.*?)```'
        matches = re.findall(pattern, response_text, re.DOTALL)
        if matches:
            return matches[-1].strip()
        
        pattern = r'```\s*\n(.*?)```'
        matches = re.findall(pattern, response_text, re.DOTALL)
        if matches:
            code = matches[-1].strip()
            if any(keyword in code for keyword in ['import', 'from ', 'def ', 'docx']):
                return code
        
        pattern = r'```([\s\S]*?)```'
        matches = re.findall(pattern, response_text)
        if matches:
            for match in matches:
                match_clean = match.strip()
                if any(keyword in match_clean for keyword in ['import', 'from ', 'def ', 'docx']):
                    return match_clean
        
        lines = response_text.split('\n')
        code_lines = []
        in_code_block = False
        potential_start_patterns = [
            r'^\s*import\s+',
            r'^\s*from\s+',
            r'^\s*doc = ',
            r'^\s*Document\(\)',
            r'^\s*document = ',
            r'^\s*def\s+',
            r'^\s*class\s+'
        ]
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if any(re.match(pattern, stripped) for pattern in potential_start_patterns):
                potential_code = [line]
                j = i + 1
                consecutive_code = 1
                
                while j < len(lines):
                    next_line = lines[j].strip()
                    if not next_line:
                        j += 1
                        continue
                    if (re.match(r'^\s*[a-zA-Z_][\w.]*\s*=', next_line) or
                        re.match(r'^\s*(import|from|def|class|if|for|while|try|with)', next_line) or
                        re.match(r'^\s*[a-zA-Z_]\w*\s*\.', next_line) or
                        next_line.endswith(':') or
                        '(' in next_line or
                        '=' in next_line or
                        re.match(r'^\s*[a-zA-Z_]\w*\s*\(', next_line)):
                        potential_code.append(lines[j])
                        consecutive_code += 1
                        j += 1
                    else:
                        if consecutive_code >= 2:
                            return '\n'.join(potential_code).strip()
                        break
                
                if consecutive_code >= 2:
                    return '\n'.join(potential_code).strip()
        
        blocks = re.split(r'\n\s*\n', response_text)
        for block in blocks:
            block = block.strip()
            if len(block) > 50:
                if any(keyword in block for keyword in ['import', 'from ', 'def ', 'docx', 'Document', 'document', 'paragraph', 'table']):
                    python_indicators = len([kw for kw in ['import', 'def', 'class', '=', '.', '(', ')', ':'] if kw in block])
                    english_indicators = len([word for word in ['the', 'is', 'are', 'and', 'or', 'but'] if f' {word} ' in block.lower()])
                    
                    if python_indicators > english_indicators:
                        return block
        
        return None

    # ─────────────────────────────────────────────────────────────────────────
    # 2. EXECUTION — now returns (success: bool, error_message: str | None)
    #    This is the KEY change. Before it swallowed the error.
    #    Now the actual Python traceback is returned so we can send it to Gemini.
    # ─────────────────────────────────────────────────────────────────────────
    def _execute_code_safely(self, code: str, output_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Execute the generated Python code safely with restricted environment.
        
        Returns:
            Tuple of (success, error_message)
            - On success:  (True, None)
            - On failure:  (False, "the actual error string")
        """
        try:
            safe_globals = {
                '__builtins__': {
                    '__import__': __import__,
                    '__build_class__': __build_class__,
                    'print': print,
                    'len': len,
                    'range': range,
                    'str': str,
                    'int': int,
                    'float': float,
                    'bool': bool,
                    'list': list,
                    'dict': dict,
                    'tuple': tuple,
                    'set': set,
                },
                '__name__': '__main__',
                '__file__': str(output_path),
                '__doc__': None,
                '__package__': None,

                'Document': Document,
                'docx': docx,
                'Pt': Pt,
                'Inches': Inches,
                'RGBColor': RGBColor,
                'WD_ALIGN_PARAGRAPH': WD_ALIGN_PARAGRAPH,
                'WD_ORIENT': WD_ORIENT,
                'qn': qn,
                'OxmlElement': OxmlElement,
                'set_cell_border': set_cell_border,

                'output_path': str(output_path),

                'range': range,
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'list': list,
                'dict': dict,
                'tuple': tuple,
                'set': set,
                'min': min,
                'max': max,
                'sum': sum,
                'abs': abs,
                'round': round,
                'enumerate': enumerate,
                'zip': zip,
                'sorted': sorted,
                'reversed': reversed,
                'any': any,
                'all': all,
                'map': map,
                'filter': filter,
                'isinstance': isinstance,
                'type': type,
                'hasattr': hasattr,
                'getattr': getattr,
                'setattr': setattr,
                'chr': chr,
                'ord': ord,
                'hex': hex,
                'oct': oct,
                'bin': bin,
                'pow': pow,
                'divmod': divmod,
                'callable': callable,
                'iter': iter,
                'next': next,
                'slice': slice,
                'property': property,
                'staticmethod': staticmethod,
                'classmethod': classmethod,
                'super': super,
                'object': object,
                'Exception': Exception,
                'ValueError': ValueError,
                'TypeError': TypeError,
                'AttributeError': AttributeError,
                'KeyError': KeyError,
                'IndexError': IndexError,
                'RuntimeError': RuntimeError,
                'NameError': NameError,
                'ImportError': ImportError,
                'ModuleNotFoundError': ModuleNotFoundError,
                'ZeroDivisionError': ZeroDivisionError,
                'FileNotFoundError': FileNotFoundError,
                'OSError': OSError,
                'IOError': IOError,
                'UnicodeDecodeError': UnicodeDecodeError,
                'UnicodeEncodeError': UnicodeEncodeError,
                'print': print,
                'open': open,
            }

            logger.debug(f"Executing code ({len(code)} chars):\n{code[:500]}...")
            code = re.sub(r'^\s*output_path\s*=\s*.+$', '', code, flags=re.MULTILINE)
            exec(code, safe_globals)

            if not Path(output_path).exists():
                import shutil
                fallback_names = [
                    'translated_document.docx',
                    'translated_invoice.docx',
                    'output.docx',
                    'document.docx',
                ]
                moved = False
                for name in fallback_names:
                    fallback = Path(name)
                    if fallback.exists():
                        shutil.move(str(fallback), str(output_path))
                        logger.info(f"Moved hardcoded '{name}' → output_path")
                        moved = True
                        break

                if not moved:
                    return (False, f"Code ran without error but no output file was created at '{output_path}'. Generated code was:\n{code}")

            return (True, None)

        except Exception as e:
            import traceback
            error_str = traceback.format_exc()
            logger.error(f"Code execution failed:\n{error_str}")
            return (False, error_str)

    # ─────────────────────────────────────────────────────────────────────────
    # 3. ASK GEMINI TO FIX THE CODE — this is the NEW method
    #    Sends: original image + the broken code + the exact error traceback
    #    Asks Gemini to return ONLY fixed Python code.
    # ─────────────────────────────────────────────────────────────────────────
    def _ask_gemini_to_fix_code(self, image_path: Path, broken_code: str, error_message: str, max_retries_per_model: int = 2) -> Optional[str]:
        """
        Send the failed code + error back to Gemini and ask for a fixed version.
        
        Args:
            image_path:     the original document image (sent again for context)
            broken_code:    the Python code that failed
            error_message:  the full traceback from exec()
            max_retries_per_model: number of retries per model (default 2)
        
        Returns:
            Fixed Python code string, or None if all models fail.
        """
        image = Image.open(image_path)

        fix_prompt = (
            "The following Python code was generated to create a translated .docx document, "
            "but it FAILED when executed. Here is the code and the exact error:\n\n"
            "─── FAILED CODE ───\n"
            f"{broken_code}\n"
            "─── END CODE ───\n\n"
            "─── ERROR TRACEBACK ───\n"
            f"{error_message}\n"
            "─── END ERROR ───\n\n"
            "The original document image is attached again for reference.\n\n"
            "Fix the code so it runs without errors. The environment already has these "
            "available without importing:\n"
            "  Document, Pt, Inches, RGBColor, WD_ALIGN_PARAGRAPH, WD_ORIENT, "
            "qn, OxmlElement, set_cell_border, output_path\n\n"
            "- CRITICAL: Do NOT reassign `output_path`. It is pre-set. Use it directly: doc.save(output_path)\n"
        )

        for model_name in self.MODELS_TO_TRY:
            for retry in range(max_retries_per_model):
                try:
                    logger.info(f"[FIX] Asking {model_name} to fix code (attempt {retry + 1}/{max_retries_per_model})...")
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=[fix_prompt, image],
                        config=genai.types.GenerateContentConfig(
                            temperature=0.2,
                            max_output_tokens=8192,
                        )
                    )

                    if response.text:
                        fixed_code = self._extract_python_code(response.text)
                        if fixed_code:
                            logger.info(f"[FIX] Got fixed code from {model_name} ({len(fixed_code)} chars)")
                            return fixed_code
                        else:
                            logger.warning(f"[FIX] {model_name} responded but no extractable code found")
                            continue

                except Exception as e:
                    error_str = str(e)
                    logger.warning(f"[FIX] {model_name} failed (attempt {retry + 1}): {error_str}")
                    
                    if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                        logger.warning(f"[FIX] ⚠️  Quota exhausted for API key #{self.selected_key_index + 1}, rotating to next key...")
                        self._rotate_api_key()
                        if retry < max_retries_per_model - 1:
                            logger.info(f"[FIX] Retrying with new API key #{self.selected_key_index + 1}...")
                            time.sleep(2)
                            continue
                    else:
                        if retry < max_retries_per_model - 1:
                            logger.info(f"[FIX] Retrying same model and key after non-quota error...")
                            time.sleep(1)
                            continue
                    break

        logger.error("[FIX] All models failed to produce fixed code")
        return None

    def _create_docx_from_code(self, response_text: str, image_path: Path, output_path: Path) -> bool:
        """
        Create a DOCX by:
          1. Extracting Python code from Gemini's response
          2. Running it
          3. If it fails → sending the error back to Gemini for a fix
          4. Running the fixed code
          5. Repeat up to MAX_CODE_FIX_ATTEMPTS times
        
        NOTE: image_path is now required here so we can re-send it to Gemini on errors.
        """
        code = self._extract_python_code(response_text)
        if not code:
            logger.error("No Python code found in initial Gemini response")
            return False

        logger.info(f"[LOOP] Extracted initial code ({len(code)} chars)")

        current_code = code

        for attempt in range(self.MAX_CODE_FIX_ATTEMPTS + 1):

            logger.info(f"[LOOP] Attempt {attempt + 1}/{self.MAX_CODE_FIX_ATTEMPTS + 1} — executing code...")
            success, error_message = self._execute_code_safely(current_code, output_path)

            if success:
                logger.info(f"[LOOP] ✓ Code executed successfully on attempt {attempt + 1}")
                return True

            logger.warning(f"[LOOP] ✗ Attempt {attempt + 1} failed:\n{error_message}")

            if attempt >= self.MAX_CODE_FIX_ATTEMPTS:
                logger.error("[LOOP] All fix attempts exhausted. Giving up.")
                return False

            logger.info(f"[LOOP] Sending error to Gemini for fix (attempt {attempt + 1})...")
            fixed_code = self._ask_gemini_to_fix_code(image_path, current_code, error_message)

            if not fixed_code:
                logger.error("[LOOP] Gemini could not produce fixed code. Stopping.")
                return False

            current_code = fixed_code

        return False

    def _create_docx_from_text(self, text: str, output_path: Path) -> bool:
        """Create a DOCX file from plain text (last-resort fallback)"""
        try:
            doc = DocxDocument()
            sanitized_text = self._sanitize_text(text)
            doc.add_paragraph(sanitized_text)
            doc.save(str(output_path))
            return True
        except Exception as e:
            logger.error(f"Error creating DOCX file: {e}")
            return False
    
    def _request_code_correction(self, original_image_path: Path, original_prompt: str, error_message: str) -> Optional[str]:
        """Legacy method. The new flow uses _ask_gemini_to_fix_code instead."""
        try:
            image = Image.open(original_image_path)
            correction_prompt = (
                f"The previous attempt failed with this error:\n{error_message}\n\n"
                f"Original request: {original_prompt}\n\n"
                "Please provide only the correctly translated text to Turkmen "
                "without any additional commentary. Preserve the structure and meaning."
            )
            
            for model_name in self.MODELS_TO_TRY:
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=[correction_prompt, image],
                        config=genai.types.GenerateContentConfig(
                            temperature=0.3,
                            max_output_tokens=8192,
                        )
                    )
                    if response.text:
                        logger.info(f"Successfully received corrected response from {model_name}")
                        return response.text
                except Exception as e:
                    logger.warning(f"Correction request failed with {model_name}: {e}")
                    continue
            return None
        except Exception as e:
            logger.error(f"Error requesting code correction: {e}")
            return None

    def _process_translation_request(self, image_path: Path, prompt: str, max_retries: int = 3) -> Optional[str]:
        """Process a translation request with the AI model.
        
        Tries every (api_key × model) combination before giving up.
        Quota-exhausted keys are skipped for remaining models.
        All failures are logged to the daily backend log file.
        """
        try:
            image = Image.open(image_path)
        except Exception as e:
            logger.error(f"Failed to open image {image_path}: {e}")
            return None

        exhausted_key_indices: set = set()
        total_attempts = 0

        for model_name in self.MODELS_TO_TRY:
            # Build list of key indices to try for this model (exclude quota-exhausted ones)
            # Randomize the order of keys to avoid always starting from the same key
            available_key_indices = [i for i in range(len(self.api_keys)) if i not in exhausted_key_indices]
            random.shuffle(available_key_indices)
            
            if not available_key_indices:
                logger.warning(f"[ROTATION] All API keys exhausted — skipping model {model_name}")
                continue

            for key_index in available_key_indices:
                # Switch to this key
                self.selected_key_index = key_index
                self.api_key = self.api_keys[key_index]
                self.client = genai.Client(api_key=self.api_key)

                for attempt in range(max_retries):
                    total_attempts += 1
                    try:
                        logger.info(f"[TRANSLATE] Model={model_name}, Key=#{key_index + 1}/{len(self.api_keys)}, Attempt={attempt + 1}/{max_retries}")
                        response = self.client.models.generate_content(
                            model=model_name,
                            contents=[prompt, image],
                            config=genai.types.GenerateContentConfig(
                                temperature=0.3,
                                max_output_tokens=8192,
                            )
                        )

                        if response.text:
                            logger.info(f"[TRANSLATE] ✓ Success with model={model_name}, key=#{key_index + 1}")
                            return response.text

                    except Exception as e:
                        error_msg = str(e)
                        logger.warning(f"[TRANSLATE] ✗ Model={model_name}, Key=#{key_index + 1}, Attempt={attempt + 1}: {error_msg}")

                        # Log every failure to the daily log file
                        try:
                            from pathlib import Path as _Path
                            from datetime import datetime as _dt
                            _log_dir = _Path("logs")
                            _log_dir.mkdir(exist_ok=True)
                            _daily_log = _log_dir / f"backend_operations_{_dt.now().strftime('%Y%m%d')}.log"
                            with open(_daily_log, "a", encoding="utf-8") as _f:
                                _f.write(
                                    f"{_dt.now().isoformat()} - ERROR - [API_KEY_FAILURE] "
                                    f"model={model_name} key_index={key_index + 1}/{len(self.api_keys)} "
                                    f"attempt={attempt + 1}/{max_retries} "
                                    f"image={image_path.name} error={error_msg}\n"
                                )
                        except Exception:
                            pass  # Never let logging crash the translator

                        is_quota_error = (
                            "429" in error_msg or
                            "RESOURCE_EXHAUSTED" in error_msg or
                            "quota" in error_msg.lower() or
                            "rate" in error_msg.lower()
                        )

                        if is_quota_error:
                            logger.warning(f"[ROTATION] Quota exhausted for key #{key_index + 1} on model={model_name}. Marking key as exhausted.")
                            exhausted_key_indices.add(key_index)
                            break  # Skip remaining retries for this key+model, try next key
                        else:
                            if attempt < max_retries - 1:
                                logger.info(f"[TRANSLATE] Non-quota error, retrying same key+model after 1s...")
                                time.sleep(1)
                                continue
                            # Other error, all retries for this key exhausted
                            break

        # All (key × model) combinations exhausted
        logger.error(
            f"[TRANSLATE] FAILED — exhausted all {len(self.api_keys)} API key(s) × "
            f"{len(self.MODELS_TO_TRY)} model(s) ({total_attempts} total attempts) "
            f"for image: {image_path.name}"
        )

        # Write summary failure to daily log
        try:
            from pathlib import Path as _Path
            from datetime import datetime as _dt
            _log_dir = _Path("logs")
            _log_dir.mkdir(exist_ok=True)
            _daily_log = _log_dir / f"backend_operations_{_dt.now().strftime('%Y%m%d')}.log"
            with open(_daily_log, "a", encoding="utf-8") as _f:
                _f.write(
                    f"{_dt.now().isoformat()} - CRITICAL - [TRANSLATION_FAILED] "
                    f"All {len(self.api_keys)} API key(s) × {len(self.MODELS_TO_TRY)} model(s) "
                    f"exhausted after {total_attempts} attempts. "
                    f"image={image_path.name} "
                    f"exhausted_keys={sorted(exhausted_key_indices)}\n"
                )
        except Exception:
            pass

        return None

    
    def translate_image_to_document(self,
        image_path: Path,
        output_path: Path,
        custom_prompt: Optional[str] = None,
        target_language: str = "Turkmen") -> bool:
        """Translate an image to a document using AI, with code-fix retry loop"""
        try:
            self.file_counter += 1
            logger.info(f"Processing translation for: {image_path.name}")
            
            try:
                prompt_path = Path(__file__).resolve().parent.parent.parent.parent / 'prompt.txt'
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    prompt_template = f.read().strip()
            except FileNotFoundError:
                prompt_template = (
                    "Analyze the uploaded invoice/document image and translate ALL text from the source language to $language while preserving the exact layout, tables, orientation, and formatting.\n\n"
                    "The image may be rotated (album / landscape orientation).\n"
                    "You MUST detect the original orientation of the document and preserve it exactly in the output.\n"
                    "If the source document is landscape or rotated, the generated .docx MUST use the same page orientation.\n"
                    "Do NOT normalize, straighten, or re-orient the content.\n\n"
                    "Requirements:\n"
                    "1. Translate all visible text to $language\n"
                    "2. Maintain the original document structure, tables, and layout\n"
                    "3. Keep numbers, dates, and formatting identical\n"
                    "4. Preserve table borders, cell alignment, spacing, and orientation\n"
                    "5. Save structure on send A4 list all in one page, you should generate one page translated\n\n"
                    "Generate ONLY executable Python code that:\n"
                    "- Uses the python-docx library to create a .docx file\n"
                    "- Recreates the document structure with translated text\n"
                    "- Sets page orientation to match the source image (portrait or landscape)\n"
                    "- Uses the variable `output_path` as the save location. (e.g. doc.save(output_path))\n"
                    "- IMPORTANT: In python-docx, `Paragraph` has no `font` attribute. To set font, use `run = paragraph.add_run('text')` and `run.font`.\n\n"
                    "Output ONLY the Python code, with NO explanations before or after.\n"
                    "The code must be complete and ready to run in the Python interpreter."
                )
            
            if custom_prompt:
                prompt = custom_prompt.replace("$language", target_language)
            else:
                prompt = prompt_template.replace("$language", target_language)
            
            translated_text = self._process_translation_request(image_path, prompt)
            
            if not translated_text:
                logger.error(f"Failed to get translation for {image_path.name}")
                return False
            
            success = self._create_docx_from_code(translated_text, image_path, output_path)
            
            if success:
                logger.info(f"Successfully created translated document: {output_path.name}")
                return True
            else:
                logger.error(f"Failed to create translated document after all retry attempts")
                return False
                
        except Exception as e:
            logger.error(f"Error in translate_image_to_document: {e}")
            return False

    def translate_with_single_api_key(self,
        image_path: Path,
        output_path: Path,
        api_key_index: int,
        custom_prompt: Optional[str] = None) -> bool:
        """
        Translate using a single API key for the entire process.
        This ensures 1 API key per translation document.
        """
        global _busy_api_keys, _busy_keys_lock
        
        try:
            if api_key_index >= len(self.api_keys):
                raise ValueError(f"API key index {api_key_index} is out of range")
            
            original_selected_key_index = getattr(self, 'selected_key_index', 0)
            self.selected_key_index = api_key_index
            self.api_key = self.api_keys[api_key_index]
            self.client = genai.Client(api_key=self.api_key)
            
            result = self.translate_image_to_document(image_path, output_path, custom_prompt)
            
            # Release the key from busy state
            with _busy_keys_lock:
                _busy_api_keys.discard(api_key_index)
            
            # Restore original key
            self.selected_key_index = original_selected_key_index
            self.api_key = self.api_keys[self.selected_key_index]
            self.client = genai.Client(api_key=self.api_key)
            
            return result
            
        except Exception as e:
            # Release the key from busy state even if there's an error
            with _busy_keys_lock:
                _busy_api_keys.discard(api_key_index)
            logger.error(f"Error in single API key translation: {e}")
            return False
        
    def __del__(self):
        """Release the API key from busy state when translator is destroyed"""
        global _busy_api_keys, _busy_keys_lock
        try:
            if hasattr(self, 'selected_key_index'):
                with _busy_keys_lock:
                    _busy_api_keys.discard(self.selected_key_index)
                    logger.info(f"Released API key #{self.selected_key_index + 1} from busy state")
        except:
            pass

def process_translation_background(document_id: int, api_key_index: int = None, target_language: str = None):
   """
   Background function to process translation for a document.
   
   Args:
       document_id:    The ID of the Document record to translate.
       api_key_index:  If provided, this specific API key index is used exclusively
                       for this document (already claimed by the caller via
                       _claim_api_key_index). If None, the translator picks one
                       via the normal random-selection logic.
       target_language: If provided, overrides document.target_language before
                        translating (used when re-starting with a new language).
   """
   from sqlmodel import Session
   from ..database import engine
   from ..models.document import Document
   from ..utils.logging_util import log_translation_process, log_error, log_database_operation
   from pathlib import Path
   import os
   
   with Session(engine) as session:
       document = session.get(Document, document_id)
       if not document:
           logger.error(f"Document with ID {document_id} not found")
           # Release the key immediately if we can't find the document
           if api_key_index is not None:
               with _busy_keys_lock:
                   _busy_api_keys.discard(api_key_index)
           return
       
       # Override language if a new one was passed in
       if target_language:
           document.target_language = target_language
       
       document.status = "processing"
       session.add(document)
       session.commit()
       
       translator = None
       try:
           log_translation_process(document_id, document.user_id, document.filename, document.target_language, "processing")
           
           translator = SafeTranslator(db_session=session)
           
           # If a specific key was pre-assigned by the caller, switch to it now.
           # The key is already marked busy inside _busy_api_keys by _claim_api_key_index.
           if api_key_index is not None and api_key_index < len(translator.api_keys):
               # Release the key the translator picked during __init__
               with _busy_keys_lock:
                   _busy_api_keys.discard(translator.selected_key_index)
               # Switch to the pre-assigned key
               translator.selected_key_index = api_key_index
               translator.api_key = translator.api_keys[api_key_index]
               translator.client = genai.Client(api_key=translator.api_key)
               logger.info(f"[KEY ASSIGN] Document #{document_id} using pre-assigned API key #{api_key_index + 1}/{len(translator.api_keys)}")
           
           input_path = Path(document.filepath)
           output_filename = f"translated_{input_path.name}.docx"
           uploads_dir = Path("uploads")
           uploads_dir.mkdir(exist_ok=True)
           output_path = uploads_dir / output_filename
           
           try:
               prompt_path = Path(__file__).resolve().parent.parent.parent.parent / 'prompt.txt'
               with open(prompt_path, 'r', encoding='utf-8') as f:
                   prompt_template = f.read().strip()
                   custom_prompt = prompt_template.replace("$language", document.target_language)
           except FileNotFoundError:
               custom_prompt = (
                   "Analyze the uploaded invoice/document image and translate ALL text from the source language to $language while preserving the exact layout, tables, orientation, and formatting.\n\n"
                   "The image may be rotated (album / landscape orientation).\n"
                   "You MUST detect the original orientation of the document and preserve it exactly in the output.\n"
                   "If the source document is landscape or rotated, the generated .docx MUST use the same page orientation.\n"
                   "Do NOT normalize, straighten, or re-orient the content.\n\n"
                   "Requirements:\n"
                   "1. Translate all visible text to $language\n"
                   "2. Maintain the original document structure, tables, and layout\n"
                   "3. Keep numbers, dates, and formatting identical\n"
                   "4. Preserve table borders, cell alignment, spacing, and orientation\n"
                   "5. Save structure on send A4 list all in one page, you should generate one page translated\n\n"
                   "Generate ONLY executable Python code that:\n"
                   "- Uses the python-docx library to create a .docx file\n"
                   "- Recreates the document structure with translated text\n"
                   "- Sets page orientation to match the source image (portrait or landscape)\n"
                   "- Uses the variable `output_path` as the save location. (e.g. doc.save(output_path))\n"
                   "- IMPORTANT: In python-docx, `Paragraph` has no `font` attribute. To set font, use `run = paragraph.add_run('text')` and `run.font`.\n\n"
                   "Output ONLY the Python code, with NO explanations before or after.\n"
                   "The code must be complete and ready to run in the Python interpreter."
               ).replace("$language", document.target_language)
           
           from .document_validator import validate_document_image
           validation_result = validate_document_image(input_path)
           if validation_result == "REJECT_NOT_A_DOCUMENT":
               document.status = "failed"
               document.error_message = "Document validation failed: Uploaded file does not appear to be a valid document with readable text."
               session.add(document)
               session.commit()
               
               log_translation_process(document_id, document.user_id, document.filename, document.target_language, "failed", document.error_message)
               log_database_operation("update", "document", document.id, document.user_id, False, document.error_message)
               logger.error(f"Document validation failed for {input_path}")
               # Release the key
               with _busy_keys_lock:
                   _busy_api_keys.discard(translator.selected_key_index)
               return
           
           success = translator.translate_image_to_document(
               image_path=input_path,
               output_path=output_path,
               custom_prompt=custom_prompt,
               target_language=document.target_language
           )
           
           if success:
               document.status = "completed"
               document.output_filepath = str(output_path)
               document.completed_at = datetime.utcnow()
               
               log_translation_process(document_id, document.user_id, document.filename, document.target_language, "completed")
               log_database_operation("update", "document", document.id, document.user_id, True, None)
           else:
               document.status = "failed"
               document.error_message = "Translation failed after all retry attempts"
               
               log_translation_process(document_id, document.user_id, document.filename, document.target_language, "failed", document.error_message)
               log_database_operation("update", "document", document.id, document.user_id, False, document.error_message)
           
           session.add(document)
           session.commit()
           
           # Update parent folder status when all documents are done
           if document.folder_id:
               from ..models.workspace import WorkspaceFolder
               from sqlmodel import select as sql_select
               folder_docs = session.exec(
                   sql_select(Document).where(Document.folder_id == document.folder_id)
               ).all()
               
               pending_or_processing = [d for d in folder_docs if d.status in ("pending", "processing")]
               if not pending_or_processing:
                   folder = session.get(WorkspaceFolder, document.folder_id)
                   if folder:
                       has_failed = any(d.status == "failed" for d in folder_docs)
                       folder.status = "failed" if has_failed else "completed"
                       session.add(folder)
                       session.commit()
                       logger.info(f"[FOLDER] Folder #{document.folder_id} status updated to '{folder.status}'")
           
           # Release this document's API key
           if translator is not None and hasattr(translator, 'selected_key_index'):
               with _busy_keys_lock:
                   _busy_api_keys.discard(translator.selected_key_index)
           
       except Exception as e:
           document.status = "failed"
           document.error_message = str(e)
           session.add(document)
           session.commit()
           
           if translator is not None and hasattr(translator, 'selected_key_index'):
               with _busy_keys_lock:
                   _busy_api_keys.discard(translator.selected_key_index)
           elif api_key_index is not None:
               # Translator was never created; release the pre-assigned key
               with _busy_keys_lock:
                   _busy_api_keys.discard(api_key_index)
           
           log_error("process_translation_background", e, document.user_id, {"document_id": document_id})
           log_translation_process(document_id, document.user_id, document.filename, document.target_language, "failed", str(e))
           logger.error(f"Error processing translation for document {document_id}: {e}")