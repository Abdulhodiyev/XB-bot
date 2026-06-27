from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📢 Elon berish")],
        [KeyboardButton(text="🤝 Yóqolgan / Topilgan (Bepul)")],
        [
            KeyboardButton(text="ℹ️ Narxlar + Instagram"),
            KeyboardButton(text="📞 Admin bilan boĝlanish")
        ],
        [
            KeyboardButton(text="📁 Mening elonlarim"),
            KeyboardButton(text="💼 Bosh ish órinlari (vakansiyalar)")
        ],
        [
            KeyboardButton(text="🌤 Ob-havo ma'lumotlari"),
            KeyboardButton(text="👨‍💻 Dastur creatori")
        ]
    ],
    resize_keyboard=True,
    input_field_placeholder="Kerakli bo'limni tanlang..."
)