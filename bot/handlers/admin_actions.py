import logging
from contextlib import suppress
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from bot.keyboards.inline.auto_inline import get_reject_reasons_kb, get_admin_action_kb, REJECT_REASONS
from bot.keyboards.inline.business_inline import get_business_admin_kb
from bot.keyboards.inline.house_inline import get_house_admin_kb
from bot.keyboards.inline.phone_inline import get_phone_admin_kb
from bot.keyboards.inline.other_inline import get_other_admin_kb
from bot.keyboards.inline.lost_found_inline import get_lf_admin_kb

from bot.models import Advertisement
from bot.states.ad_states import PaymentState, AdminEditState, AdminRejectState
from bot.keyboards.reply.common_reply import cancel_kb
from bot.keyboards.reply.main_menu import main_menu_kb
from bot.utils.formatters import format_auto_text, format_house_text, format_phone_text, format_other_text, \
    get_admin_footer, format_lost_found_text
from bot.utils.media_sender import send_ad_media
from bot.utils.helpers import get_ad_type
from core.config import ADMIN_GROUP_ID

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data.startswith("admin_payment_"))
async def admin_ask_payment(call: CallbackQuery, bot: Bot, state: FSMContext):
    with suppress(TelegramBadRequest):
        await call.answer()
    ad_id = int(call.data.split("_")[-1])
    try:
        ad = await Advertisement.objects.select_related("user").aget(id=ad_id)
        if ad.status != "pending":
            await call.message.edit_reply_markup(reply_markup=None)
            return await call.answer("⚠️ Kech qoldingiz, bu e'lonni boshqa admin hal qildi!", show_alert=True)

        # 🛑 HIMOYA: Agar e'lon Bepul bo'lsa to'lov so'ramaydi
        if ad.details.get("tariff") == "Bepul":
            return await call.answer("❗️ Bepul e'lon uchun to'lov so'ralmaydi!", show_alert=True)

        user_id = ad.user.user_id
        await call.message.edit_reply_markup(reply_markup=None)
        await call.message.reply("⏳ Mijozga to'lov so'rovi yuborilmoqda...")

        user_state = FSMContext(storage=state.storage, key=StorageKey(bot_id=bot.id, chat_id=user_id, user_id=user_id))
        await user_state.set_state(PaymentState.waiting_for_receipt)
        await user_state.update_data(payment_ad_id=ad_id)

        text = (
            "🎉 <b>E'loningiz adminlar tomonidan ma'qullandi!</b>\n\n"
            f"Kanalga chiqarish uchun quyidagi kartaga to'lov qiling:\n"
            f"💳 <b>9860010514986529</b> (Zokirov Boburjon nomida)\n"
            f"💰 To'lov summasi: <b>{ad.details.get('tariff', 'Kelishilgan')}</b>\n\n"
            "To'lov qilganingizdan so'ng, <b>chek rasmini (skrinshot)</b> shu yerga yuboring!"
        )

        # 🛑 SHARPA XATONI USHLOVCHI QOPQON
        try:
            await bot.send_message(chat_id=user_id, text=text, parse_mode="HTML", reply_markup=cancel_kb())
            await call.message.answer("✅ <b>Mijozga to'lov so'rovi muvaffaqiyatli yuborildi!</b>", parse_mode="HTML")
        except Exception as send_err:
            logger.error(f"Xabar yuborishda xato: {send_err}")
            await call.message.answer(f"❗️ <b>Mijozga xabar yuborib bo'lmadi!</b>\n\n<b>Xato sababi:</b> {send_err}",
                                      parse_mode="HTML")

    except Exception as e:
        logger.exception(f"To'lov so'rashda xato: {e}")
        await call.message.answer("⚠️ Tizimda xatolik yuz berdi.")


@router.callback_query(F.data.startswith("admin_reject_"))
async def admin_show_reject_reasons(call: CallbackQuery):
    with suppress(TelegramBadRequest): await call.answer()
    ad_id = int(call.data.split("_")[-1])
    ad = await Advertisement.objects.aget(id=ad_id)
    if ad.status != "pending":
        await call.message.edit_reply_markup(reply_markup=None)
        return await call.answer("⚠️ Bu e'lonni boshqa admin hal qildi!", show_alert=True)
    await call.message.edit_reply_markup(reply_markup=get_reject_reasons_kb(ad_id))


@router.callback_query(F.data.startswith("reject_back_"))
async def admin_reject_back(call: CallbackQuery):
    with suppress(TelegramBadRequest):
        await call.answer()
    ad_id = int(call.data.split("_")[-1])
    ad = await Advertisement.objects.aget(id=ad_id)

    ad_type = get_ad_type(ad)
    if ad_type == "Biznes":
        kb_func = get_business_admin_kb
    elif ad_type == "Uy-joy":
        kb_func = get_house_admin_kb
    elif ad_type == "Telefon":
        kb_func = get_phone_admin_kb
    elif ad_type == "Boshqa":
        kb_func = get_other_admin_kb
    elif ad_type == "Yo'qolgan/Topilgan":
        kb_func = get_lf_admin_kb
    else:
        kb_func = get_admin_action_kb

    await call.message.edit_reply_markup(reply_markup=kb_func(ad_id))


@router.callback_query(F.data.startswith("reject_reason_"))
async def admin_process_reject(call: CallbackQuery, bot: Bot):
    with suppress(TelegramBadRequest):
        await call.answer("Rad etildi!", show_alert=False)
    parts = call.data.split("_")
    ad_id, reason_idx = int(parts[2]), int(parts[3])
    selected_reason = REJECT_REASONS[reason_idx]

    try:
        ad = await Advertisement.objects.select_related("user").aget(id=ad_id)
        if ad.status != "pending": return await call.message.edit_reply_markup(reply_markup=None)

        ad.status = "rejected"
        await ad.asave()
        await call.message.edit_reply_markup(reply_markup=None)
        await call.message.reply(f"❌ E'lon rad etildi.\nSabab: <b>{selected_reason}</b>", parse_mode="HTML")

        with suppress(TelegramForbiddenError, TelegramBadRequest):
            reject_text = f"❌ <b>E'loningiz adminlar tomonidan rad etildi!</b>\n\n<b>Sabab:</b> {selected_reason}\n\nIltimos, xatoliklarni to'g'rilab, e'lonni qaytadan yuboring."
            await bot.send_message(chat_id=ad.user.user_id, text=reject_text, parse_mode="HTML",
                                   reply_markup=main_menu_kb)
    except Exception as e:
        logger.exception(f"Rad etishda xato: {e}")


@router.callback_query(F.data.startswith("reject_custom_"))
async def admin_reject_custom(call: CallbackQuery, state: FSMContext):
    with suppress(TelegramBadRequest): await call.answer()
    ad_id = int(call.data.split("_")[-1])
    await state.set_state(AdminRejectState.waiting_for_reason)
    await state.update_data(reject_ad_id=ad_id)
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.reply(
        "✍️ <b>Mijozga yuboriladigan rad etish sababini yozing:</b>\n\n<i>(Bekor qilish uchun pastdagi tugmani bosing)</i>",
        parse_mode="HTML", reply_markup=cancel_kb())


@router.message(AdminRejectState.waiting_for_reason)
async def process_custom_reject_reason(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    ad_id = data.get("reject_ad_id")
    custom_reason = message.html_text or message.text

    if not custom_reason or len(custom_reason) < 3: return await message.answer("❗️ Iltimos, sababni to'liqroq yozing.")

    try:
        ad = await Advertisement.objects.select_related("user").aget(id=ad_id)
        if ad.status != "pending":
            await state.clear()
            return await message.answer("⚠️ Bu e'lonni boshqa admin hal qildi yoki holati o'zgargan!")

        ad.status = "rejected"
        await ad.asave()
        await state.clear()

        await message.reply(f"✅ E'lon muvaffaqiyatli rad etildi.\nSabab: <b>{custom_reason}</b>", parse_mode="HTML",
                            reply_markup=main_menu_kb)

        with suppress(TelegramForbiddenError, TelegramBadRequest):
            reject_text = f"❌ <b>E'loningiz adminlar tomonidan rad etildi!</b>\n\n<b>Sabab:</b> {custom_reason}\n\nIltimos, xatoliklarni to'g'rilab, e'lonni qaytadan yuboring."
            await bot.send_message(chat_id=ad.user.user_id, text=reject_text, parse_mode="HTML",
                                   reply_markup=main_menu_kb)
    except Exception as e:
        logger.exception(f"Qo'lda rad etishda xato: {e}")
        await message.answer("⚠️ Texnik xatolik yuz berdi.")


@router.message(PaymentState.waiting_for_receipt, F.photo | F.document)
async def receive_payment_receipt(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    ad_id = data.get("payment_ad_id")
    if not ad_id:
        await state.clear()
        return await message.answer("❗️ E'lon ma'lumotlari topilmadi, iltimos boshqadan urinib ko'ring.")

    file_id = message.photo[-1].file_id if message.photo else message.document.file_id
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Kanalga joylash", callback_data=f"receipt_approve_{ad_id}")
    builder.button(text="❌ Chek xato", callback_data=f"receipt_reject_{ad_id}")
    builder.adjust(1)
    admin_text = f"🧾 <b>YANGI TO'LOV CHEKI!</b>\n\n📌 E'lon ID: #{ad_id}\n👤 Mijoz: {message.from_user.full_name}"

    if message.photo:
        await bot.send_photo(chat_id=ADMIN_GROUP_ID, photo=file_id, caption=admin_text, parse_mode="HTML",
                             reply_markup=builder.as_markup())
    else:
        await bot.send_document(chat_id=ADMIN_GROUP_ID, document=file_id, caption=admin_text, parse_mode="HTML",
                                reply_markup=builder.as_markup())

    await state.clear()
    await message.answer("✅ <b>Chek qabul qilindi!</b>\n\nAdminlarimiz uni tekshirib kanalga joylashadi. Rahmat!",
                         parse_mode="HTML", reply_markup=main_menu_kb)


@router.callback_query(F.data.startswith("receipt_approve_"))
async def admin_approve_receipt(call: CallbackQuery, bot: Bot):
    with suppress(TelegramBadRequest):
        await call.answer("Kanalga joylanmoqda...", show_alert=False)
    ad_id = int(call.data.split("_")[-1])
    try:
        ad = await Advertisement.objects.select_related("user", "category").aget(id=ad_id)
        if ad.status == "approved":
            await call.message.edit_reply_markup(reply_markup=None)
            return await call.answer("❗️ Bu e'lon allaqachon kanalga joylangan!", show_alert=True)

        from core.config import CHANNEL_ID
        ad_type = get_ad_type(ad)

        if ad_type == "Biznes":
            formatted_text = ad.details.get("business_text", "")
        elif ad_type == "Uy-joy":
            formatted_text = format_house_text(ad.details, ad.phone_numbers) + "\n\n👉 <b>@XonobodBugun</b>"
        elif ad_type == "Telefon":
            formatted_text = format_phone_text(ad.details, ad.phone_numbers)
        elif ad_type == "Boshqa":
            formatted_text = ad.details.get("custom_admin_text", "")
            if not formatted_text: formatted_text = format_other_text(ad.details, ad.phone_numbers)
        else:
            formatted_text = format_auto_text(ad.details, ad.phone_numbers)

        media_list = ad.details.get("media_list", [])
        if media_list:
            sent_ids = await send_ad_media(bot=bot, chat_id=CHANNEL_ID, media_list=media_list, caption=formatted_text)
        else:
            msg = await bot.send_message(chat_id=CHANNEL_ID, text=formatted_text, parse_mode="HTML")
            sent_ids = [msg.message_id]

        ad.status = "approved"
        ad.message_ids = sent_ids
        await ad.asave()
        await call.message.edit_reply_markup(reply_markup=None)
        await call.message.reply(f"✅ #{ad.id} e'lon muvaffaqiyatli kanalga joylandi!")

        with suppress(TelegramForbiddenError, TelegramBadRequest):
            if ad_type == "Biznes":
                user_success_text = "🎉 <b>Tabriklaymiz!</b> E'loningiz @XonobodBugun kanaliga muvaffaqiyatli joylandi."
            else:
                user_success_text = "🎉 <b>Tabriklaymiz!</b> E'loningiz @XonobodBugun kanaliga muvaffaqiyatli joylandi.\n\n💡 <b>Muhim eslatma:</b> Agar e'loningiz o'z egasini topsa, botning Asosiy menyusidan <b>🗂 Mening e'lonlarim</b> bo'limiga kiring va <b>🤝 Sotildi</b> tugmasini bosing.\n\n👍 Shunda sizni hadeb bezovta qilishmaydi, telefon raqamingiz olib tashlanadi! "
            await bot.send_message(chat_id=ad.user.user_id, text=user_success_text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Chekni tasdiqlashda xato: {e}")


@router.callback_query(F.data.startswith("lf_admin_approve_"))
async def admin_approve_lf(call: CallbackQuery, bot: Bot):
    with suppress(TelegramBadRequest):
        await call.answer("Kanalga joylanmoqda...", show_alert=False)
    ad_id = int(call.data.split("_")[-1])
    try:
        ad = await Advertisement.objects.select_related("user", "category").aget(id=ad_id)
        if ad.status == "approved":
            await call.message.edit_reply_markup(reply_markup=None)
            return await call.answer("❗️ Bu e'lon allaqachon kanalga joylangan!", show_alert=True)

        from core.config import CHANNEL_ID
        formatted_text = format_lost_found_text(ad.details, ad.phone_numbers)
        media_list = ad.details.get("media_list", [])

        if media_list:
            sent_ids = await send_ad_media(bot=bot, chat_id=CHANNEL_ID, media_list=media_list, caption=formatted_text)
        else:
            msg = await bot.send_message(chat_id=CHANNEL_ID, text=formatted_text, parse_mode="HTML")
            sent_ids = [msg.message_id]

        ad.status = "approved"
        ad.message_ids = sent_ids
        await ad.asave()
        await call.message.edit_reply_markup(reply_markup=None)
        await call.message.reply(f"✅ #{ad.id} Yo'qolgan/Topilgan e'lon kanalga joylandi!")

        with suppress(TelegramForbiddenError, TelegramBadRequest):
            await bot.send_message(chat_id=ad.user.user_id,
                                   text="🎉 <b>Tabriklaymiz!</b> E'loningiz @XonobodBugun kanaliga muvaffaqiyatli joylandi.",
                                   parse_mode="HTML")
    except Exception as e:
        logger.error(f"LF tasdiqlashda xato: {e}")


@router.callback_query(F.data.startswith("receipt_reject_"))
async def admin_reject_receipt(call: CallbackQuery, bot: Bot, state: FSMContext):
    with suppress(TelegramBadRequest):
        await call.answer()
    ad_id = int(call.data.split("_")[-1])
    try:
        ad = await Advertisement.objects.select_related("user").aget(id=ad_id)
        if ad.status == "approved":
            await call.message.edit_reply_markup(reply_markup=None)
            return await call.answer("❗️ E'lon allaqachon kanalga joylangan!", show_alert=True)

        await call.message.edit_reply_markup(reply_markup=None)
        await call.message.reply("❌ Chek rad etildi. Mijozga qayta so'rov yuborildi.")

        user_state = FSMContext(storage=state.storage,
                                key=StorageKey(bot_id=bot.id, chat_id=ad.user.user_id, user_id=ad.user.user_id))
        await user_state.set_state(PaymentState.waiting_for_receipt)
        await user_state.update_data(payment_ad_id=ad_id)

        with suppress(TelegramForbiddenError, TelegramBadRequest):
            await bot.send_message(chat_id=ad.user.user_id,
                                   text="❗️ <b>To'lov chekida xatolik mavjud!</b>\nIltimos, to'g'ri chek rasmini qayta yuboring.",
                                   parse_mode="HTML")
    except Exception as e:
        logger.error(f"Chekni rad etishda xato: {e}")


# ==========================================
# 🛑 HAKIQIY MANTIQIY TAHRIRLASH (QOLIP BUZILMAYDI) 🛑
# ==========================================
@router.callback_query(F.data.startswith("admin_edit_tg_"))
async def admin_show_edit_unified(call: CallbackQuery, state: FSMContext):
    ad_id = int(call.data.split("_")[-1])
    try:
        from bot.models import Advertisement
        from bot.utils.helpers import get_ad_type
        ad = await Advertisement.objects.aget(id=ad_id)
        ad_type = get_ad_type(ad)

        if ad_type == "Avto":
            from bot.keyboards.inline.auto_inline import get_auto_edit_kb
            await call.message.edit_reply_markup(reply_markup=get_auto_edit_kb(ad_id))
        elif ad_type == "Uy-joy":
            from bot.keyboards.inline.house_inline import get_house_edit_kb
            await call.message.edit_reply_markup(
                reply_markup=get_house_edit_kb(ad_id, ad.details.get("property_type", "")))
        elif ad_type == "Telefon":
            from bot.keyboards.inline.phone_inline import get_phone_edit_kb
            await call.message.edit_reply_markup(reply_markup=get_phone_edit_kb(ad_id))
        elif ad_type == "Yo'qolgan/Topilgan":
            from bot.keyboards.inline.lost_found_inline import get_lf_edit_kb
            await call.message.edit_reply_markup(reply_markup=get_lf_edit_kb(ad_id))
        elif ad_type == "Boshqa" and not ad.details.get("is_ready_post", False):
            # 🛑 TO'G'RILANDI: Qadamma-qadam terilgan "Boshqa" e'lonlar uchun o'zining maxsus menyusi (Nomi, Narxi va hk) ochiladi
            from bot.keyboards.inline.other_inline import get_other_edit_kb
            await call.message.edit_reply_markup(reply_markup=get_other_edit_kb(ad_id))
        else:
            # FAQAT Biznes va Tayyor (Rasmi va matni bitta qilib jo'natilgan) e'lonlar uchungina yaxlit matn so'raladi
            from bot.states.ad_states import AdminEditState
            from bot.keyboards.reply.common_reply import cancel_kb
            await state.set_state(AdminEditState.waiting_for_new_post)
            await state.update_data(edit_ad_id=ad_id)
            await call.message.delete()
            await call.message.answer(
                "✍️ <b>Ushbu e'lon uchun yangi matn va rasm/video yuboring:</b>\n\n<i>(Bekor qilish uchun pastdagi tugmani bosing)</i>",
                parse_mode="HTML", reply_markup=cancel_kb()
            )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(e)
        await call.answer("⚠️ Xatolik", show_alert=False)


# FAQAT BIZNES VA BOSHQA E'LONLAR UCHUN ISHLAYDI
@router.message(AdminEditState.waiting_for_new_post)
async def admin_save_edit(message: Message, state: FSMContext):
    data = await state.get_data()
    ad_id = data.get("edit_ad_id")

    ad = await Advertisement.objects.select_related("user").aget(id=ad_id)
    details = ad.details.copy()
    ad_type = get_ad_type(ad)

    new_text = (message.html_text or "")
    if "👉 <b>@XonobodBugun</b>" not in new_text:
        new_text += "\n\n👉 <b>@XonobodBugun</b>"

    if ad_type == "Biznes":
        details["business_text"] = new_text
    else:
        details["custom_admin_text"] = new_text

    if message.photo:
        details["media_list"] = [{"type": "photo", "file_id": message.photo[-1].file_id}]
    elif message.video:
        details["media_list"] = [{"type": "video", "file_id": message.video.file_id}]

    ad.details = details
    await ad.asave()
    await state.clear()
    await message.reply("✅ <b>Muvaffaqiyatli tahrirlandi!</b>\nQuyida uning yangi holati (Prevyu):", parse_mode="HTML",
                        reply_markup=main_menu_kb)

    if ad_type == "Biznes":
        admin_text = ad.details.get("business_text", "")
        kb_func = get_business_admin_kb
    else:
        admin_text = ad.details.get("custom_admin_text", "")
        kb_func = get_other_admin_kb

    admin_text += get_admin_footer(ad.user, ad.details.get("tariff", "Kelishilgan"))
    current_media = ad.details.get("media_list", [])

    if current_media:
        await send_ad_media(bot=message.bot, chat_id=message.chat.id, media_list=current_media, caption=admin_text,
                            reply_markup=kb_func(ad_id))
    else:
        await message.answer(text=admin_text, parse_mode="HTML", reply_markup=kb_func(ad_id))