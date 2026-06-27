from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from bot.models import TelegramUser
from bot.keyboards.reply.main_menu import main_menu_kb

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    username = message.from_user.username

    # Mijozni bazadan izlaymiz yoki yangi yaratamiz
    user, created = await TelegramUser.objects.aget_or_create(
        user_id=user_id,
        defaults={'full_name': full_name, 'username': username}
    )

    # Ismi/Username o'zgargan bo'lsa yangilab qo'yamiz
    if not created and (user.full_name != full_name or user.username != username):
        user.full_name = full_name
        user.username = username
        await user.asave()

    if created:
        text = (
            f"😊 Assalomu alekum {full_name}, @XonobodBugun kanalini rasmiy botiga xush kelibsiz!\n\n"
            f"Quyidagi menyulardan birini tanlang!"
        )
    else:
        text = f"👋 Qaytganingizdan xursandmiz {full_name}, o'zingizga kerakli bo'limni tanlang!"

    await message.answer(text, reply_markup=main_menu_kb)

# A'zo bo'lgach "Tasdiqlash" tugmasini bossa ishlaydigan mantiq
@router.callback_query(F.data == "check_sub")
async def check_sub_confirm(call: CallbackQuery):
    await call.message.delete()
    await cmd_start(call.message)