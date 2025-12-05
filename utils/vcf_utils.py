import re
import vobject
from typing import List, Tuple
from utils.file_utils import FileUtils


class VCFUtils:
    @staticmethod
    def create_vcf_entry(phone_number: str, contact_name: str) -> str:
        phone_str = str(phone_number).strip()
        if not phone_str.startswith('+') and not phone_str.startswith('0'):
            phone_str = '+' + phone_str

        return f"""BEGIN:VCARD
VERSION:3.0
FN:{contact_name}
TEL;TYPE=CELL:{phone_str}
END:VCARD

"""

    @staticmethod
    def create_vcf_file(phone_numbers: List[str], contact_name: str, filepath: str):
        with open(filepath, 'w', encoding='utf-8') as f:
            for i, phone in enumerate(phone_numbers, start=1):
                phone_str = str(phone).strip()
                if not phone_str.startswith('+') and not phone_str.startswith('0'):
                    phone_str = '+' + phone_str

                vcf_entry = f"""BEGIN:VCARD
VERSION:3.0
FN:{contact_name} {str(i).zfill(4)}
TEL;TYPE=CELL:{phone_str}
END:VCARD

"""
                f.write(vcf_entry)

    @staticmethod
    def extract_phone_numbers(vcf_filepath: str) -> List[str]:
        with open(vcf_filepath, 'r', encoding='utf-8') as f:
            vcf_content = f.read()

        numbers = []
        try:
            vcard_list = vobject.readComponents(vcf_content)
            for vcard in vcard_list:
                if hasattr(vcard, 'tel'):
                    for tel in vcard.tel_list:
                        numbers.append(tel.value)
        except Exception:
            pattern = r'TEL[^:]*:([^\r\n]+)'
            matches = re.findall(pattern, vcf_content)
            numbers = [m.strip() for m in matches]

        return numbers

    @staticmethod
    def extract_contacts(vcf_filepath: str) -> List[Tuple[str, str]]:
        with open(vcf_filepath, 'r', encoding='utf-8') as f:
            vcf_content = f.read()

        contacts = []
        try:
            vcard_list = vobject.readComponents(vcf_content)
            for vcard in vcard_list:
                name = ""
                phone = ""
                if hasattr(vcard, 'fn'):
                    name = vcard.fn.value
                if hasattr(vcard, 'tel'):
                    for tel in vcard.tel_list:
                        phone = tel.value
                        break
                if phone:
                    contacts.append((name, phone))
        except Exception:
            pass

        return contacts

    @staticmethod
    def read_vcf_components(vcf_filepath: str):
        with open(vcf_filepath, 'r', encoding='utf-8') as f:
            vcf_content = f.read()
        return list(vobject.readComponents(vcf_content))

    @staticmethod
    def rename_contacts(contacts, start_index: int, name_prefix: str):
        renamed = []
        for index, contact in enumerate(contacts, start=start_index):
            if hasattr(contact, 'fn'):
                clean_name = re.sub(r'\d+', '', contact.fn.value).strip()
                clean_name = FileUtils.remove_emojis(clean_name)
                contact.fn.value = f'{name_prefix} {str(index).zfill(2)}'
            renamed.append(contact)
        return renamed

    @staticmethod
    def merge_vcf_files(file_paths: List[str], output_path: str) -> int:
        all_vcards = []
        for filepath in file_paths:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    vcf_content = f.read()
                vcards = list(vobject.readComponents(vcf_content))
                all_vcards.extend(vcards)
            except Exception:
                continue

        with open(output_path, 'w', encoding='utf-8') as f:
            for vcard in all_vcards:
                f.write(vcard.serialize())

        return len(all_vcards)

    @staticmethod
    def count_contacts(filepath: str) -> int:
        if filepath.endswith('.vcf'):
            return len(VCFUtils.extract_phone_numbers(filepath))
        elif filepath.endswith('.txt'):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            numbers = FileUtils.extract_numbers_from_text(content)
            return len(numbers)
        return 0
