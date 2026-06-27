from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_other_type_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 E'lon tayyorlash", callback_data="otype_step")
    builder.button(text="✅ E'lonim tayyor", callback_data="otype_ready")
    builder.button(text="🔙 Orqaga", callback_data="ad_type_trade")
    builder.adjust(1)
    return builder.as_markup()


# 🛑 O'ZGARISH: is_ready parametri qo'shildi
def get_other_confirm_kb(ad_id: int, is_ready: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlash", callback_data=f"o_confirm_{ad_id}")

    if is_ready:
        builder.button(text="🔄 Boshidan boshlash", callback_data=f"o_restart_{ad_id}")
    else:
        builder.button(text="✏️ Tahrirlash", callback_data=f"o_edit_{ad_id}")

    builder.button(text="❌ Bekor qilish", callback_data=f"o_cancel_{ad_id}")
    builder.adjust(1)
    return builder.as_markup()


def get_other_tariff_kb(ad_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔘 Bir martlaik narx - 20.000 so'm", callback_data=f"o_tariff_oddiy_{ad_id}")
    builder.button(text="🔘 Bir oy (Kun ora - 200.000 so'm)", callback_data=f"o_tariff_vip1_{ad_id}")
    builder.button(text="🔘 Bir oy (Har kuni - 400.000 so'm)", callback_data=f"o_tariff_vip2_{ad_id}")
    builder.button(text="🔙 Orqaga", callback_data=f"o_tback_{ad_id}")
    builder.adjust(1)
    return builder.as_markup()


def get_other_admin_kb(ad_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 To'lov so'rash", callback_data=f"admin_payment_{ad_id}")
    builder.button(text="❌ Rad etish", callback_data=f"admin_reject_{ad_id}")
    builder.button(text="✏️ Tahrirlash", callback_data=f"admin_edit_tg_{ad_id}")
    builder.adjust(2, 1)
    return builder.as_markup()


# 🛑 YANGI: Tahrirlash klaviaturasi
def get_other_edit_kb(ad_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🛍 Nomi", callback_data=f"e_other_title_{ad_id}")
    builder.button(text="✍️ Ma'lumot", callback_data=f"e_other_info_{ad_id}")
    builder.button(text="💰 Narxi", callback_data=f"e_other_price_{ad_id}")
    builder.button(text="☎️ Raqam", callback_data=f"e_other_phone_{ad_id}")
    builder.button(text="📍 Manzil", callback_data=f"e_other_location_{ad_id}")
    builder.button(text="📸 Rasmlar", callback_data=f"e_other_photo_{ad_id}")
    builder.button(text="🔙 Orqaga", callback_data=f"o_tback_{ad_id}")
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()