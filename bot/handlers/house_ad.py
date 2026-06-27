import logging
from contextlib import suppress
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from bot.states.ad_states import HouseAdState
from bot.keyboards.inline.house_inline import get_house_type_kb, get_house_action_kb
from bot.keyboards.inline.house_inline import get_house_confirm_kb
from bot.utils.media_sender import send_ad_media  # 🛑 USER_MEDIA_CACHE OLIB TASHLANDI
from bot.models import TelegramUser, Category, Advertisement
from bot.keyboards.reply.common_reply import cancel_kb, skip_cancel_kb, multi_phone_kb, done_media_kb
from bot.utils.validators import AutoAdValidator
from bot.utils.helpers import is_valid_text

logger = logging.getLogger(__name__)
router = Router()

# ==========================================
# 1-3. BOSH MENU VA MAQSAD TANLASH
# ==========================================
@router.callback_query(F.data == "category_house")
async def start_house_ad(call: CallbackQuery, state: FSMContext):
    with suppress(TelegramBadRequest): await call.answer()
    await state.clear()
    await call.message.edit_text("🏠 <b>Uy-joy bo'limiga xush kelibsiz!</b>\n\nQanday turdagi e'lon bermoqchisiz?", parse_mode="HTML", reply_markup=get_house_type_kb())

@router.callback_query(F.data.startswith("htype_"))
async def process_house_type(call: CallbackQuery, state: FSMContext):
    with suppress(TelegramBadRequest): await call.answer()
    property_type = call.data.split("_")[1]
    type_names = {"kvartira": "Kvartira", "hovli": "Hovli / Yer", "noturar": "Noturar joy"}
    display_names = {"kvartira": "🏢 Kvartira", "hovli": "🏡 Hovli / Yer", "noturar": "🏪 Noturar joy"}

    await state.update_data(property_type=type_names[property_type])
    await call.message.edit_text(f"Tanlandi: <b>{display_names[property_type]}</b>\n\n👇 Endi e'lon maqsadini tanlang:", parse_mode="HTML", reply_markup=get_house_action_kb())

@router.callback_query(F.data.startswith("haction_"))
async def process_house_action(call: CallbackQuery, state: FSMContext):
    with suppress(TelegramBadRequest): await call.answer()

    if call.data == "haction_back": return await start_house_ad(call, state)

    action = "Sotiladi" if call.data == "haction_sotiladi" else "Ijaraga"
    data = await state.get_data()
    prop_type = data.get("property_type", "")

    await state.update_data(action_type=action)
    await call.message.delete()

    if "Kvartira" in prop_type:
        await state.set_state(HouseAdState.rooms)
        await call.message.answer("🔢 <b>Necha xonadan iborat?</b>\n\n<i>(Masalan: 3 yoki 4 xona)</i>", parse_mode="HTML", reply_markup=cancel_kb())
    elif "Hovli" in prop_type:
        await state.set_state(HouseAdState.area)
        await call.message.answer("📏 <b>Yer maydoni qancha?</b>\n\n<i>(Masalan: 4 sotix yoki 400 kv.m)</i>", parse_mode="HTML", reply_markup=cancel_kb())
    elif "Noturar" in prop_type:
        await state.set_state(HouseAdState.building_name)
        await call.message.answer("🏪 <b>Obyekt nomini kiriting:</b>\n\n<i>(Masalan: Do'kon yokii ishlab chiqarish, noturar joy)</i>", parse_mode="HTML", reply_markup=cancel_kb())

# ==========================================
# 4. SHOXLANUVCHI QADAMLAR
# ==========================================
@router.message(HouseAdState.building_name)
async def h_building_name(message: Message, state: FSMContext):
    if not is_valid_text(message.text): return await message.answer("❗️ Iltimos, obyekt nomini to'g'ri kiriting.")
    await state.update_data(building_name=message.text)
    await state.set_state(HouseAdState.area)
    await message.answer("📏 <b>Yer maydoni qancha?</b>", parse_mode="HTML", reply_markup=cancel_kb())

@router.message(HouseAdState.area)
async def h_area(message: Message, state: FSMContext):
    if not is_valid_text(message.text): return await message.answer("❗️ Iltimos, maydonni to'g'ri kiriting.")
    await state.update_data(area=message.text)
    data = await state.get_data()
    prop_type = data.get("property_type", "")

    if "Hovli" in prop_type:
        await state.set_state(HouseAdState.rooms)
        await message.answer("🔢 <b>Necha xonadan iborat?</b>\n\n<i>(Faqat raqam kiriting)</i>", parse_mode="HTML", reply_markup=cancel_kb())
    elif "Noturar" in prop_type:
        await state.set_state(HouseAdState.docs)
        await message.answer("📄 <b>Hujjatlari qanday?</b>", parse_mode="HTML", reply_markup=cancel_kb())

@router.message(HouseAdState.rooms)
async def h_rooms(message: Message, state: FSMContext):
    if not message.text: return await message.answer("❗️ Iltimos, xonalar sonini faqat raqamda kiriting (masalan: 3)")
    await state.update_data(rooms=message.text)
    data = await state.get_data()
    prop_type = data.get("property_type", "")

    if "Kvartira" in prop_type:
        await state.set_state(HouseAdState.floor)
        await message.answer("🏢 <b>Nechanchi qavatda joylashgan?</b>", parse_mode="HTML", reply_markup=cancel_kb())
    elif "Hovli" in prop_type:
        await state.set_state(HouseAdState.conditions)
        await message.answer("🚰 <b>Sharoitlar qanday?</b>\n\n<i>(Masalan: Gaz, Suv, Svet bor)</i>", parse_mode="HTML", reply_markup=cancel_kb())

@router.message(HouseAdState.floor)
async def h_floor(message: Message, state: FSMContext):
    if not is_valid_text(message.text): return await message.answer("❗️ Iltimos, qavatni to'g'ri kiriting.")
    await state.update_data(floor=message.text)
    await state.set_state(HouseAdState.conditions)
    await message.answer("🚰 <b>Sharoitlar qanday?</b>\n\n<i>(Masalan: Gaz, Suv, Svet bor)</i>", parse_mode="HTML", reply_markup=cancel_kb())

@router.message(HouseAdState.docs)
async def h_docs(message: Message, state: FSMContext):
    if not is_valid_text(message.text): return await message.answer("❗️ Iltimos, hujjatlarni to'g'ri kiriting.")
    await state.update_data(docs=message.text)
    await state.set_state(HouseAdState.conditions)
    await message.answer("🚰 <b>Sharoitlar qanday?</b>\n\n<i>(Masalan: Gaz, Suv, Svet bor)</i>", parse_mode="HTML", reply_markup=cancel_kb())

# ==========================================
# 5. UMUMIY O'ZANGA TUSHISH
# ==========================================
@router.message(HouseAdState.conditions)
async def h_conditions(message: Message, state: FSMContext):
    if not is_valid_text(message.text): return await message.answer("❗️ Iltimos, sharoitlarni to'g'ri kiriting.")
    await state.update_data(conditions=message.text)
    data = await state.get_data()

    if "Noturar" in data.get("property_type", ""):
        await state.set_state(HouseAdState.info)
        await message.answer("✍️ <b>Qo'shimcha ma'lumotlar:</b>\n<i>(Ixtiyoriy. O'tkazib yuborishingiz mumkin)</i>", parse_mode="HTML", reply_markup=skip_cancel_kb())
    else:
        await state.set_state(HouseAdState.condition_state)
        await message.answer("🛠 <b>Remonti (Holati) qanday?</b>", parse_mode="HTML", reply_markup=cancel_kb())

@router.message(HouseAdState.condition_state)
async def h_condition_state(message: Message, state: FSMContext):
    if not is_valid_text(message.text): return await message.answer("❗️ Iltimos, holatini to'g'ri kiriting.")
    await state.update_data(condition_state=message.text)
    await state.set_state(HouseAdState.info)
    await message.answer("✍️ <b>Qo'shimcha ma'lumotlar:</b>\n<i>(Ixtiyoriy. O'tkazib yuborishingiz mumkin)</i>", parse_mode="HTML", reply_markup=skip_cancel_kb())

@router.message(HouseAdState.info)
async def h_info(message: Message, state: FSMContext):
    info_text = "" if message.text == "⏭ O'tkazib yuborish" else message.text
    if info_text and not is_valid_text(info_text): return await message.answer("❗️ Matnni to'g'ri kiriting yoki o'tkazib yuboring.")
    await state.update_data(info=info_text)
    await state.set_state(HouseAdState.price)
    await message.answer("💰 <b>Narxini kiriting:</b>\n<i>(Masalan: 35,000$ yoki Kelishamiz)</i>", parse_mode="HTML", reply_markup=cancel_kb())

# ==========================================
# 6. NARX -> TELEFON -> MANZIL
# ==========================================
@router.message(HouseAdState.price)
async def h_price(message: Message, state: FSMContext):
    is_valid, err = AutoAdValidator.validate_price(message.text)
    if not is_valid: return await message.answer(err)

    # 🛑 Yordamchi xotira maydonlari yaratildi
    await state.update_data(price=message.text, phone_list=[], media_list=[])
    await state.set_state(HouseAdState.phone)
    await message.answer("☎️ <b>Telefon raqamingizni kiriting:</b>\n\n<i>📱 Bitta raqam yuborish uchun pastdagi tugmani bosing.\n✍️ Yoki yana raqam qo'shib, keyin <b>➡️ Keyingi qadam</b> tugmasini bosing!</i>", parse_mode="HTML", reply_markup=multi_phone_kb())

@router.message(HouseAdState.phone)
async def h_phone(message: Message, state: FSMContext):
    if message.text == "➡️ Keyingi qadam (Manzilga o'tish)":
        data = await state.get_data()
        phones = data.get("phone_list", [])
        if not phones: return await message.answer("❗️ Iltimos, kamida bitta telefon raqam kiriting.")

        await state.update_data(phone=", ".join(phones))
        await state.set_state(HouseAdState.location)
        return await message.answer("📍 <b>Manzilni kiriting:</b>", parse_mode="HTML", reply_markup=cancel_kb())

    phone = message.contact.phone_number if message.contact else message.text

    is_valid, err = AutoAdValidator.validate_phone(phone)
    if not is_valid: return await message.answer(err)

    data = await state.get_data()
    phones = data.get("phone_list", [])
    if phone not in phones:
        phones.append(phone)
        await state.update_data(phone_list=phones)
        await message.answer(f"✅ Raqam qo'shildi: <b>{phone}</b>\nDavom etish uchun <b>Keyingi qadam</b> ni bosing.", parse_mode="HTML")
    else:
        await message.answer("❗️ Bu raqam allaqachon qo'shilgan!")

@router.message(HouseAdState.location)
async def h_location(message: Message, state: FSMContext):
    if not is_valid_text(message.text): return await message.answer("❗️ Iltimos, manzilni to'g'ri kiriting.")
    await state.update_data(location=message.text)
    await state.set_state(HouseAdState.photos)
    await message.answer("📸 <b>E'lon uchun rasm yoki videolarni yuboring.</b>\n\n<i>Barcha rasmlarni yuborib bo'lsangiz, pastdagi <b>✅ Rasmlar tayyor</b> tugmasini bosing.</i>", parse_mode="HTML", reply_markup=cancel_kb())

# ==========================================
# 7. RASMLARNI YIG'ISH (FSM XOTIRADAN)
# ==========================================
@router.message(HouseAdState.photos, F.photo | F.video)
async def accumulate_house_media(message: Message, state: FSMContext):
    data = await state.get_data()
    media_list = data.get("media_list", [])

    if len(media_list) >= 10:
        return await message.answer("❗️ Maksimum 10 ta rasm yoki video yuborish mumkin!")

    media_type = "photo" if message.photo else "video"
    file_id = message.photo[-1].file_id if message.photo else message.video.file_id

    media_list.append({"type": media_type, "file_id": file_id})
    await state.update_data(media_list=media_list)

    if len(media_list) == 1:
        await message.answer("📸 Qabul qilindi! Yana yuborishingiz mumkin.\nTugatganingizdan so'ng pastdagi <b>✅ Rasmlar tayyor</b> tugmasini bosing.", parse_mode="HTML", reply_markup=done_media_kb())

@router.message(HouseAdState.photos, F.text == "✅ Rasmlar tayyor")
async def finish_house_media(message: Message, state: FSMContext):
    data = await state.get_data()
    media_list = data.get("media_list", [])

    if not media_list: return await message.answer("❗️ Iltimos, kamida bitta rasm yoki video yuboring.")
    if data.get("is_submitting"): return await message.answer("⏳ E'lon saqlanmoqda, iltimos kuting...")
    await state.update_data(is_submitting=True)

    await message.answer("⏳ E'loningiz tayyorlanmoqda...", reply_markup=ReplyKeyboardRemove())

    from bot.utils.formatters import format_house_text
    details_data = {
        "property_type": data.get("property_type"), "action_type": data.get("action_type"),
        "rooms": data.get("rooms"), "floor": data.get("floor"), "area": data.get("area"),
        "building_name": data.get("building_name"), "docs": data.get("docs"),
        "conditions": data.get("conditions"), "condition_state": data.get("condition_state"),
        "info": data.get("info"), "price": data.get("price"), "location": data.get("location"),
        "media_list": media_list
    }
    phone_str = data.get('phone', '')
    full_text = format_house_text(details_data, phone_str) + "\n\n👉 <b>@XonobodBugun</b>"
    details_data["custom_admin_text"] = full_text

    try:
        user, _ = await TelegramUser.objects.aget_or_create(
            user_id=message.from_user.id,
            defaults={"full_name": message.from_user.full_name, "username": message.from_user.username}
        )
        category, _ = await Category.objects.aget_or_create(callback_data="category_house", defaults={"name": "Uy-joy", "is_active": True})
        ad = await Advertisement.objects.acreate(user=user, category=category, details=details_data, phone_numbers=phone_str, status=Advertisement.Status.DRAFT)

        await send_ad_media(bot=message.bot, chat_id=message.chat.id, media_list=media_list, caption=full_text, reply_markup=get_house_confirm_kb(ad.id))
    except Exception as e:
        logger.exception(f"Uy-joy e'lon saqlashda xato: {e}")
        await message.answer("⚠️ Texnik xatolik yuz berdi.")
    finally:
        await state.clear()