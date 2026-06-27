import logging
from contextlib import suppress

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from bot.keyboards.inline.ad_types import get_ad_type_kb, get_trade_categories_kb
from bot.states.ad_states import BusinessAdState
from bot.keyboards.reply.common_reply import cancel_kb

logger = logging.getLogger(__name__)
router = Router()


# ==========================================
# 🛑 HIMOYA QO'SHILDI: StateFilter('*') va state.clear()
# ==========================================
@router.message(F.text == "📢 Elon berish", StateFilter('*'))
async def process_create_ad(message: Message, state: FSMContext):
    # Agar mijoz boshqa joyda e'lon yozib yotgan bo'lsa, xotirani tozalaymiz!
    if state:
        await state.clear()

    await message.answer(
        "Qaysi turdagi e'lonni bermoqchisiz?",
        reply_markup=get_ad_type_kb()
    )


@router.callback_query(F.data == "ad_type_business")
async def process_business_ad(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer(
        "💼 <b>Biznes eloni tanladi</b>\n\n"
        "- E'loningizni tayyor holatda (rasm yoki video va matni bilan birga) yuboring!\n\n",
        parse_mode="HTML",
        reply_markup=cancel_kb()
    )
    await state.set_state(BusinessAdState.waiting_for_post)


@router.callback_query(F.data == "ad_type_trade")
async def process_trade_ad(call: CallbackQuery):
    await call.message.delete()
    await call.message.answer(
        "Ajoyib, qaysi yo'nalishda elon bermoqchisiz?",
        reply_markup=get_trade_categories_kb()
    )


@router.callback_query(F.data == "back_to_ad_types")
async def back_to_ad_types_menu(call: CallbackQuery):
    with suppress(TelegramBadRequest):
        await call.answer()

    # Eski xabarni tahrirlab, 1-qadamga qaytaramiz
    await call.message.edit_text(
        text="Qaysi turdagi e'lonni bermoqchisiz?",
        reply_markup=get_ad_type_kb()
    )