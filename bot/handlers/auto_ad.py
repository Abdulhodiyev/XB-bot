import logging
from contextlib import suppress

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from bot.keyboards.inline.auto_inline import get_user_confirm_kb, get_admin_action_kb
from bot.keyboards.reply.main_menu import main_menu_kb
from bot.models import TelegramUser, Category, Advertisement
from bot.states.ad_states import AutoAdState
from bot.keyboards.reply.common_reply import cancel_kb, multi_phone_kb, skip_kb
from bot.utils.formatters import format_auto_text
from bot.utils.media_sender import send_ad_media  # 🛑 USER_MEDIA_CACHE OLIB TASHLANDI
from bot.utils.validators import AutoAdValidator
from bot.utils.helpers import is_valid_text

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(F.data == "category_auto")
async def start_auto_ad(call: CallbackQuery, state: FSMContext):
    with suppress(TelegramBadRequest):
        await call.answer()
        await call.message.delete()
    await call.message.answer("🚗 <b>Avtomobil rusumini kiriting</b>\n<i>(Masalan: Matiz Best):</i>", parse_mode="HTML", reply_markup=cancel_kb())
    await state.set_state(AutoAdState.model)

@router.message(AutoAdState.model)
async def process_auto_model(message: Message, state: FSMContext):
    if not is_valid_text(message.text): return await message.answer("❗️ Iltimos, rusumni to'g'ri kiriting (menyuni bosmang):")
    is_valid, err = AutoAdValidator.validate_model(message.text)
    if not is_valid: return await message.answer(err)
    await state.update_data(model=message.text)
    await message.answer("📅 <b>Avtomobil yilini kiriting</b>\n<i>(Masalan: 2020):</i>")
    await state.set_state(AutoAdState.year)

@router.message(AutoAdState.year)
async def process_auto_year(message: Message, state: FSMContext):
    is_valid, err = AutoAdValidator.validate_year(message.text)
    if not is_valid: return await message.answer(err)
    await state.update_data(year=message.text)
    await message.answer("📟 Yurgani (Probeg qancha)?")
    await state.set_state(AutoAdState.distance)

@router.message(AutoAdState.distance)
async def process_auto_distance(message: Message, state: FSMContext):
    is_valid, err = AutoAdValidator.validate_distance(message.text)
    if not is_valid: return await message.answer(err)
    await state.update_data(distance=message.text)
    await message.answer("🎨 Kraska holati qanday?")
    await state.set_state(AutoAdState.coat)

@router.message(AutoAdState.coat)
async def process_auto_coat(message: Message, state: FSMContext):
    if not is_valid_text(message.text): return await message.answer("❗️ Kraska holatini to'g'ri kiriting:")
    await state.update_data(coat=message.text)
    await message.answer("⚙️ Texnik holati qanday?")
    await state.set_state(AutoAdState.condition)

@router.message(AutoAdState.condition)
async def process_auto_condition(message: Message, state: FSMContext):
    if not is_valid_text(message.text): return await message.answer("❗️ Texnik holatini to'g'ri kiriting:")
    await state.update_data(condition=message.text)
    await message.answer("⛽️ Yoqilg'i turi (Benzin, Gaz, Propan)?")
    await state.set_state(AutoAdState.oil)

@router.message(AutoAdState.oil)
async def process_auto_oil(message: Message, state: FSMContext):
    if not is_valid_text(message.text): return await message.answer("❗️ Yoqilg'ini to'g'ri kiriting:")
    await state.update_data(oil=message.text)
    await message.answer("✍️ Qo'shimcha ma'lumot? (Yoki o'tkazib yuboring)", reply_markup=skip_kb())
    await state.set_state(AutoAdState.info)

@router.message(AutoAdState.info)
async def process_auto_info(message: Message, state: FSMContext):
    text = message.text
    info = "" if text == "⏭ O'tkazib yuborish" else text
    if info and not is_valid_text(info): return await message.answer("❗️ Matnni to'g'ri kiriting yoki o'tkazib yuboring:")
    await state.update_data(info=info)
    await message.answer("💰 Narxini kiriting:", reply_markup=cancel_kb())
    await state.set_state(AutoAdState.price)

@router.message(AutoAdState.price)
async def process_auto_price(message: Message, state: FSMContext):
    is_valid, err = AutoAdValidator.validate_price(message.text)
    if not is_valid: return await message.answer(err)
    await state.update_data(price=message.text, phones=[], media_list=[]) # 🛑 XAVFSIZ XOTIRA TAYYORLANDI
    await message.answer("☎️ <b>Telefon raqamingizni kiriting:</b>\n\n<i>📱 Bitta raqam yuborish uchun pastdagi tugmani bosing.\n✍️ Yana raqam qo'shmoqchi bo'lsangiz, yozib yuborishingiz mumkin.</i>", reply_markup=multi_phone_kb(), parse_mode="HTML")
    await state.set_state(AutoAdState.phone)

@router.message(AutoAdState.phone)
async def process_auto_phone(message: Message, state: FSMContext):
    data = await state.get_data()
    phones = data.get("phones", [])
    if message.text == "➡️ Keyingi qadam (Manzilga o'tish)":
        if not phones: return await message.answer("❗️ Iltimos, kamida bitta telefon raqam kiriting!")
        await message.answer("📍 Manzilni kiriting (Masalan: Xonobod shahar):", reply_markup=cancel_kb())
        await state.set_state(AutoAdState.location)
        return

    phone = message.contact.phone_number if message.contact else message.text
    is_valid, err = AutoAdValidator.validate_phone(phone)
    if not is_valid: return await message.answer(err)

    if phone not in phones:
        phones.append(phone)
        await state.update_data(phones=phones)

    await message.answer(f"✅ Raqam qo'shildi: <b>{phone}</b>\n\nYana raqam qo'shasizmi yoki keyingi qadamga o'tamizmi?", reply_markup=multi_phone_kb(), parse_mode="HTML")

@router.message(AutoAdState.location)
async def process_auto_location(message: Message, state: FSMContext):
    if not is_valid_text(message.text): return await message.answer("❗️ Manzilni to'g'ri kiriting:")
    await state.update_data(location=message.text)
    await message.answer("📸 <b>Avtomobil rasm yoki videolarini yuboring:</b>\n\n<i>Barcha rasmlarni yuborib bo'lsangiz, pastdagi <b>✅ Rasmlar tayyor</b> tugmasini bosing.</i>", parse_mode="HTML", reply_markup=cancel_kb())
    await state.set_state(AutoAdState.photo)

# ==========================================
# 🛑 RASM YIG'ISH (FSM XOTIRA ORQALI)
# ==========================================
@router.message(AutoAdState.photo, F.photo | F.video)
async def accumulate_auto_media(message: Message, state: FSMContext):
    data = await state.get_data()
    user_media = data.get("media_list", [])

    if len(user_media) >= 10:
        return await message.answer("❗️ Maksimum 10 ta rasm yoki video yuborish mumkin!")

    media_type = "photo" if message.photo else "video"
    file_id = message.photo[-1].file_id if message.photo else message.video.file_id
    user_media.append({"type": media_type, "file_id": file_id})
    await state.update_data(media_list=user_media)

    if len(user_media) == 1:
        from bot.keyboards.reply.common_reply import done_media_kb
        await message.answer("📸 Qabul qilindi! Istasangiz yana yuborishingiz mumkin.\nTugatganingizdan so'ng pastdagi <b>✅ Rasmlar tayyor</b> tugmasini bosing.", reply_markup=done_media_kb())

@router.message(AutoAdState.photo, F.text == "✅ Rasmlar tayyor")
async def process_auto_media_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    media_list = data.get("media_list", [])

    if not media_list: return await message.answer("❗️ Hali hech qanday rasm yubormadingiz!")
    if data.get("is_submitting"): return await message.answer("⏳ E'lon saqlanmoqda, iltimos kuting...")
    await state.update_data(is_submitting=True)

    try:
        user, _ = await TelegramUser.objects.aget_or_create(
            user_id=message.from_user.id,
            defaults={"full_name": message.from_user.full_name, "username": message.from_user.username}
        )
        category, _ = await Category.objects.aget_or_create(callback_data="category_auto", defaults={"name": "Avto", "is_active": True})
        phones_str = ", ".join(data.get("phones", []))

        details_data = {
            "model": data.get("model"), "year": data.get("year"), "distance": data.get("distance"),
            "coat": data.get("coat"), "condition": data.get("condition"), "oil": data.get("oil"),
            "info": data.get("info"), "price": data.get("price"), "location": data.get("location"),
            "media_list": media_list,
        }

        ad = await Advertisement.objects.acreate(user=user, category=category, details=details_data, phone_numbers=phones_str, status=Advertisement.Status.DRAFT)
        formatted_text = format_auto_text(details_data, phones_str)

        await message.answer("⏳ E'loningiz tayyorlandi!", reply_markup=ReplyKeyboardRemove())
        sent_msg_ids = await send_ad_media(bot=message.bot, chat_id=message.chat.id, media_list=media_list, caption=formatted_text, reply_markup=get_user_confirm_kb(ad.id))

        ad.message_ids = sent_msg_ids
        await ad.asave()
    except Exception as e:
        logger.exception(f"Saqlashda xato yuz berdi: {e}")
        await message.answer("⚠️ Texnik xatolik yuz berdi. Iltimos qayta urinib ko'ring.")
    finally:
        await state.clear()