from django.contrib import admin
from .models import TelegramUser, Category, Advertisement, Vacancy


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'full_name', 'username', 'created_at')
    search_fields = ('user_id', 'full_name', 'username')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'callback_data', 'is_active')
    search_fields = ('name', 'callback_data')
    list_filter = ('is_active',)

@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'category', 'status', 'created_at')
    list_filter = ('status', 'category', 'created_at')
    search_fields = ('phone_numbers', 'user__full_name', 'user__user_id', 'details')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'salary', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('title', 'company')