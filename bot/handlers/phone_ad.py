import logging
from contextlib import suppress

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from bot.keyboards.inline.phone_inline import get_phone_confirm_kb
from bot.models import TelegramUser, Category, Advertisement
from bot.states.ad_states import PhoneAdState
from bot.keyboards.reply.common_reply import cancel_kb, multi_phone_kb, skip_kb, done_media_kb
from bot.utils.media_sender import send_ad_media  # 🛑 USER_MEDIA_CACHE OLIB TASHLANDI
from bot.utils.validators import AutoAdValidator
from bot.utils.helpers import is_valid_text

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(F.data == "category_phone")
async def start_phone_ad(call: CallbackQuery, state: FSMContext):
    with suppress(TelegramBadRequest):
        await call.answer()
        await call.message.delete()
    await call.message.answer("📱 <b>Telefon rusumini kiriting</b>\n<i>(Masalan: iPhone 13 Pro yoki Samsung S23 Ultra):</i>", parse_mode="HTML", reply_markup=cancel_kb())
    await state.set_state(PhoneAdState.model)

@router.message(PhoneAdState.model)
async def p_model(message: Message, state: FSMContext):
    if not is_valid_text(message.text): return await message.answer("❗️ Iltimos, rusumni to'g'ri kiriting:")
    await state.update_data(model=message.text)
    await message.answer("💾 <b>Xotirasini kiriting:</b>\n<i>(Masalan: 128 GB yoki 8/256 GB)</i>", parse_mode="HTML")
    await state.set_state(PhoneAdState.memory)

@router.message(PhoneAdState.memory)
async def p_memory(message: Message, state: FSMContext):
    if not is_valid_text(message.text): return await message.answer("❗️ Iltimos, xotirani to'g'ri kiriting:")
    await state.update_data(memory=message.text)
    await message.answer("🛠 <b>Holati qanday?</b>\n<i>(Masalan: Yangi, Ideal, Ekrani singan)</i>", parse_mode="HTML")
    await state.set_state(PhoneAdState.condition)

@router.message(PhoneAdState.condition)
async def p_condition(message: Message, state: FSMContext):
    if not is_valid_text(message.text): return await message.answer("❗️ Iltimos, holatini to'g'ri kiriting:")
    await state.update_data(condition=message.text)
    await message.answer("📦 <b>Karobka va Dokument bormi?</b>\n<i>(Masalan: Bor, Yo'q, Pasport nusxa beraman)</i>", parse_mode="HTML")
    await state.set_state(PhoneAdState.box_docs)

@router.message(PhoneAdState.box_docs)
async def p_box_docs(message: Message, state: FSMContext):
    if not is_valid_text(message.text): return await message.answer("❗️ Iltimos, ma'lumotni to'g'ri yozing:")
    await state.update_data(box_docs=message.text)
    await message.answer("✍️ <b>Qo'shimcha ma'lumotlar:</b>\n<i>(Ixtiyoriy. O'tkazib yuborishingiz mumkin)</i>", parse_mode="HTML", reply_markup=skip_kb())
    await state.set_state(PhoneAdState.info)

@router.message(PhoneAdState.info)
async def p_info(message: Message, state: FSMContext):
    text = message.text
    info = "" if text == "⏭ O'tkazib yuborish" else text
    if info and not is_valid_text(info): return await message.answer("❗️ Matnni to'g'ri kiriting yoki o'tkazib yuboring:")
    await state.update_data(info=info)
    await message.answer("💰 <b>Narxini kiriting:</b>\n<i>(Masalan: 400$ yoki Kelishamiz)</i>", parse_mode="HTML", reply_markup=cancel_kb())
    await state.set_state(PhoneAdState.price)

@router.message(PhoneAdState.price)
async def p_price(message: Message, state: FSMContext):
    is_valid, err = AutoAdValidator.validate_price(message.text)
    if not is_valid: return await message.answer(err)

    # 🛑 YANGI MEDIA XOTIRASI OCHILDI
    await state.update_data(price=message.text, phones=[], media_list=[])
    await message.answer("☎️ <b>Telefon raqamingizni kiriting:</b>\n\n<i>📱 Bitta raqam yuborish uchun pastdagi tugmani bosing.\n✍️ Yana raqam qo'shmoqchi bo'lsangiz, yozib yuborishingiz mumkin.</i>", reply_markup=multi_phone_kb(), parse_mode="HTML")
    await state.set_state(PhoneAdState.phone)

@router.message(PhoneAdState.phone)
async def p_phone(message: Message, state: FSMContext):
    data = await state.get_data()
    phones = data.get("phones", [])

    if message.text == "➡️ Keyingi qadam (Manzilga o'tish)":
        if not phones: return await message.answer("❗️ Iltimos, kamida bitta telefon raqam kiriting!")
        await message.answer("📍 <b>Manzilni kiriting:</b>\n<i>(Masalan: Xonobod shahar, bozor pastida)</i>", parse_mode="HTML", reply_markup=cancel_kb())
        await state.set_state(PhoneAdState.location)
        return

    phone = message.contact.phone_number if message.contact else message.text
    is_valid, err = AutoAdValidator.validate_phone(phone)
    if not is_valid: return await message.answer(err)

    if phone not in phones:
        phones.append(phone)
        await state.update_data(phones=phones)
        await message.answer(f"✅ Raqam qo'shildi: <b>{phone}</b>\nDavom etish uchun <b>Keyingi qadam</b> ni bosing.", parse_mode="HTML")
    else:
        await message.answer("❗️ Bu raqam allaqachon qo'shilgan!")

@router.message(PhoneAdState.location)
async def p_location(message: Message, state: FSMContext):
    if not is_valid_text(message.text): return await message.answer("❗️ Manzilni to'g'ri kiriting:")
    await state.update_data(location=message.text)
    await message.answer("📸 <b>Telefon rasm yoki videolarini yuboring:</b>\n\n<i>Barcha rasmlarni yuborib bo'lsangiz, pastdagi <b>✅ Rasmlar tayyor</b> tugmasini bosing.</i>", parse_mode="HTML", reply_markup=cancel_kb())
    await state.set_state(PhoneAdState.photos)

# ==========================================
# 🛑 RASMLARNI YIG'ISH (FSM ORQALI)
# ==========================================
@router.message(PhoneAdState.photos, F.photo | F.video)
async def p_photos(message: Message, state: FSMContext):
    data = await state.get_data()
    media_list = data.get("media_list", [])

    if len(media_list) >= 10: return await message.answer("❗️ Maksimum 10 ta rasm yoki video yuborish mumkin!")

    media_type = "photo" if message.photo else "video"
    file_id = message.photo[-1].file_id if message.photo else message.video.file_id
    media_list.append({"type": media_type, "file_id": file_id})
    await state.update_data(media_list=media_list)

    if len(media_list) == 1:
        await message.answer("📸 Qabul qilindi! Yana yuborishingiz mumkin.\nTugatganingizdan so'ng pastdagi <b>✅ Rasmlar tayyor</b> tugmasini bosing.", reply_markup=done_media_kb(), parse_mode="HTML")

@router.message(PhoneAdState.photos, F.text == "✅ Rasmlar tayyor")
async def finish_phone_media(message: Message, state: FSMContext):
    data = await state.get_data()
    media_list = data.get("media_list", [])

    if not media_list: return await message.answer("❗️ Iltimos, kamida bitta rasm yoki video yuboring.")
    if data.get("is_submitting"): return await message.answer("⏳ E'lon saqlanmoqda, iltimos kuting...")
    await state.update_data(is_submitting=True)

    await message.answer("⏳ E'loningiz tayyorlanmoqda...", reply_markup=ReplyKeyboardRemove())

    from bot.utils.formatters import format_phone_text
    details_data = {
        "model": data.get("model"), "memory": data.get("memory"), "condition": data.get("condition"),
        "box_docs": data.get("box_docs"), "info": data.get("info"), "price": data.get("price"),
        "location": data.get("location"), "media_list": media_list
    }
    phones_str = ", ".join(data.get("phones", []))
    full_text = format_phone_text(details_data, phones_str)
    details_data["custom_admin_text"] = full_text

    try:
        user, _ = await TelegramUser.objects.aget_or_create(
            user_id=message.from_user.id,
            defaults={"full_name": message.from_user.full_name, "username": message.from_user.username}
        )
        category, _ = await Category.objects.aget_or_create(callback_data="category_phone", defaults={"name": "Telefon", "is_active": True})
        ad = await Advertisement.objects.acreate(user=user, category=category, details=details_data, phone_numbers=phones_str, status=Advertisement.Status.DRAFT)

        await send_ad_media(bot=message.bot, chat_id=message.chat.id, media_list=media_list, caption=full_text, reply_markup=get_phone_confirm_kb(ad.id))
    except Exception as e:
        logger.exception(f"Telefon e'lon saqlashda xato: {e}")
        await message.answer("⚠️ Texnik xatolik yuz berdi.")
    finally:
        await state.clear()