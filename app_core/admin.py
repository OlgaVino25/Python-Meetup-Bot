from django.contrib import admin
from django.utils import timezone
import pytz
from .models import *

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["first_name", "telegram_id", "role", "is_subscribed", "is_networking_active"]
    list_filter = ["role", "is_subscribed", "is_networking_active"]
    list_editable = ["role", "is_subscribed", "is_networking_active"]
    search_fields = ["first_name", "telegram_id", "company"]

class TalkInline(admin.TabularInline):
    model = Talk
    extra = 1
    fields = ("title", "speaker", "start_time", "end_time", "is_active")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "speaker":
            kwargs["queryset"] = User.objects.filter(role="speaker")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["title", "start_date", "end_date", "get_talks_count"]  # Исправлено на get_talks_count
    list_filter = ["start_date"]
    inlines = [TalkInline]
    
    def get_talks_count(self, obj):
        return obj.talk_set.count()
    get_talks_count.short_description = "Докладов"
    
    def save_model(self, request, obj, form, change):
        moscow_tz = pytz.timezone('Europe/Moscow')
        if obj.start_date and obj.start_date.tzinfo is None:
            obj.start_date = moscow_tz.localize(obj.start_date)
        if obj.end_date and obj.end_date.tzinfo is None:
            obj.end_date = moscow_tz.localize(obj.end_date)
        super().save_model(request, obj, form, change)

@admin.register(Talk)
class TalkAdmin(admin.ModelAdmin):
    list_display = ["title", "speaker", "start_time", "event", "is_active"]
    list_editable = ["is_active"]
    list_filter = ("event", "speaker", "is_active")
    search_fields = ("title", "speaker__first_name", "speaker__last_name")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "speaker":
            kwargs["queryset"] = User.objects.filter(role="speaker")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def save_model(self, request, obj, form, change):
        moscow_tz = pytz.timezone('Europe/Moscow')
        if obj.start_time and obj.start_time.tzinfo is None:
            obj.start_time = moscow_tz.localize(obj.start_time)
        if obj.end_time and obj.end_time.tzinfo is None:
            obj.end_time = moscow_tz.localize(obj.end_time)
        super().save_model(request, obj, form, change)

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["talk", "from_user", "text_preview", "is_answered", "created_at"]
    list_filter = ["is_answered", "talk", "created_at"]
    list_editable = ["is_answered"]
    
    def text_preview(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text
    text_preview.short_description = "Вопрос"

@admin.register(NetworkingMatch)
class NetworkingMatchAdmin(admin.ModelAdmin):
    list_display = ["user1", "user2", "status", "created_at"]
    list_filter = ["status", "created_at"]
    list_editable = ["status"]

@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ["from_user", "event", "amount", "created_at"]
    list_filter = ["event", "created_at"]

@admin.register(Broadcast)
class BroadcastAdmin(admin.ModelAdmin):
    list_display = ["event", "sent_by", "sent_at"]
    list_filter = ["event", "sent_at"]

@admin.register(SpeakerApplication)
class SpeakerApplicationAdmin(admin.ModelAdmin):
    list_display = ["topic", "user", "duration", "status", "created_at"]
    list_filter = ["status", "created_at"]
    list_editable = ["status"]
    search_fields = ["topic", "user__first_name", "user__last_name", "user__username"]
    readonly_fields = ["created_at"]
    fieldsets = [
        ("Основная информация", {
            "fields": ["user", "topic", "description", "duration"]
        }),
        ("Статус заявки", {
            "fields": ["status", "notes", "created_at"]
        }),
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")