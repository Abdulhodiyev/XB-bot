import logging
import math
from contextlib import suppress
from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from bot.models import Advertisement
from bot.keyboards.inline.cabinet_inline import get_my_ads_page_kb, get_ad_action_kb
from bot.utils.formatters import format_auto_text, format_house_text, format_phone_text, format_other_text, format_lost_found_text
from bot.utils.media_sender import send_ad_media
from bot.utils.helpers import get_ad_type

logger = logging.getLogger(__name__)
router = Router()

ITEMS_PER_PAGE = 5


async def get_ads_page_text(ads: list, page: int) -> str:
    status_dict = {
        "draft": "📝 Qoralama", "pending": "⏳ Kutilmoqda",
        "approved": "✅ Kanalda", "rejected": "❌ Rad etilgan", "sold": "🤝 Sotilgan"
    }

    text = f"🗂 <b>Sizning e'lonlaringiz ({page}-sahifa):</b>\n\n"

    for i, ad in enumerate(ads, start=1):
        is_sold = ad.details.get("is_sold", False)
        cat_name = get_ad_type(ad)

        # 🛑 TO'G'RILANDI: LF uchun alohida status
        if is_sold:
            status = "✅ Egasi topildi" if cat_name == "Yo'qolgan/Topilgan" else "🤝 Sotilgan"
        else:
            status = status_dict.get(ad.status, "Noma'lum")

        title = ""
        if cat_name == "Biznes":
            raw_text = ad.details.get("business_text", "Biznes e'loni")
            clean_title = raw_text.replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>",
                                                                                                     "").replace("\n",
                                                                                                                 " ")
            title = clean_title[:30] + "..." if len(clean_title) > 30 else clean_title
        elif cat_name == "Uy-joy":
            prop_type = ad.details.get('property_type', '')
            action = ad.details.get('action_type', '')
            title = f"{prop_type} ({action})"
        elif cat_name == "Telefon":
            title = f"{ad.details.get('model', '')} {ad.details.get('memory', '')}".strip()
        elif cat_name == "Boshqa":
            if ad.details.get("is_ready_post"):
                raw_text = ad.details.get("custom_admin_text", "Boshqa e'lon")
                clean_title = raw_text.replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>",
                                                                                                         "").replace(
                    "\n", " ")
                title = clean_title[:30] + "..." if len(clean_title) > 30 else clean_title
            else:
                title = ad.details.get('title', 'Boshqa buyum').strip()
        elif cat_name == "Yo'qolgan/Topilgan":
            title = f"LF: {ad.details.get('item', '')}"
        else:
            title = f"{ad.details.get('model', '')} {ad.details.get('year', '')}".strip()

        text += f"{i}️⃣ <b>{cat_name}:</b> {title}\n└ <i>Holati:</i> {status}\n\n"

    text += "👇 <b>Batafsil ko'rish uchun pastdagi raqamlarni bosing:</b>"
    return text

async def render_ads_page(bot: Bot, chat_id: int, user_id: int, page: int = 1, is_edit: bool = False, msg_to_edit: Message = None):
    all_ads = [ad async for ad in Advertisement.objects.filter(user__user_id=user_id).order_by("-created_at")]

    if not all_ads:
        empty_text = "📭 <b>Sizda hozircha e'lonlar yo'q.</b>"
        if is_edit: return await msg_to_edit.edit_text(empty_text, parse_mode="HTML")
        return await bot.send_message(chat_id=chat_id, text=empty_text, parse_mode="HTML")

    total_pages = math.ceil(len(all_ads) / ITEMS_PER_PAGE)
    if page > total_pages: page = total_pages
    if page < 1: page = 1

    start_idx = (page - 1) * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    current_ads = all_ads[start_idx:end_idx]

    text = await get_ads_page_text(current_ads, page)
    kb = get_my_ads_page_kb(current_ads, page, total_pages)

    if is_edit:
        with suppress(TelegramBadRequest):
            await msg_to_edit.edit_text(text, parse_mode="HTML", reply_markup=kb)
    else:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML", reply_markup=kb)

@router.message(F.text.contains("elonlarim") | F.text.contains("e'lonlarim"), StateFilter('*'))
async def show_my_ads_list(message: Message, state: FSMContext):
    if state: await state.clear()
    await render_ads_page(message.bot, message.chat.id, message.from_user.id, page=1)

@router.callback_query(F.data.startswith("myads_page_"))
async def process_page_change(call: CallbackQuery):
    with suppress(TelegramBadRequest): await call.answer()
    page = int(call.data.split("_")[-1])
    await render_ads_page(call.bot, call.message.chat.id, call.from_user.id, page=page, is_edit=True, msg_to_edit=call.message)

@router.callback_query(F.data == "myad_back_list")
async def back_to_ads_list(call: CallbackQuery):
    with suppress(TelegramBadRequest):
        await call.answer()
        await call.message.delete()
    await render_ads_page(call.bot, call.message.chat.id, call.from_user.id, page=1)

@router.callback_query(F.data == "ignore")
async def ignore_pagination(call: CallbackQuery):
    await call.answer()


@router.callback_query(F.data.startswith("myad_view_"))
async def view_single_ad(call: CallbackQuery):
    with suppress(TelegramBadRequest):
        await call.answer()
        await call.message.delete()

    ad_id = int(call.data.split("_")[-1])
    try:
        ad = await Advertisement.objects.aget(id=ad_id)
        cat_name = get_ad_type(ad)

        if cat_name == "Biznes":
            text = ad.details.get("business_text", "")
        elif cat_name == "Uy-joy":
            text = format_house_text(ad.details, ad.phone_numbers) + "\n\n👉 <b>@XonobodBugun</b>"
        elif cat_name == "Telefon":
            text = format_phone_text(ad.details, ad.phone_numbers)
        elif cat_name == "Boshqa":
            text = ad.details.get("custom_admin_text", "")
            if not text: text = format_other_text(ad.details, ad.phone_numbers)
        elif cat_name == "Yo'qolgan/Topilgan":
            text = format_lost_found_text(ad.details, ad.phone_numbers)
        else:
            text = format_auto_text(ad.details, ad.phone_numbers)

        is_sold = ad.details.get("is_sold", False)
        status_text = {
            "draft": "📝 Qoralama", "pending": "⏳ Tasdiq kutilmoqda",
            "approved": "✅ Kanalda faol", "rejected": "❌ Rad etilgan", "paid": "💸 To'lov qilingan"
        }

        # 🛑 TO'G'RILANDI: LF uchun alohida status
        if is_sold:
            current_status = "✅ Egasi topildi" if cat_name == "Yo'qolgan/Topilgan" else "🤝 Sotilgan/Kelishilgan"
        else:
            current_status = status_text.get(ad.status, 'Noma\'lum')

        text = f"<b>Holati:</b> {current_status}\n\n" + text
        media_list = ad.details.get("media_list", [])

        if media_list:
            await send_ad_media(bot=call.bot, chat_id=call.message.chat.id, media_list=media_list, caption=text,
                                reply_markup=get_ad_action_kb(ad_id, ad.status, cat_name))
        else:
            await call.message.answer(text=text, parse_mode="HTML",
                                      reply_markup=get_ad_action_kb(ad_id, ad.status, cat_name))
    except Exception as e:
        logger.exception(e)
        await call.message.answer("⚠️ E'lonni yuklashda xatolik yuz berdi.")


@router.callback_query(F.data.startswith("myad_sold_"))
async def mark_ad_as_sold(call: CallbackQuery, bot: Bot):
    ad_id = int(call.data.split("_")[-1])
    try:
        ad = await Advertisement.objects.aget(id=ad_id)
        cat_name = get_ad_type(ad)

        if cat_name == "Biznes": return await call.answer("❗️ Biznes e'lonlarini o'zgartirib bo'lmaydi.",
                                                          show_alert=True)
        if ad.status != "approved": return await call.answer("Faol bo'lmagan e'lonni o'zgartirib bo'lmaydi.",
                                                             show_alert=True)
        if not ad.message_ids: return await call.answer("⚠️ E'lonning kanal xabari topilmadi.", show_alert=True)

        from core.config import CHANNEL_ID
        details_copy = ad.details.copy()
        details_copy["is_sold"] = True
        ad.details = details_copy

        # 🛑 MANTIQ TO'G'RILANDI: DB dagi raqam o'rniga nima yozilishi
        if cat_name == "Yo'qolgan/Topilgan":
            ad.phone_numbers = "✅ EGASI TOPILDI"
        else:
            ad.phone_numbers = "🤝 SOTILDI"

        await ad.asave()

        new_text = ""
        if cat_name == "Uy-joy":
            new_text = format_house_text(ad.details, ad.phone_numbers) + "\n\n👉 <b>@XonobodBugun</b>"
        elif cat_name == "Telefon":
            new_text = format_phone_text(ad.details, ad.phone_numbers)
        elif cat_name == "Boshqa":
            base_text = ad.details.get("custom_admin_text", "")
            if not base_text: base_text = format_other_text(ad.details, ad.phone_numbers)
            new_text = base_text + "\n\n<b>🤝 USHBU E'LON O'Z EGASINI TOPDI!</b>"
        elif cat_name == "Yo'qolgan/Topilgan":
            new_text = format_lost_found_text(ad.details, ad.phone_numbers)
        else:
            new_text = format_auto_text(ad.details, ad.phone_numbers)

        main_msg_id = ad.message_ids[0]
        try:
            media_list = ad.details.get("media_list", [])
            if media_list:
                await bot.edit_message_caption(chat_id=CHANNEL_ID, message_id=main_msg_id, caption=new_text,
                                               parse_mode="HTML")
            else:
                await bot.edit_message_text(chat_id=CHANNEL_ID, message_id=main_msg_id, text=new_text,
                                            parse_mode="HTML")

            # 🛑 KANALGA TASHALADIGAN QO'SHIMCHA XABAR (Reply)
            if cat_name == "Yo'qolgan/Topilgan":
                reply_text = "🎉 <b>Ushbu buyum tez orada o'z egasini topdi!</b>\nE'tiborli bo'lib, yordam bergan barchaga rahmat! 🤝"
            else:
                reply_text = "🎉 <b>Ushbu e'lon qisqa fursatda o'z egasini topdi!</b>\nIkkala tarafga ham baraka bersin! 🤝"

            await bot.send_message(chat_id=CHANNEL_ID, reply_to_message_id=main_msg_id, text=reply_text,
                                   parse_mode="HTML")

        except Exception as tg_error:
            logger.error(f"Kanalga yozishda Telegram API xatosi: {tg_error}")
            return await call.answer("⚠️ Telegram xatosi.", show_alert=True)

        await call.answer("Muvaffaqiyatli belgilandi!", show_alert=True)
        await back_to_ads_list(call)
    except Exception as e:
        logger.error(f"Sotildi/Topildi qilishda Dasturiy xato: {e}")
        await call.answer("Xatolik: Tizimda muammo yuz berdi.", show_alert=True)