import logging
from contextlib import suppress
from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from bot.keyboards.inline.other_inline import get_other_type_kb, get_other_confirm_kb, get_other_edit_kb
from bot.models import TelegramUser, Category, Advertisement
from bot.states.ad_states import OtherAdState, ReadyOtherAdState, EditOtherState
from bot.keyboards.reply.common_reply import cancel_kb, multi_phone_kb, skip_kb, done_media_kb
from bot.utils.media_sender import send_ad_media
from bot.utils.validators import AutoAdValidator
from bot.utils.helpers import is_valid_text
from bot.keyboards.reply.main_menu import main_menu_kb

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "category_other")
async def start_other_ad(call: CallbackQuery, state: FSMContext):
    with suppress(TelegramBadRequest): await call.answer()
    await state.clear()
    await call.message.edit_text("🛒 <b>Boshqa turdagi e'lonlar bo'limi</b>\n\nQanday usulda e'lon bermoqchisiz?",
                                 parse_mode="HTML", reply_markup=get_other_type_kb())


@router.callback_query(F.data == "otype_ready")
async def process_ready_other_ad(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer(
        "✅ <b>Juda yaxshi, tayyor holatdagi e'loningizni yuboring!</b>\n\n<i>(Rasm yoki videoni e'lon matni bilan birga yuboring)</i>",
        parse_mode="HTML", reply_markup=cancel_kb())
    await state.set_state(ReadyOtherAdState.waiting_for_post)


@router.message(ReadyOtherAdState.waiting_for_post)
async def o_ready_post_received(message: Message, state: FSMContext):
    if not (message.text or message.caption): return await message.answer(
        "❗️ Iltimos, e'lon matnini ham yozib yuboring.")
    media_list = []
    if message.photo:
        media_list.append({"type": "photo", "file_id": message.photo[-1].file_id})
    elif message.video:
        media_list.append({"type": "video", "file_id": message.video.file_id})

    raw_text = message.html_text or message.text or ""
    full_text = raw_text + "\n\n👉 <b>@XonobodBugun</b>"
    details_data = {"is_ready_post": True, "business_text": full_text, "media_list": media_list,
                    "custom_admin_text": full_text}

    try:
        user, _ = await TelegramUser.objects.aget_or_create(user_id=message.from_user.id,
                                                            defaults={"full_name": message.from_user.full_name,
                                                                      "username": message.from_user.username})
        category, _ = await Category.objects.aget_or_create(callback_data="category_other",
                                                            defaults={"name": "Boshqa", "is_active": True})
        ad = await Advertisement.objects.acreate(user=user, category=category, details=details_data,
                                                 phone_numbers="Tayyor e'lon", status=Advertisement.Status.DRAFT)

        await message.answer("⏳ E'lon qabul qilindi. Tasdiqlang:", reply_markup=main_menu_kb)
        # 🛑 HIMOYA: Tayyor post bo'lgani uchun is_ready=True beramiz
        kb = get_other_confirm_kb(ad.id, is_ready=True)
        if media_list:
            await send_ad_media(bot=message.bot, chat_id=message.chat.id, media_list=media_list, caption=full_text,
                                reply_markup=kb)
        else:
            await message.answer(text=full_text, parse_mode="HTML", reply_markup=kb)
    except Exception as e:
        logger.exception(e)
        await message.answer("⚠️ Xatolik yuz berdi.")
    finally:
        await state.clear()


@router.callback_query(F.data == "otype_step")
async def process_step_other_ad(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("🛍 <b>Nima sotmoqchisiz?</b>", parse_mode="HTML", reply_markup=cancel_kb())
    await state.set_state(OtherAdState.title)


@router.message(OtherAdState.title)
async def o_title(message: Message, state: FSMContext):
    if not is_valid_text(message.text): return await message.answer("❗️ Iltimos, mahsulot nomini to'g'ri kiriting:")
    await state.update_data(title=message.text)
    await message.answer("✍️ <b>Qo'shimcha ma'lumotlar:</b>\n<i>(Ixtiyoriy. O'tkazib yuborishingiz mumkin)</i>",
                         parse_mode="HTML", reply_markup=skip_kb())
    await state.set_state(OtherAdState.info)


@router.message(OtherAdState.info)
async def o_info(message: Message, state: FSMContext):
    text = message.text
    info = "" if text == "⏭ O'tkazib yuborish" else text
    if info and not is_valid_text(info): return await message.answer(
        "❗️ Matnni to'g'ri kiriting yoki o'tkazib yuboring:")
    await state.update_data(info=info)
    await message.answer("💰 <b>Narxini kiriting:</b>", parse_mode="HTML", reply_markup=cancel_kb())
    await state.set_state(OtherAdState.price)


@router.message(OtherAdState.price)
async def o_price(message: Message, state: FSMContext):
    is_valid, err = AutoAdValidator.validate_price(message.text)
    if not is_valid: return await message.answer(err)
    await state.update_data(price=message.text, phones=[], media_list=[])
    await message.answer("☎️ <b>Telefon raqamingizni kiriting:</b>\n\n<i>📱 Bitta raqam yuborish uchun pastdagi tugmani bosing.\n✍️ Yana raqam qo'shmoqchi bo'lsangiz, yozib yuborishingiz mumkin.</i>", reply_markup=multi_phone_kb(),
                         parse_mode="HTML")
    await state.set_state(OtherAdState.phone)


@router.message(OtherAdState.phone)
async def o_phone(message: Message, state: FSMContext):
    data = await state.get_data()
    phones = data.get("phones", [])

    if message.text == "➡️ Keyingi qadam (Manzilga o'tish)":
        if not phones: return await message.answer("❗️ Iltimos, kamida bitta telefon raqam kiriting!")
        await message.answer("📍 <b>Manzilni kiriting:</b>\n<i>(Masalan: Xonobod shahar)</i>", parse_mode="HTML",
                             reply_markup=cancel_kb())
        await state.set_state(OtherAdState.location)
        return

    phone = message.contact.phone_number if message.contact else message.text
    is_valid, err = AutoAdValidator.validate_phone(phone)
    if not is_valid: return await message.answer(err)

    if phone not in phones:
        phones.append(phone)
        await state.update_data(phones=phones)
        await message.answer(f"✅ Raqam qo'shildi: <b>{phone}</b>\nDavom etish uchun <b>Keyingi qadam</b> ni bosing.",
                             parse_mode="HTML")


@router.message(OtherAdState.location)
async def o_location(message: Message, state: FSMContext):
    if not is_valid_text(message.text): return await message.answer("❗️ Manzilni to'g'ri kiriting:")
    await state.update_data(location=message.text)
    await message.answer(
        "📸 <b>E'lon rasmi yoki videolarini yuboring:</b>\n\n<i>Barcha rasmlarni yuborib bo'lsangiz, pastdagi <b>✅ Rasmlar tayyor</b> tugmasini bosing.</i>",
        parse_mode="HTML", reply_markup=cancel_kb())
    await state.set_state(OtherAdState.photos)


@router.message(OtherAdState.photos, F.photo | F.video)
async def o_photos(message: Message, state: FSMContext):
    data = await state.get_data()
    media_list = data.get("media_list", [])
    if len(media_list) >= 10: return await message.answer("❗️ Maksimum 10 ta rasm/video mumkin!")
    media_type = "photo" if message.photo else "video"
    file_id = message.photo[-1].file_id if message.photo else message.video.file_id
    media_list.append({"type": media_type, "file_id": file_id})
    await state.update_data(media_list=media_list)
    if len(media_list) == 1: await message.answer(
        "📸 Qabul qilindi! Yana yuboring yoki <b>✅ Rasmlar tayyor</b> ni bosing.", reply_markup=done_media_kb(),
        parse_mode="HTML")


@router.message(OtherAdState.photos, F.text == "✅ Rasmlar tayyor")
async def finish_other_media(message: Message, state: FSMContext):
    data = await state.get_data()
    media_list = data.get("media_list", [])
    if not media_list: return await message.answer("❗️ Iltimos, kamida bitta rasm yoki video yuboring.")
    if data.get("is_submitting"): return await message.answer("⏳ E'lon saqlanmoqda, iltimos kuting...")
    await state.update_data(is_submitting=True)

    await message.answer("⏳ E'loningiz tayyorlanmoqda...", reply_markup=main_menu_kb)
    from bot.utils.formatters import format_other_text
    details_data = {
        "title": data.get("title"), "info": data.get("info"), "price": data.get("price"),
        "location": data.get("location"), "media_list": media_list
    }
    phones_str = ", ".join(data.get("phones", []))
    full_text = format_other_text(details_data, phones_str)
    details_data["custom_admin_text"] = full_text

    try:
        user, _ = await TelegramUser.objects.aget_or_create(user_id=message.from_user.id,
                                                            defaults={"full_name": message.from_user.full_name,
                                                                      "username": message.from_user.username})
        category, _ = await Category.objects.aget_or_create(callback_data="category_other",
                                                            defaults={"name": "Boshqa", "is_active": True})
        ad = await Advertisement.objects.acreate(user=user, category=category, details=details_data,
                                                 phone_numbers=phones_str, status=Advertisement.Status.DRAFT)

        # 🛑 HIMOYA: Qadamma-qadam terilgani uchun is_ready=False bo'ladi
        kb = get_other_confirm_kb(ad.id, is_ready=False)
        await send_ad_media(bot=message.bot, chat_id=message.chat.id, media_list=media_list, caption=full_text,
                            reply_markup=kb)
    except Exception as e:
        logger.exception(f"Boshqa e'lon saqlashda xato: {e}")
        await message.answer("⚠️ Texnik xatolik yuz berdi.")
    finally:
        await state.clear()


# ==========================================
# 🛑 BOSHQA E'LON TAYYORLASH (TAHRIRLASH) QISMI 🛑
# ==========================================
FIELD_PROMPTS = {
    "title": "🛍 <b>Yangi mahsulot nomini kiriting:</b>",
    "info": "✍️ <b>Yangi qo'shimcha ma'lumot kiriting:</b>",
    "price": "💰 <b>Yangi narxni kiriting:</b>",
    "phone": "☎️ <b>Yangi telefon raqamlarini kiriting:</b>\n<i>(Vergul bilan yozing)</i>",
    "location": "📍 <b>Yangi manzilni kiriting:</b>"
}


@router.callback_query(F.data.startswith("e_other_"))
async def ask_new_other_value(call: CallbackQuery, state: FSMContext):
    with suppress(TelegramBadRequest): await call.answer()
    parts = call.data.split("_")
    field, ad_id = parts[2], int(parts[3])
    with suppress(TelegramBadRequest):
        await call.message.edit_reply_markup(reply_markup=None)
    if field == "photo":
        await state.set_state(EditOtherState.waiting_for_photo)
        await state.update_data(edit_ad_id=ad_id, media_list=[])
        return await call.message.answer("📸 <b>Yangi rasm/videolarni yuboring:</b>", parse_mode="HTML",
                                         reply_markup=done_media_kb())

    await state.set_state(EditOtherState.waiting_for_text)
    await state.update_data(edit_ad_id=ad_id, edit_field=field)
    await call.message.answer(FIELD_PROMPTS.get(field, "Yangi ma'lumotni kiriting:"), parse_mode="HTML",
                              reply_markup=cancel_kb())


@router.message(EditOtherState.waiting_for_text)
async def process_edit_other_text(message: Message, state: FSMContext):
    data = await state.get_data()
    field, ad_id, text = data.get("edit_field"), data.get("edit_ad_id"), message.text

    if field != "info" and len(text.strip()) < 2: return await message.answer("❗️ Iltimos, to'liqroq kiriting.")
    if field == "price":
        is_valid, err = AutoAdValidator.validate_price(text)
        if not is_valid: return await message.answer(err)
    elif field == "phone":
        raw_phones = [p.strip() for p in text.split(",") if p.strip()]
        if not raw_phones: return await message.answer("❗️ Iltimos, raqam kiriting.")
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

        from bot.utils.formatters import format_other_text
        formatted_text = format_other_text(ad.details, ad.phone_numbers)

        is_admin = message.chat.type in ['group', 'supergroup']
        if is_admin:
            from bot.keyboards.inline.other_inline import get_other_admin_kb
            from bot.utils.formatters import get_admin_footer
            formatted_text += get_admin_footer(ad.user, ad.details.get("tariff", "Kelishilgan"))
            kb = get_other_admin_kb(ad.id)
        else:
            kb = get_other_confirm_kb(ad.id, is_ready=False)

        sent_ids = await send_ad_media(bot=message.bot, chat_id=message.chat.id,
                                       media_list=ad.details.get("media_list", []), caption=formatted_text,
                                       reply_markup=kb)
        ad.message_ids = sent_ids
        await ad.asave()
    except Exception as e:
        logger.exception(e)


@router.message(EditOtherState.waiting_for_photo, F.photo | F.video)
async def accumulate_edit_other_media(message: Message, state: FSMContext):
    data = await state.get_data()
    media_list = data.get("media_list", [])
    if len(media_list) >= 10: return await message.answer("❗️ Maksimum 10 ta rasm/video mumkin!")
    media_type = "photo" if message.photo else "video"
    file_id = message.photo[-1].file_id if message.photo else message.video.file_id
    media_list.append({"type": media_type, "file_id": file_id})
    await state.update_data(media_list=media_list)
    if len(media_list) == 1: await message.answer("📸 Qabul qilindi! Yana yuborishingiz mumkin.", parse_mode="HTML")


@router.message(EditOtherState.waiting_for_photo, F.text == "✅ Rasmlar tayyor")
async def finish_edit_other_media(message: Message, state: FSMContext):
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

        from bot.utils.formatters import format_other_text
        formatted_text = format_other_text(ad.details, ad.phone_numbers)

        is_admin = message.chat.type in ['group', 'supergroup']
        if is_admin:
            from bot.keyboards.inline.other_inline import get_other_admin_kb
            from bot.utils.formatters import get_admin_footer
            formatted_text += get_admin_footer(ad.user, ad.details.get("tariff", "Kelishilgan"))
            kb = get_other_admin_kb(ad.id)
        else:
            kb = get_other_confirm_kb(ad.id, is_ready=False)

        sent_ids = await send_ad_media(bot=message.bot, chat_id=message.chat.id, media_list=media_list,
                                       caption=formatted_text, reply_markup=kb)
        ad.message_ids = sent_ids
        await ad.asave()
    except Exception as e:
        logger.exception(e)