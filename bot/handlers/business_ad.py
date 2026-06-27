import logging
from contextlib import suppress
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from bot.keyboards.reply.common_reply import cancel_kb
from bot.models import TelegramUser, Category, Advertisement
from bot.states.ad_states import BusinessAdState
from bot.keyboards.inline.business_inline import get_business_confirm_kb, get_business_tariff_kb, get_business_admin_kb
from bot.utils.media_sender import send_ad_media
from bot.keyboards.reply.main_menu import main_menu_kb

logger = logging.getLogger(__name__)
router = Router()

# ==========================================
# 1. TAYYOR BIZNES POSTNI QABUL QILISH
# ==========================================
@router.message(BusinessAdState.waiting_for_post)
async def receive_business_post(message: Message, state: FSMContext):
    if message.text and message.text.startswith(("📢", "📁", "🗂", "📞", "ℹ️", "💼", "🤝", "/", "⬅️")):
        await state.clear()
        return await message.answer(
            "❌ <b>Biznes e'lon berish bekor qilindi.</b>\nIltimos, kerakli bo'limni qayta bosing.", parse_mode="HTML")

    html_text = message.html_text or ""
    clean_text = message.text or ""

    if not message.photo and not message.video:
        if len(clean_text.strip()) < 15:
            return await message.answer(
                "❗️ <b>Iltimos, e'lon matnini batafsilroq yozing</b> (kamida 15 ta belgi) yoki rasm/video bilan yuboring.",
                parse_mode="HTML"
            )

    media_list = []
    if message.photo:
        media_list.append({"type": "photo", "file_id": message.photo[-1].file_id})
    elif message.video:
        media_list.append({"type": "video", "file_id": message.video.file_id})

    html_text += "\n\n👉 <b>@XonobodBugun</b>"

    try:
        user, _ = await TelegramUser.objects.aget_or_create(
            user_id=message.from_user.id,
            defaults={"full_name": message.from_user.full_name, "username": message.from_user.username}
        )
        category, _ = await Category.objects.aget_or_create(
            callback_data="ad_type_business",
            defaults={"name": "Biznes", "is_active": True}
        )

        details_data = {
            "business_text": html_text,
            "media_list": media_list,
        }

        ad = await Advertisement.objects.acreate(
            user=user, category=category, details=details_data,
            phone_numbers="Biznes e'lon", status=Advertisement.Status.DRAFT,
        )

        # 🛑 XATO TO'G'RILANDI: Asosiy menyu chaqirildi!
        await message.answer("⏳ E'loningiz qabul qilindi! Quyida ko'rib chiqing:", reply_markup=main_menu_kb)

        if media_list:
            sent_ids = await send_ad_media(
                bot=message.bot, chat_id=message.chat.id,
                media_list=media_list, caption=html_text,
                reply_markup=get_business_confirm_kb(ad.id)
            )
        else:
            msg = await message.answer(html_text, parse_mode="HTML", reply_markup=get_business_confirm_kb(ad.id))
            sent_ids = [msg.message_id]

        ad.message_ids = sent_ids
        await ad.asave()
        await state.clear()

    except Exception as e:
        logger.exception(f"Biznes elon saqlashda xato: {e}")
        await message.answer("⚠️ Xatolik yuz berdi.")

# ==========================================
# 2. TASDIQLASH VA TARIF TANLASH
# ==========================================
@router.callback_query(F.data.startswith("b_confirm_"))
async def confirm_business_ad(call: CallbackQuery):
    ad_id = int(call.data.split("_")[-1])
    if call.message.text:
        await call.message.edit_text("<b>E'lon uchun tarifni tanlang:</b>", parse_mode="HTML", reply_markup=get_business_tariff_kb(ad_id))
    else:
        await call.message.edit_reply_markup(reply_markup=get_business_tariff_kb(ad_id))
        await call.answer("Tarifni tanlang!", show_alert=False)

@router.callback_query(F.data.startswith("b_tback_"))
async def b_back_to_confirm(call: CallbackQuery):
    ad_id = int(call.data.split("_")[-1])
    if call.message.text:
        await call.message.edit_text("<b>Harakatni tanlang:</b>", parse_mode="HTML", reply_markup=get_business_confirm_kb(ad_id))
    else:
        await call.message.edit_reply_markup(reply_markup=get_business_confirm_kb(ad_id))
        await call.answer("Harakatni tanlang", show_alert=False)

# ==========================================
# 3. ADMINGA YUBORISH
# ==========================================
@router.callback_query(F.data.startswith("b_tariff_"))
async def select_business_tariff(call: CallbackQuery):
    with suppress(TelegramBadRequest):
        await call.answer("Tarif tanlandi!", show_alert=False)

    parts = call.data.split("_")
    ad_id = int(parts[3])
    tariffs = {
        "oddiy": "Bir martalik - 60.000 so'm",
        "vip": "Bir oy (Kun ora) - 600.000 so'm",
    }
    selected_tariff = tariffs.get(parts[2], "Kelishilgan")

    try:
        ad = await Advertisement.objects.select_related("user").aget(id=ad_id)

        details_copy = ad.details.copy()
        details_copy["tariff"] = selected_tariff
        ad.details = details_copy
        ad.status = Advertisement.Status.PENDING
        await ad.asave()

        from core.config import ADMIN_GROUP_ID
        from bot.keyboards.inline.auto_inline import get_admin_action_kb
        from bot.utils.formatters import get_admin_footer

        admin_text = ad.details.get("business_text", "")
        admin_text += get_admin_footer(ad.user, selected_tariff)
        media_list = ad.details.get("media_list", [])

        if ADMIN_GROUP_ID != 0:
            if media_list:
                await send_ad_media(
                    bot=call.bot, chat_id=ADMIN_GROUP_ID,
                    media_list=media_list, caption=admin_text,
                    reply_markup=get_business_admin_kb(ad_id)
                )
            else:
                await call.bot.send_message(
                    chat_id=ADMIN_GROUP_ID, text=admin_text,
                    parse_mode="HTML",
                    reply_markup=get_business_admin_kb(ad_id)
                )

        success_text = "✅ <b>Biznes e'loningiz adminga yuborildi!</b>\nAdminlar ko'rib chiqib tasdiqlagach to'lov so'raladi, iltimos kuting..."

        if call.message.text:
            await call.message.edit_text(text=success_text, parse_mode="HTML")
        else:
            await call.message.edit_reply_markup(reply_markup=None)
            await call.message.reply(success_text, parse_mode="HTML")

    except Exception as e:
        logger.exception(f"Adminga yuborishda xato: {e}")

@router.callback_query(F.data.startswith("b_edit_"))
async def user_edit_business_ad(call: CallbackQuery, state: FSMContext):
    with suppress(TelegramBadRequest):
        await call.answer()
        await call.message.delete()

    ad_id = int(call.data.split("_")[-1])
    await Advertisement.objects.filter(id=ad_id).adelete()

    await state.set_state(BusinessAdState.waiting_for_post)
    await call.message.answer(
        "📝 <b>E'loningizni tahrirlangan holatda qayta yuboring:</b>\n\n"
        "<i>(Bekor qilish uchun pastdagi tugmani bosing)</i>",
        parse_mode="HTML", reply_markup=cancel_kb()
    )

# ==========================================
# BEKOR QILISH
# ==========================================
@router.callback_query(F.data.startswith("b_cancel_"))
async def cancel_business_ad(call: CallbackQuery):
    with suppress(TelegramBadRequest):
        await call.answer("E'lon bekor qilindi", show_alert=False)
        await call.message.delete()

    ad_id = int(call.data.split("_")[-1])
    await Advertisement.objects.filter(id=ad_id).adelete()

    await call.message.answer("❌ <b>Biznes e'loni bekor qilindi.</b>", parse_mode="HTML", reply_markup=main_menu_kb)
