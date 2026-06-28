from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from bot.models import TelegramUser
from bot.keyboards.reply.main_menu import main_menu_kb

router = Router()

# Salomlashish va DB ga yozishni umumiy funksiyaga oldik
async def get_greeting_text(user_info):
    # Mijozni bazadan izlaymiz yoki yangi yaratamiz
    user, created = await TelegramUser.objects.aget_or_create(
        user_id=user_info.id,
        defaults={'full_name': user_info.full_name, 'username': user_info.username}
    )

    # Ismi/Username o'zgargan bo'lsa yangilab qo'yamiz
    if not created and (user.full_name != user_info.full_name or user.username != user_info.username):
        user.full_name = user_info.full_name
        user.username = user_info.username
        await user.asave()

    if created:
        return f"😊 Assalomu alekum {user_info.full_name}, @XonobodBugun kanalini rasmiy botiga xush kelibsiz!\n\nQuyidagi menyulardan birini tanlang!"
    return f"👋 Qaytganingizdan xursandmiz {user_info.full_name}, o'zingizga kerakli bo'limni tanlang!"

@router.message(CommandStart())
async def cmd_start(message: Message):
    # Bu /start bosganda ishlaydi
    text = await get_greeting_text(message.from_user)
    await message.answer(text, reply_markup=main_menu_kb)

@router.callback_query(F.data == "check_sub")
async def check_sub_confirm(call: CallbackQuery):
    # Bu tasdiqlash bosilganda ishlaydi
    await call.message.delete() # Majburiy obuna xabarini o'chiramiz
    text = await get_greeting_text(call.from_user)
    await call.message.answer(text, reply_markup=main_menu_kb)
    await call.answer()