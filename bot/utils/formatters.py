import html


# ==========================================
# YORDAMCHI FUNKSIYA (Telefonlar uchun)
# ==========================================
def format_phones(phone_numbers: str) -> str:
    if not phone_numbers:
        return "☎️ <b>Aloqa:</b> Ko'rsatilmagan\n"

    # Raqamlarni vergul orqali ajratib, ro'yxatga aylantiramiz
    phones = [p.strip() for p in phone_numbers.split(",") if p.strip()]

    if len(phones) > 1:
        res = "☎️ <b>Murojaat uchun:</b>\n"
        for p in phones:
            res += f"👉 {html.escape(p)}\n"
        return res
    else:
        return f"☎️ <b>Aloqa:</b> {html.escape(phones[0])}\n"


# ==========================================
# 1. AVTO E'LONLAR UCHUN FORMAT
# ==========================================
def format_auto_text(details: dict, phones: str) -> str:
    text = "🚗 <b>AVTOMOBIL SOTILADI</b>\n\n"

    text += f"🚙 <b>Rusumi:</b> {html.escape(details.get('model', ''))}\n"
    text += f"📅 <b>Yili:</b> {html.escape(details.get('year', ''))}\n"
    text += f"📟 <b>Probeg:</b> {html.escape(details.get('distance', ''))}\n"
    text += f"🎨 <b>Kraska:</b> {html.escape(details.get('coat', ''))}\n"
    text += f"⚙️ <b>Holati:</b> {html.escape(details.get('condition', ''))}\n"
    text += f"⛽️ <b>Yoqilg'i:</b> {html.escape(details.get('oil', ''))}\n"
    if details.get('info'):
        text += f"✍️ <b>Qo'shimcha ma'lumot:</b> {html.escape(details.get('info', ''))}\n"
    text += f"💰 <b>Narxi:</b> {html.escape(details.get('price', ''))}\n\n"

    # Yordamchi funksiya ulandi
    text += format_phones(phones) + "\n"
    text += f"📍 <b>Manzil:</b> {html.escape(details.get('location', ''))}\n\n"
    text += f"👉 <b>@XonobodBugun</b>"

    return text


# ==========================================
# 2. UY-JOY E'LONLARI UCHUN FORMAT
# ==========================================
def format_house_text(details: dict, phone_numbers: str) -> str:
    prop_type = details.get("property_type", "")
    action = details.get("action_type", "")

    if "Kvartira" in prop_type:
        header_type = "KVARTIRA"
    elif "Hovli" in prop_type:
        header_type = "HOVLI / YER"
    else:
        header_type = "NOTURAR JOY"

    title_action = "SOTILADI" if action == "Sotiladi" else "IJARAGA BERILADI"
    text = f"🏠 <b>{header_type} {title_action}</b>\n\n"

    if "Kvartira" in prop_type:
        text += f"🔢 <b>Xonalar soni:</b> {html.escape(str(details.get('rooms', '')))}\n"
        text += f"🏢 <b>Qavati:</b> {html.escape(str(details.get('floor', '')))}\n"
    elif "Hovli" in prop_type:
        text += f"📏 <b>Yer maydoni:</b> {html.escape(str(details.get('area', '')))}\n"
        text += f"🔢 <b>Xonalar soni:</b> {html.escape(str(details.get('rooms', '')))}\n"
    elif "Noturar" in prop_type:
        text += f"🏢 <b>Obyekt nomi:</b> {html.escape(str(details.get('building_name', '')))}\n"
        text += f"📏 <b>Yer maydoni:</b> {html.escape(str(details.get('area', '')))}\n"
        text += f"📄 <b>Hujjatlari:</b> {html.escape(str(details.get('docs', '')))}\n"

    text += f"🚰 <b>Sharoitlar:</b> {html.escape(str(details.get('conditions', '')))}\n"

    if "Noturar" not in prop_type:
        text += f"🛠 <b>Holati/Remonti:</b> {html.escape(str(details.get('condition_state', '')))}\n"

    if details.get('info'):
        text += f"✍️ <b>Qo'shimcha ma'lumot:</b> {html.escape(str(details.get('info', '')))}\n"

    text += f"💰 <b>Narxi:</b> {html.escape(str(details.get('price', '')))}\n\n"

    # Yordamchi funksiya ulandi
    text += format_phones(phone_numbers)
    text += f"\n 📍 <b>Manzil:</b> {html.escape(str(details.get('location', '')))}"

    return text


# ==========================================
# 3. ADMIN UCHUN QO'SHIMCHA MA'LUMOT (FOOTER)
# ==========================================
def get_admin_footer(user, tariff: str) -> str:
    return (
        f"\n\n👤 <b>Mijoz:</b> <a href='tg://user?id={user.user_id}'>{html.escape(user.full_name)}</a>\n"
        f"💳 <b>Tanlangan tarif:</b> {html.escape(tariff)}"
    )


# ==========================================
# 4. TELEFON E'LONLARI UCHUN FORMAT
# ==========================================
def format_phone_text(details: dict, phones: str) -> str:
    text = "📱 <b>TELEFON SOTILADI</b>\n\n"

    text += f"🔖 <b>Modeli:</b> {html.escape(details.get('model', ''))}\n"
    text += f"💾 <b>Xotirasi:</b> {html.escape(details.get('memory', ''))}\n"
    text += f"🛠 <b>Holati:</b> {html.escape(details.get('condition', ''))}\n"
    text += f"📦 <b>Karobka/Dokument:</b> {html.escape(details.get('box_docs', ''))}\n"

    if details.get('info'):
        text += f"✍️ <b>Qo'shimcha ma'lumot:</b> {html.escape(details.get('info', ''))}\n"

    text += f"💰 <b>Narxi:</b> {html.escape(details.get('price', ''))}\n\n"

    # Yordamchi funksiya ulandi (Avto va Uy-joydagi kabi)
    text += format_phones(phones)

    text += f"\n📍 <b>Manzil:</b> {html.escape(details.get('location', ''))}\n\n"
    text += f"👉 <b>@XonobodBugun</b>"

    return text


# ==========================================
# 5. BOSHQA BUYUMLAR UCHUN FORMAT
# ==========================================
def format_other_text(details: dict, phones: str) -> str:
    text = f"🛒 <b>DIQQAT E'LON!</b>\n\n"
    text += f"🏷 <b>Ushbu {html.escape(details.get('title', ''))} sotiladi</b>\n"

    if details.get('info'):
        text += f"✍️ <b>Qo'shimcha ma'lumot:</b> {html.escape(details.get('info', ''))}\n"

    text += f"💰 <b>Narxi:</b> {html.escape(details.get('price', ''))}\n\n"
    text += format_phones(phones)
    text += f"\n📍 <b>Manzil:</b> {html.escape(details.get('location', ''))}\n\n"
    text += f"👉 <b>@XonobodBugun</b>"

    return text


def format_lost_found_text(details: dict, phones: str) -> str:
    import html
    lf_type = details.get("lf_type")

    if lf_type == "lost":
        text = "❗️ <b>DIQQAT YO'QOLGAN!</b>\n\n"
    else:
        text = "❗️ <b>DIQQAT TOPIB OLINDI!</b>\n\n"

    text += f"📦 <b>Buyum:</b> {html.escape(details.get('item', ''))}\n"
    text += f"📍 <b>Qayerda:</b> {html.escape(details.get('location', ''))}\n"

    if details.get('info'):
        text += f"📝 <b>Qo'shimcha ma'lumot:</b> {html.escape(details.get('info', ''))}\n"

    text += f"\n{format_phones(phones)}\n"

    if lf_type == "lost":
        text += "🙏 <b>Topib olganlar bo'lsa, iltimos tepadagi raqamga qo'ng'iroq qiling!</b>\n\n"
    else:
        text += "🙏 <b>Egasi bo'lsa tepadagi raqamga bog'laning! (Dalil so'raladi)</b>\n\n"

    text += "👉 <b>@XonobodBugun</b>"
    return text