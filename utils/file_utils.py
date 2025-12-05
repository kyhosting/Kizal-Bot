import os
import re
import glob
from datetime import datetime
from typing import List, Tuple


class FileUtils:
    TMP_DIR = "tmp"

    @classmethod
    def ensure_tmp_dir(cls):
        os.makedirs(cls.TMP_DIR, exist_ok=True)

    @classmethod
    def get_temp_path(cls, user_id: int, filename: str) -> str:
        cls.ensure_tmp_dir()
        return os.path.join(cls.TMP_DIR, f"temp_{user_id}_{filename}")

    @classmethod
    def cleanup_user_files(cls, user_id: int):
        pattern = os.path.join(cls.TMP_DIR, f"temp_{user_id}_*")
        for filepath in glob.glob(pattern):
            try:
                os.remove(filepath)
            except Exception:
                pass

    @classmethod
    def cleanup_old_files(cls, max_age_hours: int = 1):
        now = datetime.now()
        pattern = os.path.join(cls.TMP_DIR, "temp_*")
        for filepath in glob.glob(pattern):
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                if (now - mtime).total_seconds() > max_age_hours * 3600:
                    os.remove(filepath)
            except Exception:
                pass

    @staticmethod
    def extract_numbers_from_text(text: str) -> List[str]:
        numbers = re.findall(r'[\+]?[\d\s\-\(\)]+', text)
        cleaned = []
        for num in numbers:
            clean_num = re.sub(r'[\s\-\(\)]', '', num)
            if len(clean_num) >= 8:
                cleaned.append(clean_num)
        return cleaned

    @staticmethod
    def validate_phone_number(number: str) -> bool:
        clean = re.sub(r'[\s\-\(\)]', '', number)
        if clean.startswith('+') or clean.startswith('0'):
            return len(clean) >= 8
        return False

    @staticmethod
    def format_phone_number(number: str) -> str:
        clean = re.sub(r'[\s\-\(\)]', '', number)
        if not clean.startswith('+') and not clean.startswith('0'):
            clean = '+' + clean
        return clean

    @staticmethod
    def remove_emojis(text: str) -> str:
        emoji_pattern = re.compile(
            "["
            u"\U0001F600-\U0001F64F"
            u"\U0001F300-\U0001F5FF"
            u"\U0001F680-\U0001F6FF"
            u"\U0001F1E0-\U0001F1FF"
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE
        )
        return emoji_pattern.sub(r'', text)

    @staticmethod
    def get_file_extension(filename: str) -> str:
        return os.path.splitext(filename)[1].lower()

    @staticmethod
    def is_txt_file(filename: str) -> bool:
        return filename.lower().endswith('.txt')

    @staticmethod
    def is_vcf_file(filename: str) -> bool:
        return filename.lower().endswith('.vcf')

    @staticmethod
    def is_excel_file(filename: str) -> bool:
        ext = filename.lower()
        return ext.endswith('.xlsx') or ext.endswith('.xls')

    @staticmethod
    def safe_remove(filepath: str):
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception:
            pass

    @staticmethod
    def read_file_content(filepath: str) -> str:
        encodings = ['utf-8', 'latin-1', 'cp1252']
        for encoding in encodings:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        raise ValueError("Could not decode file with any known encoding")

    @staticmethod
    def write_file_content(filepath: str, content: str):
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
