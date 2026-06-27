import logging
from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from bot.keyboards.inline.lost_found_inline import get_lf_type_kb, get_lf_confirm_kb, get_lf_edit_kb
from bot.keyboards.reply.common_reply import cancel_kb, skip_cancel_kb, multi_phone_kb, done_media_kb
from bot.models import TelegramUser, Category, Advertisement
from bot.states.ad_states import LostFoundState
from bot.utils.formatters import format_lost_found_text
from bot.utils.media_sender import send_ad_media
from bot.utils.validators import AutoAdValidator
from bot.utils.helpers import is_valid_text
from contextlib import suppress

logger = logging.getLogger(__name__)
router = Router()

DEFAULT_LOST_PHOTO = "AgACAgIAAxkBAAEq8e5qNbH0GrkUMoe4_seoH49DlwF2FQACUrQxG3wiCUiz7b_NaAgRAgEAAwIAA3MAAzwE"


@router.message(F.text == "🤝 Yóqolgan / Topilgan (Bepul)")
async def start_lf(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Siz nimanidir yo'qotdingizmi yoki topib oldingizmi?", reply_markup=get_lf_type_kb())


@router.callback_query(F.data.startswith("lf_type_"))
async def process_lf_type(call: CallbackQuery, state: FSMContext):
    lf_type = call.data.split("_")[2]
    await state.update_data(lf_type=lf_type)
    await call.message.delete()
    await call.message.answer(
        "📦 <b>Nima buyum? (Qisqa va aniq yozing)</b>\n<i>(Masalan: Pasport, Qora hamyon, Damas kaliti)</i>",
        parse_mode="HTML", reply_markup=cancel_kb())
    await state.set_state(LostFoundState.item)


@router.message(LostFoundState.item)
async def lf_item(message: Message, state: FSMContext):
    if not is_valid_text(message.text): return await message.answer("❗️ Iltimos, buyum nomini to'g'ri kiriting.")
    await state.update_data(item=message.text)
    await message.answer("📍 <b>Qayerda? (Qaysi hududda)</b>\n<i>(Masalan: Xonobod markazida, Bozor atrofida)</i>",
                         parse_mode="HTML", reply_markup=cancel_kb())
    await state.set_state(LostFoundState.location)


@router.message(LostFoundState.location)
async def lf_location(message: Message, state: FSMContext):
    if not is_valid_text(message.text): return await message.answer("❗️ Iltimos, manzilni to'g'ri kiriting.")
    await state.update_data(location=message.text)
    await message.answer("📝 <b>Qo'shimcha ma'lumot bormi?</b>\n<i>(Ixtiyoriy. O'tkazib yuborishingiz mumkin)</i>",
                         parse_mode="HTML", reply_markup=skip_cancel_kb())
    await state.set_state(LostFoundState.info)


@router.message(LostFoundState.info)
async def lf_info(message: Message, state: FSMContext):
    text = message.text
    info = "" if text == "⏭ O'tkazib yuborish" else text
    if info and not is_valid_text(info): return await message.answer(
        "❗️ Iltimos, to'g'ri kiriting yoki o'tkazib yuboring.")
    await state.update_data(info=info, phones=[], media_list=[])
    await message.answer("☎️ <b>Telefon raqamingizni kiriting:</b>\n\n<i>📱 Bitta raqam yuborish uchun pastdagi tugmani bosing.\n✍️ Yana raqam qo'shmoqchi bo'lsangiz, yozib yuborishingiz mumkin.</i>",
                         parse_mode="HTML", reply_markup=multi_phone_kb())
    await state.set_state(LostFoundState.phone)


@router.message(LostFoundState.phone)
async def lf_phone(message: Message, state: FSMContext):
    data = await state.get_data()
    phones = data.get("phones", [])

    if message.text in ["➡️ Keyingi qadam", "➡️ Keyingi qadam (Manzilga o'tish)"]:
        if not phones: return await message.answer("❗️ Iltimos, kamida bitta raqam kiriting!")
        if data.get("lf_type") == "lost":
            await message.answer(
                "📸 <b>Yo'qolgan buyumning rasmi bormi?</b>\n<i>Agar bo'lmasa, 'O'tkazib yuborish' tugmasini bosing.</i>",
                parse_mode="HTML", reply_markup=skip_cancel_kb())
        else:
            await message.answer("📸 <b>Topilgan buyumning rasmini yuboring!</b>\n<i>(Majburiy)</i>", parse_mode="HTML",
                                 reply_markup=cancel_kb())
        await state.set_state(LostFoundState.photo)
        return

    phone_text = message.contact.phone_number if message.contact else message.text
    raw_phones = [p.strip() for p in phone_text.split(",") if p.strip()]

    added = 0
    for p in raw_phones:
        is_valid, err = AutoAdValidator.validate_phone(p)
        if not is_valid:
            await message.answer(f"❗️ Xato raqam: <b>{p}</b>\n{err}", parse_mode="HTML")
            continue

        if p not in phones:
            phones.append(p)
            added += 1
        else:
            # 🛑 XATO TO'G'RILANDI: Agar takrorlansa bot endi jim turmaydi
            await message.answer(f"❗️ <b>{p}</b> - bu raqam allaqachon qo'shilgan!", parse_mode="HTML")

    if added > 0:
        await state.update_data(phones=phones)
        await message.answer(
            f"✅ Raqam qo'shildi! Jami raqamlar: {len(phones)} ta.\nDavom etish uchun <b>Keyingi qadam</b> ni bosing.",
            parse_mode="HTML")


# 🛑 QOTIB QOLISH (is not handled) XATOSI TO'G'RILANDI
@router.message(LostFoundState.photo)
async def lf_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    lf_type = data.get("lf_type")

    if message.text == "⏭ O'tkazib yuborish":
        if lf_type == "found":
            return await message.answer("❗️ Topilgan buyumning rasmi bo'lishi shart!")
        else:
            await state.update_data(media_list=[])
            return await finish_lf_ad(message, state)

    elif message.text == "✅ Rasmlar tayyor":
        media_list = data.get("media_list", [])
        if not media_list:
            return await message.answer("❗️ Kamida bitta rasm yuboring yoki o'tkazib yuboring.")
        return await finish_lf_ad(message, state)

    elif message.photo or message.video:
        media_list = data.get("media_list", [])
        if len(media_list) >= 5: return await message.answer("❗️ Maksimum 5 ta rasm.")
        media_type = "photo" if message.photo else "video"
        file_id = message.photo[-1].file_id if message.photo else message.video.file_id
        media_list.append({"type": media_type, "file_id": file_id})
        await state.update_data(media_list=media_list)

        if len(media_list) == 1:
            await message.answer("📸 Qabul qilindi! Yana yuborishingiz mumkin yoki <b>✅ Rasmlar tayyor</b> ni bosing.",
                                 reply_markup=done_media_kb(), parse_mode="HTML")
        return

    else:
        # Fallback (Boshqa narsa tashlasa bot qotmasligi uchun)
        await message.answer("❗️ Iltimos, faqat rasm yoki video yuboring, yoki pastdagi tugmalardan birini bosing.")


async def finish_lf_ad(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("is_submitting"): return
    await state.update_data(is_submitting=True)
    await message.answer("⏳ E'loningiz tayyorlanmoqda...", reply_markup=ReplyKeyboardRemove())

    media_list = data.get("media_list", [])

    # Rasm yuborilmagan bo'lsa
    if not media_list and data.get("lf_type") == "lost":
        media_list = [{"type": "photo", "file_id": DEFAULT_LOST_PHOTO}]

    phones_str = ", ".join(data.get("phones", []))

    details_data = {
        "lf_type": data.get("lf_type"),
        "item": data.get("item"),
        "location": data.get("location"),
        "info": data.get("info"),
        "media_list": media_list
    }

    full_text = format_lost_found_text(details_data, phones_str)
    details_data["custom_admin_text"] = full_text

    try:
        user, _ = await TelegramUser.objects.aget_or_create(
            user_id=message.from_user.id,
            defaults={"full_name": message.from_user.full_name, "username": message.from_user.username}
        )
        category, _ = await Category.objects.aget_or_create(callback_data="category_lf",
                                                            defaults={"name": "Yo'qolgan/Topilgan", "is_active": True})
        ad = await Advertisement.objects.acreate(user=user, category=category, details=details_data,
                                                 phone_numbers=phones_str, status=Advertisement.Status.DRAFT)

        if media_list:
            await send_ad_media(bot=message.bot, chat_id=message.chat.id, media_list=media_list, caption=full_text,
                                reply_markup=get_lf_confirm_kb(ad.id))
        else:
            await message.answer(text=full_text, parse_mode="HTML", reply_markup=get_lf_confirm_kb(ad.id))
    except Exception as e:
        logger.exception(e)
        await message.answer("⚠️ Xatolik yuz berdi.")
    finally:
        await state.clear()


@router.callback_query(F.data.startswith("lf_edit_"))
async def show_lf_edit_menu(call: CallbackQuery):
    with suppress(TelegramBadRequest):
        await call.answer()
    ad_id = int(call.data.split("_")[-1])
    if call.message.text:
        await call.message.edit_text("Qaysi ma'lumotni o'zgartirmoqchisiz?", parse_mode="HTML",
                                     reply_markup=get_lf_edit_kb(ad_id))
    else:
        await call.message.edit_reply_markup(reply_markup=get_lf_edit_kb(ad_id))


@router.callback_query(F.data.startswith("lf_tback_"))
async def lf_back_to_confirm(call: CallbackQuery):
    ad_id = int(call.data.split("_")[-1])
    if call.message.text:
        await call.message.edit_text("Harakatni tanlang:", parse_mode="HTML", reply_markup=get_lf_confirm_kb(ad_id))
    else:
        await call.message.edit_reply_markup(reply_markup=get_lf_confirm_kb(ad_id))