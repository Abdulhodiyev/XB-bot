from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_ad_type_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🛍 Oldi-sotdi e'lonlar", callback_data="ad_type_trade")
    builder.button(text="💼 Biznes e'lonlar", callback_data="ad_type_business")
    builder.adjust(1)
    return builder.as_markup()


def get_trade_categories_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🚗 Avto", callback_data="category_auto")
    builder.button(text="🏠 Uy-joy", callback_data="category_house")

    # 🛑 YANGI BO'LIMLAR QO'SHILDI
    builder.button(text="📱 Telefon", callback_data="category_phone")
    builder.button(text="📦 Boshqa turdagi elon", callback_data="category_other")

    builder.button(text="🔙 Orqaga", callback_data="back_to_ad_types")

    # Tugmalarni ustunlarga bo'lamiz: 2, 1, 1, 1
    builder.adjust(3, 1, 1)
    return builder.as_markup()