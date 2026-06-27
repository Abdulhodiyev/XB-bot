import os
from dotenv import load_dotenv

# .env fayldagi ma'lumotlarni yuklash
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_GROUP_ID = int(os.getenv("ADMIN_GROUP_ID", 0))

# Kelajakda botni boshqaradigan adminlar ro'yxati (xotira tejamkorligi uchun tuple ishlatamiz)
ADMINS = (927240176, 87654321)

CHANNEL_USERNAME = "@XonobodBugun"
CHANNEL_ID=-1001263501416