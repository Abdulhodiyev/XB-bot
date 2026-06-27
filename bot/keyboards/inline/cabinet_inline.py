from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_my_ads_page_kb(ads: list, current_page: int, total_pages: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # 1. Raqamli tugmalar (1, 2, 3, 4, 5) - yonma-yon teriladi
    row_btns = []
    for i, ad in enumerate(ads, start=1):
        row_btns.append(InlineKeyboardButton(text=f"{i}️⃣", callback_data=f"myad_view_{ad.id}"))

    if row_btns:
        builder.row(*row_btns)

    # 2. Sahifalash tugmalari (⬅️ | 1 / 3 | ➡️)
    nav_btns = []

    if current_page > 1:
        nav_btns.append(InlineKeyboardButton(text="⬅️", callback_data=f"myads_page_{current_page - 1}"))
    else:
        nav_btns.append(InlineKeyboardButton(text="⏺", callback_data="ignore"))

    nav_btns.append(InlineKeyboardButton(text=f"{current_page} / {total_pages}", callback_data="ignore"))

    if current_page < total_pages:
        nav_btns.append(InlineKeyboardButton(text="➡️", callback_data=f"myads_page_{current_page + 1}"))
    else:
        nav_btns.append(InlineKeyboardButton(text="⏺", callback_data="ignore"))

    builder.row(*nav_btns)
    return builder.as_markup()


def get_ad_action_kb(ad_id: int, status: str, category_name: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if status == "approved" and category_name != "Biznes":
        # 🛑 HIMOYA: Kategoriyaga qarab tugma matnini o'zgartiramiz
        if category_name == "Yo'qolgan/Topilgan":
            builder.button(text="✅ Egasi topildi (Kanalda belgilash)", callback_data=f"myad_sold_{ad_id}")
        else:
            builder.button(text="🤝 Sotildi (Kanalda e'lon qilish)", callback_data=f"myad_sold_{ad_id}")

    builder.button(text="🔙 Orqaga (Ro'yxatga)", callback_data="myad_back_list")
    builder.adjust(1)
    return builder.as_markup()