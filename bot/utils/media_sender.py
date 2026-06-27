from aiogram import Bot
from aiogram.types import InputMediaPhoto, InputMediaVideo


async def send_ad_media(bot: Bot, chat_id: int | str, media_list: list, caption: str, reply_markup=None):
    if not media_list:
        return []

    if len(media_list) == 1:
        media = media_list[0]
        if media["type"] == "photo":
            msg = await bot.send_photo(chat_id=chat_id, photo=media["file_id"], caption=caption,
                                       reply_markup=reply_markup, parse_mode="HTML")
        else:
            msg = await bot.send_video(chat_id=chat_id, video=media["file_id"], caption=caption,
                                       reply_markup=reply_markup, parse_mode="HTML")
        return [msg.message_id]

    media_group = []
    for i, media in enumerate(media_list):
        cap = caption if i == 0 else None
        if media["type"] == "photo":
            media_group.append(InputMediaPhoto(media=media["file_id"], caption=cap, parse_mode="HTML"))
        else:
            media_group.append(InputMediaVideo(media=media["file_id"], caption=cap, parse_mode="HTML"))

    msgs = await bot.send_media_group(chat_id=chat_id, media=media_group)
    sent_ids = [m.message_id for m in msgs]

    # Telegram MediaGroup ichida tugmani qabul qilmagani uchun alohida text yuboramiz
    if reply_markup:
        markup_msg = await bot.send_message(chat_id=chat_id, text="<b>Harakatni tanlang:</b>",
                                            reply_markup=reply_markup, parse_mode="HTML")
        sent_ids.append(markup_msg.message_id)

    return sent_ids