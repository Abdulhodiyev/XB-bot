from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_phone_confirm_kb(ad_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlash", callback_data=f"p_confirm_{ad_id}")
    builder.button(text="✏️ Tahrirlash", callback_data=f"p_edit_{ad_id}")
    builder.button(text="❌ Bekor qilish", callback_data=f"p_cancel_{ad_id}")
    builder.adjust(2, 1)
    return builder.as_markup()

def get_phone_tariff_kb(ad_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔘 Bir martlaik narx - 20.000 so'm", callback_data=f"a_tariff_oddiy_{ad_id}")
    builder.button(text="🔘 Bir oy (Kun ora - 200.000 so'm)", callback_data=f"a_tariff_vip1_{ad_id}")
    builder.button(text="🔘 Bir oy (Har kuni - 400.000 so'm)", callback_data=f"a_tariff_vip2_{ad_id}")
    builder.button(text="🔙 Orqaga", callback_data=f"a_tback_{ad_id}")
    builder.adjust(1)
    return builder.as_markup()


def get_phone_admin_kb(ad_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 To'lov so'rash", callback_data=f"admin_payment_{ad_id}")
    builder.button(text="❌ Rad etish", callback_data=f"admin_reject_{ad_id}")
    builder.button(text="✏️ Tahrirlash", callback_data=f"admin_edit_tg_{ad_id}")
    builder.adjust(2, 1)
    return builder.as_markup()


def get_phone_edit_kb(ad_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔖 Rusumi", callback_data=f"e_phone_model_{ad_id}")
    builder.button(text="💾 Xotirasi", callback_data=f"e_phone_memory_{ad_id}")
    builder.button(text="🛠 Holati", callback_data=f"e_phone_condition_{ad_id}")
    builder.button(text="📦 Karobka/Dok", callback_data=f"e_phone_box_docs_{ad_id}")
    builder.button(text="✍️ Qo'shimcha", callback_data=f"e_phone_info_{ad_id}")
    builder.button(text="💰 Narxi", callback_data=f"e_phone_price_{ad_id}")
    builder.button(text="☎️ Raqam", callback_data=f"e_phone_phone_{ad_id}")
    builder.button(text="📍 Manzil", callback_data=f"e_phone_location_{ad_id}")
    builder.button(text="📸 Rasmlar", callback_data=f"e_phone_photo_{ad_id}")
    builder.button(text="🔙 Orqaga", callback_data=f"p_tback_{ad_id}")

    # Tugmalarni 2 tadan taxlab chiqamiz
    builder.adjust(2, 2, 2, 2, 1, 1)
    return builder.as_markup()