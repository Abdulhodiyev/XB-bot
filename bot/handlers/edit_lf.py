import logging
from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from bot.models import Advertisement
from bot.states.ad_states import EditLFState
from bot.keyboards.inline.lost_found_inline import get_lf_confirm_kb, get_lf_admin_kb
from bot.keyboards.reply.common_reply import cancel_kb, done_media_kb
from bot.utils.validators import AutoAdValidator
from bot.utils.formatters import format_lost_found_text, get_admin_footer
from bot.utils.media_sender import send_ad_media
from contextlib import suppress

logger = logging.getLogger(__name__)
router = Router()

FIELD_PROMPTS = {
    "item": "📦 <b>Yangi buyum nomini kiriting:</b>", "location": "📍 <b>Yangi joyni kiriting:</b>",
    "info": "📝 <b>Yangi qo'shimcha ma'lumot:</b>", "phone": "📞 <b>Yangi raqam:</b>"
}


@router.callback_query(F.data.startswith("e_lf_"))
async def ask_new_lf_value(call: CallbackQuery, state: FSMContext):
    with suppress(Exception): await call.answer()
    parts = call.data.split("_")
    field, ad_id = parts[2], int(parts[3])
    with suppress(TelegramBadRequest):
        await call.message.edit_reply_markup(reply_markup=None)
    if field == "photo":
        await state.set_state(EditLFState.waiting_for_photo)
        await state.update_data(edit_ad_id=ad_id, media_list=[])
        return await call.message.answer("📸 <b>Yangi rasmlarni yuboring:</b>", parse_mode="HTML",
                                         reply_markup=done_media_kb())

    await state.set_state(EditLFState.waiting_for_text)
    await state.update_data(edit_ad_id=ad_id, edit_field=field)
    await call.message.answer(FIELD_PROMPTS.get(field, "Yangi ma'lumot:"), parse_mode="HTML", reply_markup=cancel_kb())


@router.message(EditLFState.waiting_for_text)
async def process_edit_lf_text(message: Message, state: FSMContext):
    data = await state.get_data()
    field, ad_id, text = data.get("edit_field"), data.get("edit_ad_id"), message.text

    if field == "phone":
        raw_phones = [p.strip() for p in text.split(",") if p.strip()]
        unique_phones = []
        for p in raw_phones:
            if p not in unique_phones: unique_phones.append(p)
        for p in unique_phones:
            is_valid, err = AutoAdValidator.validate_phone(p)
            if not is_valid: return await message.answer(f"❗️ Xato raqam: <b>{p}</b>")
        text = ", ".join(unique_phones)

    try:
        ad = await Advertisement.objects.select_related("user").aget(id=ad_id)
        if field == "phone":
            ad.phone_numbers = text
        else:
            details = ad.details.copy()
            details[field] = text
            ad.details = details
        await ad.asave()
        await state.clear()
        with suppress(Exception):
            await message.answer("✅ <b>Yangilandi!</b>", parse_mode="HTML", reply_markup=ReplyKeyboardRemove())

        formatted_text = format_lost_found_text(ad.details, ad.phone_numbers)

        # 🛑 HIMOYA: ADMIN
        is_admin = message.chat.type in ['group', 'supergroup']
        if is_admin:
            formatted_text += get_admin_footer(ad.user, "Bepul")
            kb = get_lf_admin_kb(ad.id)
        else:
            kb = get_lf_confirm_kb(ad.id)

        sent_ids = await send_ad_media(bot=message.bot, chat_id=message.chat.id,
                                       media_list=ad.details.get("media_list", []), caption=formatted_text,
                                       reply_markup=kb)
        ad.message_ids = sent_ids
        await ad.asave()
    except Exception as e:
        logger.exception(e)


@router.message(EditLFState.waiting_for_photo, F.photo | F.video)
async def accumulate_edit_lf_media(message: Message, state: FSMContext):
    data = await state.get_data()
    media_list = data.get("media_list", [])
    if len(media_list) >= 5: return await message.answer("❗️ Maksimum 5 ta rasm mumkin!")
    media_type = "photo" if message.photo else "video"
    file_id = message.photo[-1].file_id if message.photo else message.video.file_id
    media_list.append({"type": media_type, "file_id": file_id})
    await state.update_data(media_list=media_list)
    if len(media_list) == 1: await message.answer("📸 Qabul qilindi! Yana yuborish mumkin. Tugatgach pastdagi tugmani bosing!", parse_mode="HTML")


@router.message(EditLFState.waiting_for_photo, F.text == "✅ Rasmlar tayyor")
async def finish_edit_lf_media(message: Message, state: FSMContext):
    data = await state.get_data()
    media_list, ad_id = data.get("media_list", []), data.get("edit_ad_id")
    if not media_list: return await message.answer("❗️ Kamida bitta rasm yuboring!")

    try:
        ad = await Advertisement.objects.select_related("user").aget(id=ad_id)
        details = ad.details.copy()
        details["media_list"] = media_list
        ad.details = details
        await ad.asave()
        await state.clear()
        with suppress(Exception):
            await message.answer("✅ <b>Yangilandi!</b>", parse_mode="HTML", reply_markup=ReplyKeyboardRemove())

        formatted_text = format_lost_found_text(ad.details, ad.phone_numbers)

        # 🛑 HIMOYA: ADMIN
        is_admin = message.chat.type in ['group', 'supergroup']
        if is_admin:
            formatted_text += get_admin_footer(ad.user, "Bepul")
            kb = get_lf_admin_kb(ad.id)
        else:
            kb = get_lf_confirm_kb(ad.id)

        sent_ids = await send_ad_media(bot=message.bot, chat_id=message.chat.id, media_list=media_list,
                                       caption=formatted_text, reply_markup=kb)
        ad.message_ids = sent_ids
        await ad.asave()
    except Exception as e:
        logger.exception(e)