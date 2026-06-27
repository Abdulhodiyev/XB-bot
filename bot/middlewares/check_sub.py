import logging
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from core.config import CHANNEL_USERNAME

logger = logging.getLogger(__name__)

class CheckSubscriptionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        state = data.get("state")
        if state and await state.get_state():
            return await handler(event, data)

        if isinstance(event, CallbackQuery) and event.data == "check_sub":
            return await handler(event, data)

        if isinstance(event, Message) and event.media_group_id:
            return await handler(event, data)

        user = event.from_user
        bot = data['bot']
        channel_id = CHANNEL_USERNAME if CHANNEL_USERNAME.startswith("@") else f"@{CHANNEL_USERNAME}"

        # 🛑 HIMOYA: Obunani tekshirishni alohida ajratib oldik
        is_subscribed = False
        try:
            member = await bot.get_chat_member(chat_id=channel_id, user_id=user.id)
            status = member.status.value if hasattr(member.status, 'value') else member.status
            if status in ['member', 'administrator', 'creator']:
                is_subscribed = True
        except Exception as e:
            logger.error(f"Telegram API Obuna xatosi: {e}")

        # Agar obunasi bo'lsa, handlerni ishga tushiramiz (Endi handler xatosi qorovulga aralashmaydi!)
        if is_subscribed:
            return await handler(event, data)

        # Agar obunasi yo'q bo'lsa
        text = f"❗️<b>Diqqat!</b> Botdan foydalanish uchun avval {channel_id} kanaliga obuna bo'ling!"
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=f"https://t.me/{channel_id.replace('@', '')}")],
            [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="check_sub")]
        ])

        if isinstance(event, Message):
            await event.answer(text, reply_markup=markup, parse_mode="HTML")
        elif isinstance(event, CallbackQuery):
            await event.message.answer(text, reply_markup=markup, parse_mode="HTML")
            await event.answer()
        return