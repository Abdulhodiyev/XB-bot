import logging
from contextlib import suppress
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from bot.keyboards.reply.common_reply import cancel_kb
from bot.models import Advertisement
from bot.keyboards.reply.main_menu import main_menu_kb
from bot.states.ad_states import AdminEditState
from bot.utils.formatters import get_admin_footer, format_auto_text, format_house_text, format_phone_text, \
    format_other_text
from bot.utils.media_sender import send_ad_media
from bot.utils.helpers import get_ad_type
from core.config import ADMIN_GROUP_ID

from bot.keyboards.inline.auto_inline import get_auto_tariff_kb, get_user_confirm_kb, get_admin_action_kb
from bot.keyboards.inline.house_inline import get_house_tariff_kb, get_house_confirm_kb, get_house_admin_kb, \
    get_house_edit_kb
from bot.keyboards.inline.phone_inline import get_phone_tariff_kb, get_phone_confirm_kb, get_phone_admin_kb, \
    get_phone_edit_kb
from bot.keyboards.inline.other_inline import get_other_tariff_kb, get_other_confirm_kb, get_other_admin_kb, \
    get_other_type_kb
from bot.keyboards.inline.business_inline import get_business_tariff_kb, get_business_confirm_kb, get_business_admin_kb
from bot.keyboards.inline.lost_found_inline import get_lf_admin_kb, get_lf_confirm_kb

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data.regexp(r"^(user|h|p|o|b)_cancel_(\d+)$"))
async def unified_cancel_ad(call: CallbackQuery):
    with suppress(TelegramBadRequest): await call.message.delete()
    ad_id = int(call.data.split("_")[-1])
    await Advertisement.objects.filter(id=ad_id).adelete()
    await call.message.answer("❌ <b>E'lon bekor qilindi.</b>", parse_mode="HTML", reply_markup=main_menu_kb)


@router.callback_query(F.data.regexp(r"^(user|h|p|o|b)_confirm_(\d+)$"))
async def unified_confirm_ad(call: CallbackQuery):
    parts = call.data.split("_")
    prefix, ad_id = parts[0], int(parts[-1])
    kb_map = {"user": get_auto_tariff_kb, "h": get_house_tariff_kb, "p": get_phone_tariff_kb, "o": get_other_tariff_kb,
              "b": get_business_tariff_kb}
    kb_func = kb_map.get(prefix)
    if not kb_func: return
    if call.message.text:
        await call.message.edit_text("<b>E'lon uchun tarifni tanlang:</b>", parse_mode="HTML",
                                     reply_markup=kb_func(ad_id))
    else:
        await call.message.edit_reply_markup(reply_markup=kb_func(ad_id))


# 1. Orqaga qaytish funksiyasini shunga almashtiring:
@router.callback_query(F.data.regexp(r"^(a|h|p|o|b|lf)_tback_(\d+)$"))
async def unified_back_to_confirm(call: CallbackQuery):
    parts = call.data.split("_")
    prefix, ad_id = parts[0], int(parts[-1])
    is_admin = call.message.chat.type in ['group', 'supergroup']

    # 🛑 HIMOYA: O (Boshqa e'lon) qadamma-qadamligini aniqlash
    is_ready = False
    if prefix == "o":
        with suppress(Exception):
            ad = await Advertisement.objects.aget(id=ad_id)
            is_ready = ad.details.get("is_ready_post", False)

    if is_admin:
        kb_map = {"a": get_admin_action_kb, "h": get_house_admin_kb, "p": get_phone_admin_kb, "o": get_other_admin_kb,
                  "b": get_business_admin_kb, "lf": get_lf_admin_kb}
        kb_func = kb_map.get(prefix)
        if not kb_func: return
        kb = kb_func(ad_id)
    else:
        if prefix == "a":
            kb = get_user_confirm_kb(ad_id)
        elif prefix == "h":
            kb = get_house_confirm_kb(ad_id)
        elif prefix == "p":
            kb = get_phone_confirm_kb(ad_id)
        elif prefix == "b":
            kb = get_business_confirm_kb(ad_id)
        elif prefix == "lf":
            kb = get_lf_confirm_kb(ad_id)
        elif prefix == "o":
            from bot.keyboards.inline.other_inline import get_other_confirm_kb
            kb = get_other_confirm_kb(ad_id, is_ready=is_ready)
        else:
            return

    if call.message.text:
        await call.message.edit_text("👇 <b>Harakatni tanlang:</b>", parse_mode="HTML", reply_markup=kb)
    else:
        await call.message.edit_reply_markup(reply_markup=kb)


# 2. Shu funksiyalarni tegishli joyiga (tahrirlash menyularini chaqiradigan joyga) qo'shib qo'ying:
@router.callback_query(F.data.startswith("o_edit_"))
async def show_other_edit_menu(call: CallbackQuery):
    with suppress(TelegramBadRequest):
        await call.answer()
    ad_id = int(call.data.split("_")[-1])
    from bot.keyboards.inline.other_inline import get_other_edit_kb
    if call.message.text:
        await call.message.edit_text("👇 Qaysi ma'lumotni o'zgartirmoqchisiz?", parse_mode="HTML",
                                     reply_markup=get_other_edit_kb(ad_id))
    else:
        await call.message.edit_reply_markup(reply_markup=get_other_edit_kb(ad_id))


# 3. ADMIN TAHRIRLASHI FUNKSIYASINI SHUNGA ALMASHTIRING:
@router.callback_query(F.data.startswith("admin_edit_tg_"))
async def admin_show_edit_unified(call: CallbackQuery, state: FSMContext):
    ad_id = int(call.data.split("_")[-1])
    try:
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
            # 🛑 YANGI QO'SHILDI: Agar "Boshqa" qadamma-qadam yasalgan bo'lsa
            from bot.keyboards.inline.other_inline import get_other_edit_kb
            await call.message.edit_reply_markup(reply_markup=get_other_edit_kb(ad_id))
        else:
            # FAQAT Biznes va Tayyor Boshqa e'lonlar uchun yaxlit matn so'raladi
            await state.set_state(AdminEditState.waiting_for_new_post)
            await state.update_data(edit_ad_id=ad_id)
            await call.message.delete()
            await call.message.answer(
                "✍️ <b>Ushbu e'lon uchun yangi matn va rasm/video yuboring:</b>\n\n<i>(Bekor qilish uchun pastdagi tugmani bosing)</i>",
                parse_mode="HTML", reply_markup=cancel_kb()
            )
    except Exception as e:
        logger.error(e)
        await call.answer("⚠️ Xatolik", show_alert=False)


@router.callback_query(F.data.startswith("h_edit_"))
async def show_house_edit_menu(call: CallbackQuery):
    with suppress(TelegramBadRequest):
        await call.answer()
    ad_id = int(call.data.split("_")[-1])
    ad = await Advertisement.objects.aget(id=ad_id)
    if call.message.text:
        await call.message.edit_text("<b>Qaysi ma'lumotni o'zgartirmoqchisiz?</b>", parse_mode="HTML",
                                     reply_markup=get_house_edit_kb(ad_id, ad.details.get("property_type", "")))
    else:
        await call.message.edit_reply_markup(reply_markup=get_house_edit_kb(ad_id, ad.details.get("property_type", "")))


@router.callback_query(F.data.startswith("p_edit_"))
async def show_phone_edit_menu(call: CallbackQuery):
    with suppress(TelegramBadRequest):
        await call.answer()
    ad_id = int(call.data.split("_")[-1])
    if call.message.text:
        await call.message.edit_text("Qaysi ma'lumotni o'zgartirmoqchisiz?", parse_mode="HTML",
                                     reply_markup=get_phone_edit_kb(ad_id))
    else:
        await call.message.edit_reply_markup(reply_markup=get_phone_edit_kb(ad_id))


@router.callback_query(F.data.startswith("o_restart_"))
async def restart_other_ad(call: CallbackQuery):
    with suppress(TelegramBadRequest): await call.message.delete()
    ad_id = int(call.data.split("_")[-1])
    await Advertisement.objects.filter(id=ad_id).adelete()
    await call.message.answer("🛒 <b>Boshqa turdagi e'lonlar bo'limi</b>\n\nQanday usulda e'lon bermoqchisiz?",
                              parse_mode="HTML", reply_markup=get_other_type_kb())


@router.callback_query(F.data.regexp(r"^(a|h|p|o|b)_tariff_([a-zA-Z0-9]+)_(\d+)$"))
async def unified_select_tariff(call: CallbackQuery):
    with suppress(TelegramBadRequest):
        await call.answer("Tarif tanlandi!", show_alert=False)
    parts = call.data.split("_")
    prefix, tariff_type, ad_id = parts[0], parts[2], int(parts[3])

    tariffs = {"oddiy": "1 martalik", "vip1": "Bir oy (Kun ora)", "vip2": "Bir oy (Har kuni)", "vip": "VIP e'lon"}
    price_map = {
        "a": {"oddiy": "20.000 so'm", "vip1": "200.000 so'm", "vip2": "400.000 so'm"},
        "h": {"oddiy": "20.000 so'm", "vip1": "200.000 so'm", "vip2": "400.000 so'm"},
        "p": {"oddiy": "20.000 so'm", "vip": "200.000 so'm"},
        "o": {"oddiy": "20.000 so'm", "vip": "200.000 so'm"},
        "b": {"oddiy": "60.000 so'm", "vip": "600.000 so'm"},
    }
    selected_tariff_name = f"{tariffs.get(tariff_type, 'Maxsus')} - {price_map.get(prefix, {}).get(tariff_type, 'Kelishilgan')}"

    try:
        ad = await Advertisement.objects.select_related("user", "category").aget(id=ad_id)
        details_copy = ad.details.copy()
        details_copy["tariff"] = selected_tariff_name
        ad.details = details_copy
        ad.status = Advertisement.Status.PENDING
        await ad.asave()

        ad_type = get_ad_type(ad)
        if ad_type == "Biznes":
            admin_text, admin_kb_func = ad.details.get("business_text", ""), get_business_admin_kb
        elif ad_type == "Uy-joy":
            admin_text, admin_kb_func = format_house_text(ad.details,
                                                          ad.phone_numbers) + "\n\n👉 <b>@XonobodBugun</b>", get_house_admin_kb
        elif ad_type == "Telefon":
            admin_text, admin_kb_func = format_phone_text(ad.details, ad.phone_numbers), get_phone_admin_kb
        elif ad_type == "Boshqa":
            admin_text = ad.details.get("custom_admin_text", "")
            if not admin_text: admin_text = format_other_text(ad.details, ad.phone_numbers)
            admin_kb_func = get_other_admin_kb
        else:
            admin_text, admin_kb_func = format_auto_text(ad.details, ad.phone_numbers), get_admin_action_kb

        admin_text += get_admin_footer(ad.user, selected_tariff_name)
        media_list = ad.details.get("media_list", [])

        if ADMIN_GROUP_ID != 0:
            if media_list:
                await send_ad_media(bot=call.bot, chat_id=ADMIN_GROUP_ID, media_list=media_list, caption=admin_text,
                                    reply_markup=admin_kb_func(ad_id))
            else:
                await call.bot.send_message(chat_id=ADMIN_GROUP_ID, text=admin_text, parse_mode="HTML",
                                            reply_markup=admin_kb_func(ad_id))

        with suppress(TelegramBadRequest):
            await call.message.delete()
        await call.message.answer(
            "✅ <b>E'loningiz adminga yuborildi!</b>\n\nAdminlar ko'rib chiqib tasdiqlagach to'lov so'raladi, iltimos kuting...",
            parse_mode="HTML", reply_markup=main_menu_kb)
    except Exception as e:
        logger.exception(e)


@router.callback_query(F.data.startswith("lf_confirm_"))
async def confirm_lf_ad(call: CallbackQuery):
    ad_id = int(call.data.split("_")[-1])
    try:
        ad = await Advertisement.objects.select_related("user").aget(id=ad_id)
        ad.status = Advertisement.Status.PENDING
        ad.details["tariff"] = "Bepul"
        await ad.asave()

        from bot.utils.formatters import format_lost_found_text
        admin_text = format_lost_found_text(ad.details, ad.phone_numbers) + get_admin_footer(ad.user, "Bepul")
        media_list = ad.details.get("media_list", [])

        if ADMIN_GROUP_ID != 0:
            if media_list:
                await send_ad_media(bot=call.bot, chat_id=ADMIN_GROUP_ID, media_list=media_list, caption=admin_text,
                                    reply_markup=get_lf_admin_kb(ad_id))
            else:
                await call.bot.send_message(chat_id=ADMIN_GROUP_ID, text=admin_text, parse_mode="HTML",
                                            reply_markup=get_lf_admin_kb(ad_id))

        with suppress(TelegramBadRequest):
            await call.message.delete()
        await call.message.answer("✅ <b>E'loningiz adminga yuborildi!</b>\n\n"
                                  "Bu xizmat bepul. Adminlar habar topsa kanalga joylanadi!", parse_mode="HTML",
                                  reply_markup=main_menu_kb)
    except Exception as e:
        logger.exception(e)