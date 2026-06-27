import logging
from contextlib import suppress
from aiogram import Router, F, Bot
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from bot.keyboards.reply.main_menu import main_menu_kb
from bot.keyboards.reply.common_reply import cancel_kb, skip_cancel_kb, multi_phone_kb, skip_kb
from bot.states.ad_states import AutoAdState, BusinessAdState, HouseAdState, PhoneAdState, OtherAdState, \
    ReadyOtherAdState, PaymentState, LostFoundState

router = Router()


# =========================================================================
# 🛑 ADMIN E'LONINI QAYTA TIKLASH FUNKSIYASI (YANGI)
# =========================================================================
async def restore_admin_ad(message: Message, ad_id: int):
    from bot.models import Advertisement
    from bot.utils.helpers import get_ad_type
    from bot.keyboards.inline.auto_inline import get_admin_action_kb
    from bot.keyboards.inline.house_inline import get_house_admin_kb
    from bot.keyboards.inline.phone_inline import get_phone_admin_kb
    from bot.keyboards.inline.other_inline import get_other_admin_kb
    from bot.keyboards.inline.business_inline import get_business_admin_kb
    from bot.keyboards.inline.lost_found_inline import get_lf_admin_kb
    from bot.utils.formatters import format_auto_text, format_house_text, format_phone_text, format_other_text, \
        format_lost_found_text, get_admin_footer
    from bot.utils.media_sender import send_ad_media

    try:
        ad = await Advertisement.objects.aget(id=ad_id)
        ad_type = get_ad_type(ad)

        if ad_type == "Biznes":
            admin_text = ad.details.get("business_text", "")
            kb = get_business_admin_kb(ad.id)
        elif ad_type == "Uy-joy":
            admin_text = format_house_text(ad.details, ad.phone_numbers) + "\n\n👉 <b>@XonobodBugun</b>"
            kb = get_house_admin_kb(ad.id)
        elif ad_type == "Telefon":
            admin_text = format_phone_text(ad.details, ad.phone_numbers)
            kb = get_phone_admin_kb(ad.id)
        elif ad_type == "Boshqa":
            admin_text = ad.details.get("custom_admin_text", "")
            if not admin_text: admin_text = format_other_text(ad.details, ad.phone_numbers)
            kb = get_other_admin_kb(ad.id)
        elif ad_type == "Yo'qolgan/Topilgan":
            admin_text = format_lost_found_text(ad.details, ad.phone_numbers)
            kb = get_lf_admin_kb(ad.id)
        else:
            admin_text = format_auto_text(ad.details, ad.phone_numbers)
            kb = get_admin_action_kb(ad.id)

        tariff = ad.details.get("tariff", "Kelishilgan")
        if ad_type == "Yo'qolgan/Topilgan": tariff = "Bepul"
        admin_text += get_admin_footer(ad.user, tariff)

        media_list = ad.details.get("media_list", [])

        # Pastdagi xalaqit beruvchi tugmalarni o'chirib, ma'lumot beramiz
        await message.answer("🔙 <b>Jarayon bekor qilindi. E'lon asliga qaytarildi:</b>", parse_mode="HTML",
                             reply_markup=ReplyKeyboardRemove())

        # E'lonni qaytadan to'liq tashlab beramiz
        if media_list:
            await send_ad_media(bot=message.bot, chat_id=message.chat.id, media_list=media_list, caption=admin_text,
                                reply_markup=kb)
        else:
            await message.answer(text=admin_text, parse_mode="HTML", reply_markup=kb)
    except Exception as e:
        logging.getLogger(__name__).error(f"Admin e'lonni tiklashda xato: {e}")
        await message.answer("🔙 Jarayon bekor qilindi.", reply_markup=ReplyKeyboardRemove())


@router.message(F.text == "❌ Bekor qilish", StateFilter('*'))
async def cancel_any_process(message: Message, state: FSMContext, bot: Bot):
    current_state = await state.get_state()
    data = await state.get_data()

    # 1. FOYDALANUVCHI TO'LOVDAN QOCHGANDA
    if current_state == PaymentState.waiting_for_receipt.state:
        ad_id = data.get("payment_ad_id")
        if ad_id:
            with suppress(Exception):
                from bot.models import Advertisement
                from core.config import ADMIN_GROUP_ID
                ad = await Advertisement.objects.aget(id=ad_id)
                ad.status = Advertisement.Status.DRAFT
                await ad.asave()
                alert_text = f"⚠️ <b>DIQQAT:</b> #{ad_id} e'lon egasi to'lov qilishdan yuz o'girdi va jarayonni bekor qildi."
                await bot.send_message(chat_id=ADMIN_GROUP_ID, text=alert_text, parse_mode="HTML")

    # 2. 🛑 ADMIN GURUHI UCHUN HIMOYA (E'lon havoga uchib ketmasligi uchun)
    is_admin = message.chat.type in ['group', 'supergroup']
    if is_admin:
        ad_id = data.get("edit_ad_id") or data.get("reject_ad_id")
        await state.clear()

        # Agar admin qaysidir e'lonni tahrirlayotgan bo'lsa, uni tiklaymiz
        if ad_id:
            return await restore_admin_ad(message, ad_id)

        return await message.answer("🛑 Jarayon bekor qilindi.", reply_markup=ReplyKeyboardRemove())

    # 3. ODDIY FOYDALANUVCHILAR UCHUN
    if current_state is not None:
        await state.clear()
    await message.answer("🚫 Jarayon bekor qilindi. Bosh menyudasiz:", reply_markup=main_menu_kb)


# =========================================================================
# ORQAGA QAYTISH MANTIQI
# =========================================================================

AUTO_BACK_MAP = {
    AutoAdState.year: (AutoAdState.model, "🚗 Avtomobil rusumini kiriting\n<i>(Masalan: Matiz Best):</i>", cancel_kb()),
    AutoAdState.distance: (AutoAdState.year, "📅 Avtomobil yilini kiriting (Masalan: 2020):", cancel_kb()),
    AutoAdState.coat: (AutoAdState.distance, "📟 Yurgani (Probeg qancha)?", cancel_kb()),
    AutoAdState.condition: (AutoAdState.coat, "🎨 Kraska holati qanday?", cancel_kb()),
    AutoAdState.oil: (AutoAdState.condition, "⚙️ Texnik holati qanday?", cancel_kb()),
    AutoAdState.info: (AutoAdState.oil, "⛽️ Yoqilg'i turi (Benzin, Gaz, Propan)?", cancel_kb()),
    AutoAdState.price: (AutoAdState.info, "✍️ Qo'shimcha ma'lumot? (Yoki o'tkazib yuboring)", skip_kb()),
    AutoAdState.phone: (AutoAdState.price, "💰 Narxini kiriting:", cancel_kb()),
    AutoAdState.location: (AutoAdState.phone,
                           "☎️ <b>Telefon raqamingizni kiriting:</b>\n\n<i>📱 Bitta raqam yuborish uchun pastdagi tugmani bosing.\n✍️ Yana raqam qo'shmoqchi bo'lsangiz, yozib yuborishingiz mumkin.</i>",
                           multi_phone_kb()),
    AutoAdState.photo: (AutoAdState.location, "📍 Manzilni kiriting (Masalan: Xonobod shahar):", cancel_kb()),
}

HOUSE_BACK_MAP = {
    HouseAdState.price: (
    HouseAdState.info, "✍️ <b>Qo'shimcha ma'lumotlar:</b>\n\n<i>(Ixtiyoriy. O'tkazib yuborishingiz mumkin)</i>",
    skip_cancel_kb()),
    HouseAdState.phone: (
    HouseAdState.price, "💰 <b>Narxini kiriting:</b>\n\n<i>(Masalan: 35,000$ yoki Kelishamiz)</i>", cancel_kb()),
    HouseAdState.location: (HouseAdState.phone,
                            "☎️ <b>Telefon raqamingizni kiriting:</b>\n\n<i>📱 Bitta raqam yuborish uchun pastdagi tugmani bosing.\n✍️ Yana raqam qo'shmoqchi bo'lsangiz, yozib yuborishingiz mumkin.</i>",
                            multi_phone_kb()),
    HouseAdState.photos: (
    HouseAdState.location, "📍 <b>Manzilni kiriting:</b>\n\n<i>(Masalan: Xonobod shahri, markazda)</i>", cancel_kb()),
}

PHONE_BACK_MAP = {
    PhoneAdState.memory: (PhoneAdState.model, "📱 <b>Telefon rusumini kiriting:</b>", cancel_kb()),
    PhoneAdState.condition: (PhoneAdState.memory, "💾 <b>Xotirasini kiriting:</b>", cancel_kb()),
    PhoneAdState.box_docs: (PhoneAdState.condition, "🛠 <b>Holati qanday?</b>", cancel_kb()),
    PhoneAdState.info: (PhoneAdState.box_docs, "📦 <b>Karobka va Dokument bormi?</b>", cancel_kb()),
    PhoneAdState.price: (PhoneAdState.info, "✍️ <b>Qo'shimcha ma'lumotlar:</b>", skip_kb()),
    PhoneAdState.phone: (PhoneAdState.price, "💰 <b>Narxini kiriting:</b>", cancel_kb()),
    PhoneAdState.location: (
    PhoneAdState.phone, "☎️ <b>Telefon raqamingizni kiriting:</b>\n\n<i>📱 Bitta raqam yuborish uchun pastdagi tugmani bosing.\n✍️ Yana raqam qo'shmoqchi bo'lsangiz, yozib yuborishingiz mumkin.</i>", multi_phone_kb()),
    PhoneAdState.photos: (PhoneAdState.location, "📍 <b>Manzilni kiriting:</b>", cancel_kb()),
}

OTHER_BACK_MAP = {
    OtherAdState.info: (OtherAdState.title, "🛍 <b>Nima sotmoqchisiz?</b>", cancel_kb()),
    OtherAdState.price: (OtherAdState.info, "✍️ <b>Qo'shimcha ma'lumotlar:</b>", skip_kb()),
    OtherAdState.phone: (OtherAdState.price, "💰 <b>Narxi:</b>", cancel_kb()),
    OtherAdState.location: (
    OtherAdState.phone, "☎️ <b>Telefon raqamingizni kiriting:</b>\n\n<i>📱 Bitta raqam yuborish uchun pastdagi tugmani bosing.\n✍️ Yana raqam qo'shmoqchi bo'lsangiz, yozib yuborishingiz mumkin.</i>", multi_phone_kb()),
    OtherAdState.photos: (OtherAdState.location, "📍 <b>Manzilni kiriting:</b>", cancel_kb()),
}

LF_BACK_MAP = {
    LostFoundState.location: (LostFoundState.item, "📦 <b>Nima buyum? (Qisqa va aniq yozing)</b>", cancel_kb()),
    LostFoundState.info: (LostFoundState.location, "📍 <b>Qayerda? (Qaysi hududda)</b>", cancel_kb()),
    LostFoundState.phone: (LostFoundState.info, "📝 <b>Qo'shimcha ma'lumot bormi?</b>", skip_cancel_kb()),
    LostFoundState.photo: (LostFoundState.phone, "📞 <b>Aloqa uchun raqam:</b>", multi_phone_kb()),
}

BACK_MAP = {**AUTO_BACK_MAP, **HOUSE_BACK_MAP, **PHONE_BACK_MAP, **OTHER_BACK_MAP, **LF_BACK_MAP}


@router.message(F.text == "⬅️ Orqaga", StateFilter('*'))
async def step_back_process(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None: return

    # 1. 🛑 ADMIN GURUHI UCHUN HIMOYA
    is_admin = message.chat.type in ['group', 'supergroup']
    if is_admin:
        data = await state.get_data()
        ad_id = data.get("edit_ad_id") or data.get("reject_ad_id")
        await state.clear()

        # Agar admin qaysidir e'lonni tahrirlayotgan bo'lsa, uni tiklaymiz
        if ad_id:
            return await restore_admin_ad(message, ad_id)

        return await message.answer("🔙 Jarayon bekor qilindi.", reply_markup=ReplyKeyboardRemove())

    # 2. ODDIY FOYDALANUVCHILAR UCHUN
    from bot.keyboards.inline.ad_types import get_ad_type_kb, get_trade_categories_kb
    from bot.keyboards.inline.house_inline import get_house_action_kb
    from bot.keyboards.inline.other_inline import get_other_type_kb
    from bot.keyboards.inline.lost_found_inline import get_lf_type_kb

    if current_state.startswith("Edit"):
        await state.clear()
        return await message.answer("🔙 O'zgartirish bekor qilindi. O'zingizga kerakli bo'limni tanlang:",
                                    reply_markup=main_menu_kb)

    if current_state in [AutoAdState.model.state, PhoneAdState.model.state]:
        await state.clear()
        await message.answer("🔙 Harakat bekor qilindi.", reply_markup=main_menu_kb)
        return await message.answer("Ajoyib, qaysi yo'nalishda elon bermoqchisiz? 👇",
                                    reply_markup=get_trade_categories_kb())

    if current_state in [OtherAdState.title.state, ReadyOtherAdState.waiting_for_post.state]:
        await state.clear()
        await message.answer("🔙 Harakat bekor qilindi.", reply_markup=main_menu_kb)
        return await message.answer("🛒 <b>Boshqa turdagi e'lonlar bo'limi</b>\n\nQanday usulda e'lon bermoqchisiz?",
                                    parse_mode="HTML", reply_markup=get_other_type_kb())

    if current_state == LostFoundState.item.state:
        await state.clear()
        await message.answer("🔙 Harakat bekor qilindi.", reply_markup=main_menu_kb)
        return await message.answer("Siz nimanidir yo'qotdingizmi yoki topib oldingizmi?",
                                    reply_markup=get_lf_type_kb())

    if current_state == BusinessAdState.waiting_for_post.state:
        await state.clear()
        await message.answer("🔙 Asosiy menyuga qaytdingiz:", reply_markup=main_menu_kb)
        return await message.answer("Qaysi turdagi e'lonni bermoqchisiz? 👇", reply_markup=get_ad_type_kb())

    if current_state in [s.state for s in HouseAdState]:
        data = await state.get_data()
        prop_type = data.get("property_type", "")
        if (current_state == HouseAdState.building_name.state) or (
                current_state == HouseAdState.area.state and "Hovli" in prop_type) or (
                current_state == HouseAdState.rooms.state and "Kvartira" in prop_type):
            await state.clear()
            await state.update_data(property_type=prop_type)
            await message.answer("🔙 Harakat bekor qilindi.", reply_markup=main_menu_kb)
            return await message.answer(f"Tanlandi: <b>{prop_type}</b>\n\n👇 Endi e'lon maqsadini tanlang:",
                                        parse_mode="HTML", reply_markup=get_house_action_kb())

        if current_state == HouseAdState.area.state and "Noturar" in prop_type: return await message.answer(
            "🏪 <b>Obyekt nomini kiriting:</b>", parse_mode="HTML", reply_markup=cancel_kb())
        if current_state == HouseAdState.rooms.state and "Hovli" in prop_type: return await message.answer(
            "📏 <b>Yer maydoni qancha?</b>", parse_mode="HTML", reply_markup=cancel_kb())
        if current_state == HouseAdState.floor.state: return await message.answer("🔢 <b>Necha xonadan iborat?</b>",
                                                                                  parse_mode="HTML",
                                                                                  reply_markup=cancel_kb())
        if current_state == HouseAdState.docs.state: return await message.answer("📏 <b>Yer maydoni qancha?</b>",
                                                                                 parse_mode="HTML",
                                                                                 reply_markup=cancel_kb())

        if current_state == HouseAdState.conditions.state:
            if "Kvartira" in prop_type:
                await state.set_state(HouseAdState.floor)
                return await message.answer("🏢 <b>Nechanchi qavatda joylashgan?</b>", parse_mode="HTML",
                                            reply_markup=cancel_kb())
            elif "Hovli" in prop_type:
                await state.set_state(HouseAdState.rooms)
                return await message.answer("🔢 <b>Necha xonadan iborat?</b>", parse_mode="HTML",
                                            reply_markup=cancel_kb())
            else:
                await state.set_state(HouseAdState.docs)
                return await message.answer("📄 <b>Hujjatlari qanday?</b>", parse_mode="HTML", reply_markup=cancel_kb())

        if current_state == HouseAdState.condition_state.state:
            await state.set_state(HouseAdState.conditions)
            return await message.answer("🚰 <b>Sharoitlar qanday?</b>", parse_mode="HTML", reply_markup=cancel_kb())

        if current_state == HouseAdState.info.state:
            if "Noturar" in prop_type:
                await state.set_state(HouseAdState.conditions)
                return await message.answer("🚰 <b>Sharoitlar qanday?</b>", parse_mode="HTML", reply_markup=cancel_kb())
            else:
                await state.set_state(HouseAdState.condition_state)
                return await message.answer("🛠 <b>Remonti (Holati) qanday?</b>", parse_mode="HTML",
                                            reply_markup=cancel_kb())

    for state_key, (prev_state, text, keyboard) in BACK_MAP.items():
        if current_state == state_key.state:
            await state.set_state(prev_state)
            return await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

    await message.answer("❗️ Orqaga qaytib bo'lmaydi. Yoki bekor qiling, yoki ma'lumotni kiriting.")