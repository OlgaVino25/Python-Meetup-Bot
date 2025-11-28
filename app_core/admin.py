from django.contrib import admin
from django.utils import timezone
import pytz
from .models import *
from django.conf import settings
from django.utils.html import format_html
import logging

logger = logging.getLogger(__name__)

from app_core.bot.services.admin_notification_service import send_mass_notification_sync
from app_core.bot.services.admin_notification_service import send_custom_notification_sync

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["first_name", "telegram_id", "role", "is_subscribed", "is_networking_active"]
    list_filter = ["role", "is_subscribed", "is_networking_active"]
    list_editable = ["role", "is_subscribed", "is_networking_active"]
    search_fields = ["first_name", "telegram_id", "company"]
    actions = ['send_custom_notification']

    def send_custom_notification(self, request, queryset):
        message_title = "Сообщение от организаторов"
        message_text = "У нас для вас важная информация! Следите за анонсами."
        
        try:
            user_ids = [user.id for user in queryset]
            success, failed, message = send_custom_notification_sync(user_ids, message_title, message_text)
            self.message_user(request, f"Сообщение отправлено. Успешно: {success}, Ошибок: {failed}")
        except Exception as e:
            self.message_user(request, f"Ошибка при отправке: {str(e)}", level='error')
    
    send_custom_notification.short_description = "Отправить сообщение выбранным пользователям"

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
    list_display = ["title", "start_date", "end_date", "get_talks_count", "notification_sent", "notification_sent_week", "notification_sent_day"]
    list_filter = ["start_date", "notification_sent", "notification_sent_week", "notification_sent_day"]
    list_editable = ["notification_sent", "notification_sent_week", "notification_sent_day"]
    inlines = [TalkInline]
    actions = ['create_event_notification', 'reset_notification_flags']
    
    def reset_notification_flags(self, request, queryset):
        """Сбросить флаги уведомлений для выбранных мероприятий"""
        updated = queryset.update(
            notification_sent=False,
            notification_sent_week=False,
            notification_sent_day=False
        )
        self.message_user(request, f"Флаги уведомлений сброшены для {updated} мероприятий")
    reset_notification_flags.short_description = "Сбросить флаги уведомлений"
    
    def get_talks_count(self, obj):
        return obj.talk_set.count()
    get_talks_count.short_description = "Докладов"
    
    def create_event_notification(self, request, queryset):
        for event in queryset:
            notification = MassNotification.objects.create(
                title=f"Напоминание: {event.title}",
                message=(
                    f"Напоминаем о предстоящем мероприятии!\n\n"
                    f"🎯 {event.title}\n"
                    f"📅 {event.start_date.strftime('%d.%m.%Y в %H:%M')}\n"
                    f"📝 {event.description[:300]}{'...' if len(event.description) > 300 else ''}\n\n"
                    f"Не пропустите интересные доклады!"
                ),
                target_users='all'
            )
            self.message_user(request, f"Создана рассылка для мероприятия '{event.title}'")
    
    create_event_notification.short_description = "Создать рассылку о выбранных мероприятиях"
    
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

@admin.register(MassNotification)
class MassNotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'target_users_display', 'status_display', 'sent_to_count', 'failed_count', 'sent_at', 'created_at']
    list_filter = ['status', 'target_users', 'created_at']
    readonly_fields = ['status', 'sent_to_count', 'failed_count', 'sent_at', 'created_at', 'stats_display']
    actions = ['send_selected_notifications']
    fieldsets = [
        ('Основная информация', {
            'fields': ['title', 'message', 'target_users', 'custom_users']
        }),
        ('Статистика', {
            'fields': ['stats_display', 'status', 'sent_to_count', 'failed_count', 'sent_at', 'created_at'],
            'classes': ['collapse']
        }),
    ]
    
    def target_users_display(self, obj):
        if obj.target_users == 'all':
            return "Все подписанные"
        else:
            count = obj.custom_users.count()
            return f"Выбранные ({count} чел.)"
    target_users_display.short_description = "Получатели"
    
    def status_display(self, obj):
        status_colors = {
            'draft': 'gray',
            'sending': 'orange', 
            'sent': 'green',
            'failed': 'red'
        }
        color = status_colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = "Статус"
    
    def stats_display(self, obj):
        if obj.sent_to_count > 0 or obj.failed_count > 0:
            return f"Успешно: {obj.sent_to_count}, Ошибок: {obj.failed_count}"
        return "Еще не отправлялась"
    stats_display.short_description = "Статистика отправки"
    
    def send_selected_notifications(self, request, queryset):
        results = []
        
        for notification in queryset:
            if notification.status in ['sending', 'sent']:
                results.append(f"Рассылка '{notification.title}' уже отправлена или отправляется")
                continue
            
            success, failed, message = send_mass_notification_sync(notification)
            results.append(f"'{notification.title}': {message}")
        
        for result in results:
            self.message_user(request, result)
    
    send_selected_notifications.short_description = "Отправить выбранные рассылки"
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('custom_users')