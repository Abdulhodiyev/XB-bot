from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

# 1. BOSH TUGMALAR
def get_house_type_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🏢 Kvartira", callback_data="htype_kvartira")
    builder.button(text="🏡 Hovli / Yer", callback_data="htype_hovli")
    builder.button(text="🏪 Noturar joy", callback_data="htype_noturar")

    # 🛑 YANGI TUGMA QO'SHILDI: Umumiy e'lon turlari menyusiga qaytish uchun
    builder.button(text="🔙 Orqaga", callback_data="ad_type_trade")

    # Tugmalarni tartiblaymiz: tepada 2 ta, pastda 1 ta, oxirida Orqaga
    builder.adjust(2, 1, 1)
    return builder.as_markup()

def get_house_action_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💰 Sotiladi", callback_data="haction_sotiladi")
    builder.button(text="🤝 Ijaraga", callback_data="haction_ijara")
    builder.button(text="🔙 Orqaga", callback_data="haction_back")
    builder.adjust(2, 1)
    return builder.as_markup()

# 2. FOYDALANUVCHI TASDIQLASHI
def get_house_confirm_kb(ad_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlash", callback_data=f"h_confirm_{ad_id}")
    builder.button(text="✏️ Tahrirlash", callback_data=f"h_edit_{ad_id}") # Uy-joy uchun maxsus edit
    builder.button(text="❌ Bekor qilish", callback_data=f"h_cancel_{ad_id}")
    builder.adjust(2, 1)
    return builder.as_markup()

# 3. TARIF TANLASH
def get_house_tariff_kb(ad_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔘 Bir martlaik narx - 20.000 so'm", callback_data=f"h_tariff_oddiy_{ad_id}")
    builder.button(text="🔘 Bir oy (Kun ora - 200.000 so'm)", callback_data=f"h_tariff_vip1_{ad_id}")
    builder.button(text="🔘 Bir oy (Har kuni - 400.000 so'm)", callback_data=f"h_tariff_vip2_{ad_id}")
    builder.button(text="🔙 Orqaga", callback_data=f"h_tback_{ad_id}")
    builder.adjust(1)
    return builder.as_markup()

def get_house_admin_kb(ad_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 To'lov so'rash", callback_data=f"admin_payment_{ad_id}")
    builder.button(text="❌ Rad etish", callback_data=f"admin_reject_{ad_id}")
    builder.button(text="✏️ Tahrirlash", callback_data=f"admin_edit_tg_{ad_id}")
    builder.adjust(2, 1)
    return builder.as_markup()


def get_house_edit_kb(ad_id: int, prop_type: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if "Kvartira" in prop_type:
        builder.button(text="🔢 Xonalar", callback_data=f"e_house_rooms_{ad_id}")
        builder.button(text="🏢 Qavati", callback_data=f"e_house_floor_{ad_id}")
    elif "Hovli" in prop_type:
        builder.button(text="📏 Maydoni", callback_data=f"e_house_area_{ad_id}")
        builder.button(text="🔢 Xonalar", callback_data=f"e_house_rooms_{ad_id}")
    elif "Noturar" in prop_type:
        builder.button(text="🏪 Obyekt nomi", callback_data=f"e_house_building_name_{ad_id}")
        builder.button(text="📏 Maydoni", callback_data=f"e_house_area_{ad_id}")
        builder.button(text="📄 Hujjatlari", callback_data=f"e_house_docs_{ad_id}")

    builder.button(text="🚰 Sharoitlar", callback_data=f"e_house_conditions_{ad_id}")

    if "Noturar" not in prop_type:
        builder.button(text="🛠 Holati/Remonti", callback_data=f"e_house_condition_state_{ad_id}")

    builder.button(text="✍️ Qo'shimcha", callback_data=f"e_house_info_{ad_id}")
    builder.button(text="💰 Narxi", callback_data=f"e_house_price_{ad_id}")
    builder.button(text="☎️ Raqam", callback_data=f"e_house_phone_numbers_{ad_id}")
    builder.button(text="📍 Manzil", callback_data=f"e_house_location_{ad_id}")

    builder.button(text="📸 Rasmlarni o'zgartirish", callback_data=f"e_house_photo_{ad_id}")
    builder.button(text="🔙 Orqaga", callback_data=f"h_tback_{ad_id}")

    builder.adjust(2)
    return builder.as_markup()