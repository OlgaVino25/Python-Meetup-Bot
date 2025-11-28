from asgiref.sync import sync_to_async
from app_core.models import Event, Talk
from django.utils import timezone
from datetime import timedelta

@sync_to_async
def get_todays_tomorrows_program():
    try:
        now = timezone.now()
        today = now.date()
        tomorrow = today + timedelta(days=1)
        
        events = Event.objects.filter(
            start_date__date__in=[today, tomorrow]
        ).order_by('start_date')
        
        if not events:
            return "📅 На сегодня и завтра мероприятий нет\n\nСледите за анонсами будущих митапов!"

        program_text = "🎪 Ближайшие митапы\n\n"
        
        for event in events:
            event_date = event.start_date.date()
            
            if event_date == today:
                date_label = "🟢 СЕГОДНЯ"
            else:
                date_label = "🟡 ЗАВТРА"
                
            program_text += f"{date_label} - {event.start_date.strftime('%d.%m.%Y')}\n"
            program_text += f"🎯 {event.title}\n"
            program_text += f"🕐 {event.start_date.strftime('%H:%M')} - {event.end_date.strftime('%H:%M')}\n"
            
            talks = Talk.objects.filter(event=event).order_by('start_time')
            
            if talks:
                program_text += "\n🎤 Доклады:\n"
                for i, talk in enumerate(talks, 1):
                    status = "🔴 " if talk.is_active else ""
                    program_text += (
                        f"{i}. {status}{talk.start_time.strftime('%H:%M')}-{talk.end_time.strftime('%H:%M')}\n"
                        f"   👨‍💻 {talk.speaker.first_name}\n"
                        f"   📝 {talk.title}\n\n"
                    )
            else:
                program_text += "\n   📝 Доклады пока не добавлены\n\n"
            
            program_text += "─" * 40 + "\n\n"
        
        program_text += "\n💡 Активный доклад отмечен красным кружком 🔴"
        return program_text
        
    except Exception as e:
        return f"❌ Ошибка при получении программы: {str(e)}"

@sync_to_async
def get_week_events_for_subscription():
    try:
        now = timezone.now()
        week_later = now + timedelta(days=7)
        
        events = Event.objects.filter(
            start_date__date__range=[now.date(), week_later.date()]
        ).order_by('start_date')
        
        if not events:
            return "📅 На ближайшую неделю мероприятий нет\n\nСледите за анонсами!"

        subscription_text = "🎪 Митапы на ближайшую неделю\n\n"
        
        for event in events:
            days_until = (event.start_date.date() - now.date()).days
            
            if days_until == 0:
                when = "🟢 СЕГОДНЯ"
            elif days_until == 1:
                when = "🟡 ЗАВТРА" 
            elif days_until <= 3:
                when = f"🔵 Через {days_until} дн."
            else:
                when = f"📅 Через {days_until} дн."
                
            subscription_text += f"{when}\n"
            subscription_text += f"📅 {event.start_date.strftime('%d.%m.%Y')}\n"
            subscription_text += f"🎯 {event.title}\n"
            subscription_text += f"🕐 {event.start_date.strftime('%H:%M')} - {event.end_date.strftime('%H:%M')}\n"
            
            talks = Talk.objects.filter(event=event).order_by('start_time')[:3]
            if talks:
                subscription_text += "🎤 Доклады:\n"
                for i, talk in enumerate(talks, 1):
                    subscription_text += f"   {i}. {talk.speaker.first_name}: {talk.title}\n"
                
                remaining = Talk.objects.filter(event=event).count() - 3
                if remaining > 0:
                    subscription_text += f"   ... и ещё {remaining} докладов\n"
            else:
                subscription_text += "🎤 Доклады пока не добавлены\n"
            
            subscription_text += "\n" + "─" * 40 + "\n\n"
        
        return subscription_text
        
    except Exception as e:
        return f"❌ Ошибка при получении программы: {str(e)}"


@sync_to_async
def get_current_talk():
    now = timezone.now()
    
    active_talk = Talk.objects.filter(is_active=True).first()
    if active_talk:
        return active_talk
    
    return Talk.objects.filter(
        start_time__lte=now,
        end_time__gte=now
    ).first()

@sync_to_async
def get_upcoming_events_for_notification():
    now = timezone.now()
    week_later = now + timedelta(days=7)
    
    return list(Event.objects.filter(
        start_date__date=week_later.date()
    ))