from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ==========================================
# UMUMIY RAD ETISH SABABLARI RO'YXATI
# Buni bitta joyda saqlaymiz, hamma joydan chaqiramiz (DRY)
# ==========================================
REJECT_REASONS = [
    "📸 Rasm sifatsiz yoki to'liq emas",
    "💰 Narxi noto'g'ri ko'rsatilgan",
    "🔄 Takroriy e'lon",
    "📵 Telefon raqam xato",
    "🚫 E'lon qoidalarimizga to'g'ri kelmaydi"
]


def get_user_confirm_kb(ad_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlash", callback_data=f"user_confirm_{ad_id}")
    builder.button(text="✏️ Tahrirlash", callback_data=f"user_edit_{ad_id}")
    builder.button(text="❌ Bekor qilish", callback_data=f"user_cancel_{ad_id}")
    builder.adjust(2, 1)
    return builder.as_markup()


def get_auto_tariff_kb(ad_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔘 Bir martlaik narx - 20.000 so'm", callback_data=f"a_tariff_oddiy_{ad_id}")
    builder.button(text="🔘 Bir oy (Kun ora - 200.000 so'm)", callback_data=f"a_tariff_vip1_{ad_id}")
    builder.button(text="🔘 Bir oy (Har kuni - 400.000 so'm)", callback_data=f"a_tariff_vip2_{ad_id}")
    builder.button(text="🔙 Orqaga", callback_data=f"a_tback_{ad_id}")
    builder.adjust(1)
    return builder.as_markup()


def get_admin_action_kb(ad_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 To'lov so'rash", callback_data=f"admin_payment_{ad_id}")
    builder.button(text="❌ Rad etish", callback_data=f"admin_reject_{ad_id}")
    builder.button(text="✏️ Tahrirlash", callback_data=f"admin_edit_tg_{ad_id}")
    builder.adjust(2, 1)
    return builder.as_markup()


def get_reject_reasons_kb(ad_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # Tayyor ro'yxatdan o'qiymiz
    for i, reason in enumerate(REJECT_REASONS):
        builder.button(text=reason, callback_data=f"reject_reason_{ad_id}_{i}")

    builder.button(text="✍️ Boshqa sabab (Qo'lda yozish)", callback_data=f"reject_custom_{ad_id}")
    builder.button(text="🔙 Orqaga", callback_data=f"reject_back_{ad_id}")

    builder.adjust(1)
    return builder.as_markup()


def get_auto_edit_kb(ad_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🚗 Rusumi", callback_data=f"e_auto_model_{ad_id}")
    builder.button(text="📅 Yili", callback_data=f"e_auto_year_{ad_id}")
    builder.button(text="📟 Probeg", callback_data=f"e_auto_distance_{ad_id}")
    builder.button(text="🎨 Kraska", callback_data=f"e_auto_coat_{ad_id}")
    builder.button(text="⚙️ Holati", callback_data=f"e_auto_condition_{ad_id}")
    builder.button(text="⛽️ Yoqilg'i", callback_data=f"e_auto_oil_{ad_id}")
    builder.button(text="💰 Narxi", callback_data=f"e_auto_price_{ad_id}")
    builder.button(text="☎️ Raqam", callback_data=f"e_auto_phone_numbers_{ad_id}")
    builder.button(text="✍️ Ma'lumot", callback_data=f"e_auto_info_{ad_id}")
    builder.button(text="📍 Manzil", callback_data=f"e_auto_location_{ad_id}")
    builder.button(text="📸 Rasmlarni o'zgartirish", callback_data=f"e_auto_photo_{ad_id}")
    builder.button(text="🔙 Orqaga", callback_data=f"a_tback_{ad_id}")

    builder.adjust(2, 2, 2, 2, 2, 1, 1, 1)
    return builder.as_markup()