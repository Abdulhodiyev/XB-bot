import re
from datetime import datetime


class AutoAdValidator:
    @staticmethod
    def validate_model(text: str) -> tuple[bool, str]:
        if not text or len(text.strip()) < 2:
            return False, "❗️ Kamida 2 ta belgi bo'lishi kerak."
        return True, ""

    @staticmethod
    def validate_year(text: str) -> tuple[bool, str]:
        if not text.isdigit():
            return False, "❗️ Yil faqat raqamlardan iborat bo'lishi kerak (Masalan: 2020)."
        year = int(text)
        current_year = datetime.now().year
        if not (1960 <= year <= current_year):
            return False, f"❗️ Yil 1960 va {current_year} oralig'ida bo'lishi kerak."
        return True, ""

    @staticmethod
    def validate_price(text: str) -> tuple[bool, str]:
        if not text or len(text.strip()) < 2:
            return False, "❗️ Narxni to'g'ri kiriting yoki 'Kelishamiz' deb yozing."
        return True, ""

    @staticmethod
    def validate_phone(text: str) -> tuple[bool, str]:
        # Barcha raqam bo'lmagan belgilarni tozalab, faqat raqamlarni qoldiramiz
        clean = re.sub(r'\D', '', text)

        # O'zbekiston raqamlari standartlari:
        # 1) 9 xonali (masalan: 901234567)
        # 2) 12 xonali va 998 bilan boshlangan (masalan: 998901234567)
        if len(clean) == 9:
            return True, ""
        elif len(clean) == 12 and clean.startswith("998"):
            return True, ""

        return False, "❗️ Raqam noto'g'ri! Masalan: <b>901234567</b> yoki <b>+998901234567</b> shaklida yozing."

    @staticmethod
    def validate_distance(text: str) -> tuple[bool, str]:
        clean = re.sub(r'[\s_]', '', text).lower()
        clean = clean.replace('km', '').replace('ming', '000')
        if not clean.isdigit():
            return False, "❗️ Probegni faqat raqamda kiriting (Masalan: 120000)."
        return True, ""