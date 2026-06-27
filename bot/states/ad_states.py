from aiogram.fsm.state import State, StatesGroup

class AutoAdState(StatesGroup):
    model = State()      # 1. Mashina rusumi
    year = State()       # 2. Yili
    distance = State()   # 3. Probeg
    coat = State()       # 4. Kraska
    condition = State()  # 5. Holati
    oil = State()        # 6. Yoqilg'i
    info = State()       # 7. Qo'shimcha ma'lumot
    price = State()      # 8. Narxi
    phone = State()      # 9. Telefon raqam(lar)
    location = State()   # 10. Manzil
    photo = State()      # 11. Rasm


class PaymentState(StatesGroup):
    waiting_for_receipt = State() # Mijozdan chek rasmini kutish holati


class EditAutoState(StatesGroup):
    waiting_for_text = State()  # Barcha oddiy matnlar (rusum, yil, narx, probeg...) uchun 1 ta universal holat
    waiting_for_photo = State() # Rasmlarni qayta yuklash uchun


class BusinessAdState(StatesGroup):
    waiting_for_post = State() # Tayyor postni kutish


class AdminEditState(StatesGroup):
    waiting_for_new_post = State()


class HouseAdState(StatesGroup):
    property_type = State()  # Kvartira, Hovli, Noturar joy
    action_type = State()  # Sotiladi, Ijaraga

    # 1. Shoxlanuvchi savollar (Dinamik ishlaydi)
    building_name = State()  # Nomi (Faqat Noturar uchun)
    rooms = State()  # Xonalar soni (Kvartira, Hovli)
    floor = State()  # Qavati (Faqat Kvartira)
    area = State()  # Yer maydoni (Hovli, Noturar)
    docs = State()  # Hujjatlari (Faqat Noturar)

    # 2. Umumiy savollar
    conditions = State()  # Sharoitlar
    condition_state = State()  # Remonti/Holati (Kvartira, Hovli)
    info = State()  # Qo'shimcha ma'lumot
    price = State()  # Narxi
    phone = State()  # Telefon
    location = State()  # Manzil
    photos = State()  # Rasmlar


class EditHouseState(StatesGroup):
    waiting_for_text = State()
    waiting_for_photo = State()


class AdminRejectState(StatesGroup):
    waiting_for_reason = State()


class PhoneAdState(StatesGroup):
    model = State()         # Rusumi (Masalan: iPhone 13 Pro)
    memory = State()        # Xotirasi (Masalan: 128 GB)
    condition = State()     # Holati (Yangi, Ideal, Qirilgan)
    box_docs = State()      # Karobka-Dokument (Bor/Yo'q)
    info = State()          # Qo'shimcha ma'lumot
    price = State()         # Narxi
    phone = State()         # Telefon raqami
    location = State()      # Manzil
    photos = State()        # Rasmlar

class EditPhoneState(StatesGroup):
    waiting_for_text = State()
    waiting_for_photo = State()


class OtherAdState(StatesGroup):
    title = State()       # Nima sotmoqchisiz?
    info = State()        # Qo'shimcha ma'lumot
    price = State()       # Narxi
    phone = State()       # Telefon
    location = State()    # Manzil
    photos = State()      # Rasm

class ReadyOtherAdState(StatesGroup):
    waiting_for_post = State()  # Tayyor e'lonni kutish


class LostFoundState(StatesGroup):
    item = State()       # Buyum
    location = State()   # Qayerda
    info = State()       # Qo'shimcha ma'lumot
    phone = State()      # Aloqa raqami
    photo = State()      # Rasm


class EditLFState(StatesGroup):
    waiting_for_text = State()
    waiting_for_photo = State()


class EditOtherState(StatesGroup):
    waiting_for_text = State()
    waiting_for_photo = State()