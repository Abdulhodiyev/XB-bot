import os
import django
import asyncio
import logging

# ==========================================
# 1. DJANGO NI SOZLASH (ENG MUHIM QADAM)
# ==========================================
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()

# ==========================================
# 2. BOT IMPORTLARI
# ==========================================
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from core.config import BOT_TOKEN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
    dp = Dispatcher()

    # 1. Middleware ni ulaymiz (Qorovul)
    from bot.middlewares.check_sub import CheckSubscriptionMiddleware
    dp.message.middleware(CheckSubscriptionMiddleware())
    dp.callback_query.middleware(CheckSubscriptionMiddleware())

    # 2. Routerlarni ulaymiz
    from bot.handlers import start, create_ad, auto_ad, navigation, admin_actions, edit_auto, business_ad, cabinet, house_ad, edit_house, phone_ad, edit_phone, other_ad, ad_actions, lost_found, edit_lf, information
    dp.include_router(start.router)
    dp.include_router(navigation.router)
    dp.include_router(create_ad.router)
    dp.include_router(auto_ad.router)
    dp.include_router(admin_actions.router)
    dp.include_router(edit_auto.router)
    dp.include_router(business_ad.router)
    dp.include_router(cabinet.router)
    dp.include_router(house_ad.router)
    dp.include_router(edit_house.router)
    dp.include_router(phone_ad.router)
    dp.include_router(edit_phone.router)
    dp.include_router(other_ad.router)
    dp.include_router(ad_actions.router)
    dp.include_router(lost_found.router)
    dp.include_router(edit_lf.router)
    dp.include_router(information.router)

    logger.info("Bot ishga tushirildi... 🚀")

    # Bot o'chiq paytida kelgan eski xabarlarga javob bermasligi uchun
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot to'xtatildi! 🛑")