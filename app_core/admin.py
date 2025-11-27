from django.contrib import admin
from .models import *


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["first_name", "telegram_id", "role", "company"]
    list_filter = ["role", "is_networking_active"]
    list_editable = ["role",]


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["title", "date", "location", "is_active"]


@admin.register(Talk)
class TalkAdmin(admin.ModelAdmin):
    list_display = ["title", "speaker", "start_time", "event"]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["from_user", "talk", "is_answered", "created_at"]


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ["from_user", "amount", "event", "created_at"]


@admin.register(NetworkingMatch)
class NetworkingMatchAdmin(admin.ModelAdmin):
    list_display = ["user1", "user2", "status", "created_at"]


@admin.register(Broadcast)
class BroadcastAdmin(admin.ModelAdmin):
    list_display = ["event", "sent_by", "sent_at"]


@admin.register(UserEvent)
class UserEventAdmin(admin.ModelAdmin):
    list_display = ["user", "event", "registered_at"]
