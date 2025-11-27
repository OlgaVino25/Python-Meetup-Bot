from asgiref.sync import sync_to_async
from app_core.models import Event, Talk
from django.utils import timezone

@sync_to_async
def get_current_event_program():
    """Получить программу текущего мероприятия"""
    try:
        event = Event.objects.filter(is_active=True).latest('date')
        talks = Talk.objects.filter(event=event).order_by('start_time')
        
        if not talks:
            return "Программа мероприятия пока не доступна"
        
        program_text = f"📅 Программа: {event.title}\n\n"
        for talk in talks:
            program_text += (
                f"🕐 {talk.start_time.strftime('%H:%M')} - {talk.end_time.strftime('%H:%M')}\n"
                f"🎤 {talk.speaker.first_name}: {talk.title}\n\n"
            )
        
        return program_text
    except Event.DoesNotExist:
        return "Активных мероприятий нет"