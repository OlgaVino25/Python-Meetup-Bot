from django.contrib import admin
from .models import *


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["first_name", "telegram_id", "role"]
    list_filter = ["role",]
    list_editable = ["role",]


class TalkInline(admin.TabularInline):
    model = Talk
    extra = 1
    fields = ("title", "speaker", "start_time", "end_time")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "speaker":
            kwargs["queryset"] = User.objects.filter(role="speaker")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["title", "start_date", "end_date"]
    inlines = [TalkInline]


@admin.register(Talk)
class TalkAdmin(admin.ModelAdmin):
    list_display = ["title", "speaker", "start_time", "event"]
    list_filter = ("event", "speaker")
    search_fields = ("title", "speaker__first_name", "speaker__last_name")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "speaker":
            kwargs["queryset"] = User.objects.filter(role="speaker")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
