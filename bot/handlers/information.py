import logging
import aiohttp
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import StateFilter
from bot.models import Vacancy
from contextlib import suppress
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger(__name__)
router = Router()


# ==========================================
# 1. NARXLAR VA INSTAGRAM
# ==========================================
@router.message(F.text.contains("Narxlar"), StateFilter('*'))
async def show_prices(message: Message):
    text = (
        "📊 <b>@XonobodBugun Telegram kanalida e'lon berish narxlari:</b>\n\n"
        "🔰 <b>Oldi-Sotdi e'lonlar uchun:</b>\n"
        "▫️ Bir martalik narx: 20.000 so'm\n"
        "▫️ Bir oylik (Kun ora): 200.000 so'm\n"
        "▫️ Bir oylik (Har kuni): 400.000 so'm\n\n"
        "🔰 <b>Biznes turiga kiruvchi e'lonlar uchun:</b>\n"
        "▫️ Bir martalik narx: 60.000 so'm\n"
        "▫️ Bir oylik (Kun ora): 600.000 so'm\n"
        "▫️ Bir oylik (Har kuni): 1.200.000 so'm\n\n"
        "🔰 <b>Yo'qolgan / Topilgan:</b> Mutlaqo Bepul!\n\n"
        "➖➖➖➖➖➖➖➖\n\n"
        "📊 <b>@XonobodBugun Instagram sahifasida reklama narxlari:</b>\n\n"
        "▫️ Istoriya (stories): 100.000 so'm\n"
        "▫️ Post (Tayyor bo'lsa): 60$\n"
        "▫️ Post (O'zimiz borib reklama qilib berishimiz): 150$\n\n"
        "☎️ <b>Batafsil:</b> +998999050690\n"
        "Telegramda: @Bobur_Zokiroff\n\n"
        "❗️<b>Diqqat:</b> Firibgarlik, qimor, noqonuniy narsalar sotish, oriflaymga o'xshash va boshqa noqonuniy reklamalar qat'iyan man etiladi!"
    )
    await message.answer(text, parse_mode="HTML")


# ==========================================
# 2. ADMIN BILAN BOG'LANISH
# ==========================================
@router.message(F.text.contains("Admin bilan"), StateFilter('*'))
async def contact_admin(message: Message):
    text = (
        "👨‍💻 <b>Admin bilan aloqa</b>\n\n"
        "✍️ Savollar, takliflar yoki bot ishlashida muammo bo'lsa, bizga yozishingiz mumkin!\n\n"
        "👉 <b>Telegram:</b> @XonobodBugun_admin\n"
        "📞 <b>Telefon:</b> +998999050690 (Boburjon)"
    )
    await message.answer(text, parse_mode="HTML")


# ==========================================
# 3. DASTUR CREATORI
# ==========================================
@router.message(F.text == "👨‍💻 Dastur creatori", StateFilter('*'))
async def show_creator(message: Message):
    text = (
        "👨‍💻 <b>Dastur haqida:</b>\n\n"
        "Ushbu raqamli loyiha va Telegram bot <b>Muhammaddiyor Abdulhodiyev</b> tomonidan noldan ishlab chiqilgan va avtomatlashtirilgan.\n\n"
        "🔗 <b>GitHub profil:</b> <a href='https://github.com/abdulhodiyev-muhammaddiyor'>abdulhodiyev-muhammaddiyor</a>"
    )
    await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)


# ==========================================
# 4. VAKANSIYALAR (DJANGO BAZADAN)
# ==========================================
@router.message(F.text.contains("vakansiyalar"), StateFilter('*'))
async def show_vacancies(message: Message):
    # Bazadagi faqat "Aktiv" bo'lgan ish o'rinlarini eng yangisidan boshlab tortib olamiz
    vacancies = [v async for v in Vacancy.objects.filter(is_active=True).order_by('-created_at')]

    if not vacancies:
        text = (
            "💼 <b>Bo'sh ish o'rinlari:</b>\n\n"
            "Ayni vaqtda Xonobod shahrida aktiv vakansiyalar mavjud emas. Yangi ish o'rinlari qo'shilishi bilan shu yerda ko'rishingiz mumkin!\n\n"
            "<i>Agar o'zingiz ishchi qidirayotgan bo'lsangiz, Asosiy menyudan 'Biznes / Boshqa' bo'limini tanlab e'lon berishingiz mumkin.</i>"
        )
        return await message.answer(text, parse_mode="HTML")

    text = "💼 <b>Xonobod shahridagi dolzarb bo'sh ish o'rinlari:</b>\n\n"
    for i, v in enumerate(vacancies, start=1):
        text += (
            f"<b>{i}. {v.title}</b>\n"
            f"🏢 <b>Korxona:</b> {v.company}\n"
            f"💰 <b>Maosh:</b> {v.salary}\n"
            f"📋 <b>Talablar:</b> {v.requirements}\n"
            f"📞 <b>Aloqa:</b> {v.phone}\n"
            "➖➖➖➖➖➖➖➖\n"
        )

    text += "\n👉 <b>@XonobodBugun</b>"
    await message.answer(text, parse_mode="HTML")


# ==========================================
# 5. OB-HAVO (1 Kunlik va 1 Haftalik)
# ==========================================
@router.message(F.text == "🌤 Ob-havo ma'lumotlari", StateFilter('*'))
async def weather_menu(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌤 Bugun va Ertaga", callback_data="weather_2days")],
        [InlineKeyboardButton(text="📅 1 Haftalik prognoz", callback_data="weather_7days")]
    ])
    await message.answer("👇 <b>Qaysi vaqt uchun ob-havo ma'lumoti kerak?</b>", parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(F.data.startswith("weather_"))
async def process_weather(call: CallbackQuery):
    with suppress(TelegramBadRequest):
        await call.answer("Yuklanmoqda...", show_alert=False)

    days = 2 if call.data == "weather_2days" else 7
    # Xonobod koordinatalari
    lat, lon = 40.8131, 73.0093
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,weathercode&timezone=Asia/Tashkent&forecast_days={days}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    daily = data.get("daily", {})

                    dates = daily.get("time", [])
                    max_temps = daily.get("temperature_2m_max", [])
                    min_temps = daily.get("temperature_2m_min", [])
                    codes = daily.get("weathercode", [])

                    title = "🌤 <b>Bugun va Ertaga</b>" if days == 2 else "📅 <b>1 Haftalik prognoz</b>"
                    text = f"{title} uchun Xonobod shahri ob-havosi:\n\n"

                    # 🛑 YANGI: Ob-havo kodlarini insoniy tilga o'girish
                    def get_weather_desc(code):
                        if code == 0:
                            return "☀️", "Havo ochiq, yog'ingarchilik kutilmaydi."
                        elif code in [1, 2, 3]:
                            return "⛅️", "O'zgaruvchan bulutli, yog'ingarchiliksiz."
                        elif code in [45, 48]:
                            return "🌫", "Tuman tushishi ehtimoli bor."
                        elif code in [51, 53, 55, 56, 57]:
                            return "🌧", "Yengil shabada va mayda yomg'ir yog'ishi mumkin."
                        elif code in [61, 63, 65, 66, 67, 80, 81, 82]:
                            return "🌧", "Yomg'ir yog'ishi kutilmoqda."
                        elif code in [71, 73, 75, 77, 85, 86]:
                            return "❄️", "Qor yog'ishi ehtimoli bor."
                        elif code in [95, 96, 99]:
                            return "⛈", "Momaqaldiroq va kuchli yomg'ir bo'lishi mumkin."
                        return "🌡", "Havo harorati o'zgaruvchan."

                    for i in range(len(dates)):
                        date_str = dates[i]
                        t_max = round(max_temps[i])
                        t_min = round(min_temps[i])
                        emoji, desc = get_weather_desc(codes[i])

                        text += f"🗓 <b>{date_str}</b>\n"
                        text += f"{emoji} Kunduzi: <b>+{t_max}°C</b> | Kechasi: <b>+{t_min}°C</b>\n"
                        text += f"📝 <i>{desc}</i>\n➖➖➖➖➖➖➖➖\n"

                    text += "\n<i>Ma'lumotlar Open-Meteo sun'iy yo'ldoshlaridan olinmoqda.</i>"

                    await call.message.edit_text(text, parse_mode="HTML")
                else:
                    await call.message.edit_text("⚠️ Hozircha ob-havo serveriga ulanib bo'lmadi.")
    except Exception as e:
        logger.error(f"Ob-havo API xatosi: {e}")
        await call.message.edit_text("⚠️ Ob-havo ma'lumotlarini olishda texnik xatolik yuz berdi.")