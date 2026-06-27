# ==========================================
# MARKAZIY YORDAMCHI FUNKSIYALAR (DRY)
# ==========================================

def is_valid_text(text: str) -> bool:
    if not text:
        return False

    blacklist = [
        "📢 Elon berish", "🗂 Mening elonlarim", "⬅️ Orqaga",
        "❌ Bekor qilish", "⏭ O'tkazib yuborish", "➡️ Keyingi qadam",
        "📁", "💼", "🌤", "👨‍💻", "🤝", "ℹ️", "📞"
    ]

    for b in blacklist:
        if b in text:
            return False

    return len(text.strip()) >= 1


def get_ad_type(ad) -> str:
    d = ad.details
    if "business_text" in d and not d.get("is_ready_post"):
        return "Biznes"
    if "property_type" in d:
        return "Uy-joy"
    if "memory" in d and "box_docs" in d:
        return "Telefon"

    # 🛑 DIQQAT: LF tekshiruvi Avto'dan doim tepada turishi shart!
    if "lf_type" in d:
        return "Yo'qolgan/Topilgan"

    if d.get("is_ready_post") or "title" in d:
        return "Boshqa"

    return "Avto"