from django.db import models


# ==========================================
# 0. ASOSIY (ABSTRACT) MODEL
# ==========================================
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqti")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan vaqti")

    class Meta:
        abstract = True


# ==========================================
# 1. FOYDALANUVCHILAR JADVALI
# ==========================================
class TelegramUser(TimeStampedModel):
    user_id = models.BigIntegerField(unique=True, verbose_name="Telegram ID")
    full_name = models.CharField(max_length=255, verbose_name="To'liq ismi")
    username = models.CharField(max_length=255, null=True, blank=True, verbose_name="Username")

    def __str__(self):
        return f"{self.full_name} ({self.user_id})"

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "1. Foydalanuvchilar"


# ==========================================
# 2. KATEGORIYALAR JADVALI
# ==========================================
class Category(TimeStampedModel):
    name = models.CharField(max_length=50, verbose_name="Kategoriya nomi")
    callback_data = models.CharField(max_length=50, unique=True, verbose_name="Tugma (Callback) data")
    is_active = models.BooleanField(default=True, verbose_name="Aktivmi?")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "2. Kategoriyalar"


# ==========================================
# 3. E'LONLAR JADVALI (ASOSIY YURAK)
# ==========================================
class Advertisement(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = 'draft', "Qoralama (Yozilmoqda)"
        PENDING = 'pending', "Kutilmoqda (Adminga yuborilgan)"
        APPROVED = 'approved', "Tasdiqlangan"
        REJECTED = 'rejected', "Rad etilgan"

    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, verbose_name="Foydalanuvchi")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, verbose_name="Kategoriya")

    # Avto, Kvartira, Hovli kabi turlicha shablonlarga moslashuvchan maydon
    details = models.JSONField(default=dict, verbose_name="E'lon tafsilotlari")

    # Bitta e'londa 2-3 ta raqam qabul qilish uchun kengaytirilgan maydon
    phone_numbers = models.CharField(max_length=255, verbose_name="Aloqa raqamlari")

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, verbose_name="Holati")

    # Media xabarlarni xavfsiz va aniq o'chirish uchun ID larni ro'yxat ko'rinishida saqlaymiz
    message_ids = models.JSONField(default=list, blank=True, verbose_name="Xabar ID lari")

    def __str__(self):
        return f"E'lon #{self.id} | {self.user.full_name}"

    class Meta:
        verbose_name = "E'lon"
        verbose_name_plural = "3. Barcha E'lonlar"


# ==========================================
# 4. VAKANSIYALAR (BO'SH ISH O'RINLARI)
# ==========================================
class Vacancy(TimeStampedModel):
    title = models.CharField(max_length=255, verbose_name="Lavozim / Kasb")
    company = models.CharField(max_length=255, verbose_name="Ish joyi nomi")
    salary = models.CharField(max_length=100, verbose_name="Maosh (Oylik)")
    requirements = models.TextField(verbose_name="Talablar va Sharoitlar")
    phone = models.CharField(max_length=100, verbose_name="Aloqa uchun raqam")
    is_active = models.BooleanField(default=True, verbose_name="Aktivmi? (Saytda ko'rinishi)")

    def __str__(self):
        return f"{self.title} - {self.company}"

    class Meta:
        verbose_name = "Vakansiya"
        verbose_name_plural = "4. Vakansiyalar"