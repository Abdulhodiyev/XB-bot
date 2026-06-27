import logging
from contextlib import suppress
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from bot.models import Advertisement
from bot.states.ad_states import EditAutoState
from bot.keyboards.inline.auto_inline import get_auto_edit_kb, get_user_confirm_kb, get_admin_action_kb
from bot.keyboards.reply.common_reply import cancel_kb, done_media_kb
from bot.utils.validators import AutoAdValidator
from bot.utils.formatters import format_auto_text, get_admin_footer
from bot.utils.media_sender import send_ad_media

logger = logging.getLogger(__name__)
router = Router()

FIELD_PROMPTS = {
    "model": "🚗 <b>Yangi avtomobil rusumini kiriting:</b>",
    "year": "📅 <b>Yangi yilni kiriting:</b>",
    "distance": "📟 <b>Yangi probegni kiriting:</b>",
    "coat": "🎨 <b>Kraska holatini yangilang:</b>",
    "condition": "⚙️ <b>Texnik holatni yangilang:</b>",
    "oil": "⛽️ <b>Yangi yoqilg'i turini kiriting:</b>",
    "price": "💰 <b>Yangi narxni kiriting:</b>",
    "phone_numbers": "☎️ <b>Yangi telefon raqamlarini kiriting:</b>\n<i>(Vergul bilan ajratib yozing)</i>",
    "info": "✍️ <b>Yangi qo'shimcha ma'lumotni kiriting:</b>",
    "location": "📍 <b>Yangi manzilni kiriting:</b>"
}


@router.callback_query(F.data.startswith("user_edit_"))
@router.callback_query(F.data.startswith("e_auto_"))
async def handle_auto_edit_callbacks(call: CallbackQuery, state: FSMContext):
    with suppress(TelegramBadRequest):
        await call.answer()

    if call.data.startswith("user_edit_"):
        ad_id = int(call.data.split("_")[-1])
        if call.message.text:
            await call.message.edit_text("<b>Qaysi ma'lumotni o'zgartirmoqchisiz?</b>", parse_mode="HTML",
                                         reply_markup=get_auto_edit_kb(ad_id))
        else:
            await call.message.edit_reply_markup(reply_markup=get_auto_edit_kb(ad_id))
        return

    parts = call.data.split("_")
    field = parts[2]
    if field == "phone" and parts[3] == "numbers":
        field = "phone_numbers"
        ad_id = int(parts[4])
    else:
        ad_id = int(parts[3])

    with suppress(TelegramBadRequest):
        await call.message.edit_reply_markup(reply_markup=None)
    is_admin = call.message.chat.type in ['group', 'supergroup']

    if field == "photo":
        await state.set_state(EditAutoState.waiting_for_photo)
        await state.update_data(edit_ad_id=ad_id, media_list=[])
        return await call.message.answer(
            "📸 <b>Yangi rasm/videolarni yuboring:</b>\n\nTugatgach, tayyor tugmasini bosing.",
            parse_mode="HTML", reply_markup=done_media_kb())

    await state.set_state(EditAutoState.waiting_for_text)
    await state.update_data(edit_ad_id=ad_id, edit_field=field)
    await call.message.answer(FIELD_PROMPTS.get(field, "Yangi ma'lumotni kiriting:"), parse_mode="HTML",
                              reply_markup=cancel_kb())


@router.message(EditAutoState.waiting_for_text)
async def process_edit_text(message: Message, state: FSMContext):
    data = await state.get_data()
    field, ad_id, text = data.get("edit_field"), data.get("edit_ad_id"), message.text

    if field != "info" and len(text.strip()) < 2: return await message.answer(
        "❗️ Iltimos, ma'lumotni to'liqroq kiriting.")
    if field == "price":
        is_valid, err = AutoAdValidator.validate_price(text)
        if not is_valid: return await message.answer(err)
    elif field == "year":
        is_valid, err = AutoAdValidator.validate_year(text)
        if not is_valid: return await message.answer(err)
    elif field == "distance":
        is_valid, err = AutoAdValidator.validate_distance(text)
        if not is_valid: return await message.answer(err)
    elif field == "phone_numbers":
        raw_phones = [p.strip() for p in text.split(",") if p.strip()]
        if not raw_phones: return await message.answer("❗️ Iltimos, kamida bitta raqam kiriting.")
        unique_phones = []
        for p in raw_phones:
            if p not in unique_phones: unique_phones.append(p)
        for p in unique_phones:
            is_valid, err = AutoAdValidator.validate_phone(p)
            if not is_valid: return await message.answer(f"❗️ Xato raqam: <b>{p}</b>", parse_mode="HTML")
        text = ", ".join(unique_phones)

    try:
        ad = await Advertisement.objects.select_related("user").aget(id=ad_id)
        if field == "phone_numbers":
            ad.phone_numbers = text
        else:
            details = ad.details.copy()
            details[field] = text
            ad.details = details

        await ad.asave()
        await state.clear()

        with suppress(Exception):
            await message.answer("✅ <b>Yangilandi!</b>", parse_mode="HTML", reply_markup=ReplyKeyboardRemove())

        formatted_text = format_auto_text(ad.details, ad.phone_numbers)

        # 🛑 HIMOYA: ADMIN UCHUN TASDIQLASH CHIQMASLIGI TA'MINLANDI
        is_admin = message.chat.type in ['group', 'supergroup']
        if is_admin:
            formatted_text += get_admin_footer(ad.user, ad.details.get("tariff", "Kelishilgan"))
            kb = get_admin_action_kb(ad.id)
        else:
            kb = get_user_confirm_kb(ad.id)

        sent_ids = await send_ad_media(bot=message.bot, chat_id=message.chat.id,
                                       media_list=ad.details.get("media_list", []), caption=formatted_text,
                                       reply_markup=kb)
        ad.message_ids = sent_ids
        await ad.asave()
    except Exception as e:
        logger.exception(e)
        await message.answer("⚠️ Xatolik yuz berdi.")


@router.message(EditAutoState.waiting_for_photo, F.photo | F.video)
async def accumulate_edit_media(message: Message, state: FSMContext):
    data = await state.get_data()
    user_media = data.get("media_list", [])
    if len(user_media) >= 10: return await message.answer("❗️ Maksimum 10 ta.")
    media_type = "photo" if message.photo else "video"
    file_id = message.photo[-1].file_id if message.photo else message.video.file_id
    user_media.append({"type": media_type, "file_id": file_id})
    await state.update_data(media_list=user_media)
    if len(user_media) == 1: await message.answer("📸 Qabul qilindi! Yana yuborish mumkin.", parse_mode="HTML")


@router.message(EditAutoState.waiting_for_photo, F.text == "✅ Rasmlar tayyor")
async def finish_edit_media(message: Message, state: FSMContext):
    data = await state.get_data()
    media_list, ad_id = data.get("media_list", []), data.get("edit_ad_id")
    if not media_list: return await message.answer("❗️ Rasm yuboring!")

    try:
        ad = await Advertisement.objects.select_related("user").aget(id=ad_id)
        details = ad.details.copy()
        details["media_list"] = media_list
        ad.details = details
        await ad.asave()
        await state.clear()

        with suppress(Exception):
            await message.answer("✅ <b>Yangilandi!</b>", parse_mode="HTML", reply_markup=ReplyKeyboardRemove())

        formatted_text = format_auto_text(ad.details, ad.phone_numbers)

        # 🛑 HIMOYA: ADMIN
        is_admin = message.chat.type in ['group', 'supergroup']
        if is_admin:
            formatted_text += get_admin_footer(ad.user, ad.details.get("tariff", "Kelishilgan"))
            kb = get_admin_action_kb(ad.id)
        else:
            kb = get_user_confirm_kb(ad.id)

        sent_ids = await send_ad_media(bot=message.bot, chat_id=message.chat.id, media_list=media_list,
                                       caption=formatted_text, reply_markup=kb)
        ad.message_ids = sent_ids
        await ad.asave()
    except Exception as e:
        logger.exception(e)