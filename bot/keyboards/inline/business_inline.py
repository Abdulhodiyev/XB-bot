from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_business_confirm_kb(ad_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlash", callback_data=f"b_confirm_{ad_id}")
    builder.button(text="✏️ Tahrirlash", callback_data=f"b_edit_{ad_id}")
    builder.button(text="❌ Bekor qilish", callback_data=f"user_cancel_{ad_id}")
    builder.adjust(2, 1)
    return builder.as_markup()

def get_business_tariff_kb(ad_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔘 Bir martalik narx - 60.000 so'm", callback_data=f"b_tariff_oddiy_{ad_id}")
    builder.button(text="🔘 Bir oy (Kun ora - 600.000 so'm)", callback_data=f"b_tariff_vip_{ad_id}")
    builder.button(text="🔙 Orqaga", callback_data=f"b_tback_{ad_id}")
    builder.adjust(1)
    return builder.as_markup()

def get_business_admin_kb(ad_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 To'lov so'rash", callback_data=f"admin_payment_{ad_id}")
    builder.button(text="❌ Rad etish", callback_data=f"admin_reject_{ad_id}")
    builder.button(text="✏️ Tahrirlash", callback_data=f"admin_edit_tg_{ad_id}")
    builder.adjust(2, 1)
    return builder.as_markup()