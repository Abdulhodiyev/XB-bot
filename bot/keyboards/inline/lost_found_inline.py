from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_lf_type_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔍 Yo'qotib qo'ydim", callback_data="lf_type_lost")
    builder.button(text="🎁 Topib oldim", callback_data="lf_type_found")
    builder.adjust(2)
    return builder.as_markup()

def get_lf_confirm_kb(ad_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlash (Adminga yuborish)", callback_data=f"lf_confirm_{ad_id}")
    builder.button(text="✏️ Tahrirlash", callback_data=f"lf_edit_{ad_id}")
    builder.button(text="❌ Bekor qilish", callback_data=f"lf_cancel_{ad_id}")
    builder.adjust(1, 2)
    return builder.as_markup()

def get_lf_admin_kb(ad_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Kanalga joylash", callback_data=f"lf_admin_approve_{ad_id}")
    builder.button(text="❌ Rad etish", callback_data=f"admin_reject_{ad_id}")
    builder.button(text="✏️ Tahrirlash", callback_data=f"admin_edit_tg_{ad_id}")
    builder.adjust(1, 2)
    return builder.as_markup()

def get_lf_edit_kb(ad_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📦 Buyum", callback_data=f"e_lf_item_{ad_id}")
    builder.button(text="📍 Qayerda", callback_data=f"e_lf_location_{ad_id}")
    builder.button(text="📝 Ma'lumot", callback_data=f"e_lf_info_{ad_id}")
    builder.button(text="📞 Raqam", callback_data=f"e_lf_phone_{ad_id}")
    builder.button(text="📸 Rasm", callback_data=f"e_lf_photo_{ad_id}")
    builder.button(text="🔙 Orqaga", callback_data=f"lf_tback_{ad_id}")
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup()