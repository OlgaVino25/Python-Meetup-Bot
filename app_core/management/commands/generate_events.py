from django.core.management.base import BaseCommand
from app_core.models import Event, Talk, User
from django.utils import timezone
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Генерация мероприятий с 28.11.2025 по 5.12.2025'

    def handle(self, *args, **options):
        self.stdout.write("Создание мероприятий на ноябрь-декабрь 2025...")
        
        event_dates = [
            "2025-11-28", "2025-11-29", "2025-11-30",
            "2025-12-01", "2025-12-02", "2025-12-03", 
            "2025-12-04", "2025-12-05"
        ]
        
        talk_themes = [
            "Асинхронный Python", "Django REST Framework", "FastAPI в продакшене",
            "Тестирование Python приложений", "ML с Scikit-learn", "Data Science на Python",
            "Web Scraping с BeautifulSoup", "Базы данных и ORM", "Docker для Python разработчиков",
            "Microservices на Python", "Celery и асинхронные задачи", "Python и DevOps",
            "Оптимизация Python кода", "Type hints и mypy", "Python для мобильной разработки"
        ]
        
        speakers = []
        speaker_names = [
            "Иван Петров", "Мария Сидорова", "Алексей Козлов", 
            "Елена Новикова", "Дмитрий Волков", "Анна Орлова",
            "Сергей Павлов", "Ольга Морозова"
        ]
        
        for i, name in enumerate(speaker_names):
            speaker, created = User.objects.get_or_create(
                telegram_id=f"speaker_{i+1}",
                defaults={
                    "first_name": name,
                    "role": "speaker",
                    "company": ["Yandex", "Tinkoff", "Ozon", "VK", "Сбер", "Mail.ru", "Avito"][i % 7],
                    "job_title": ["Team Lead", "Senior Developer", "Data Scientist", "Architect", "Tech Lead"][i % 5]
                }
            )
            speakers.append(speaker)
            if created:
                self.stdout.write(f"✅ Создан спикер: {name}")

        for i, date_str in enumerate(event_dates):
            event_date = datetime.strptime(date_str, "%Y-%m-%d")
            
            event = Event.objects.create(
                title=f"PythonMeetup Москва - {event_date.strftime('%d.%m.%Y')}",
                description=(
                    f"Ежеквартальная встреча Python-разработчиков. "
                    f"Обсуждаем актуальные темы, делимся опытом, знакомимся с коллегами. "
                    f"Тема дня: {random.choice(['Web Development', 'Data Science', 'DevOps', 'Machine Learning'])}"
                ),
                start_date=timezone.make_aware(datetime.combine(event_date, datetime.strptime("18:00", "%H:%M").time())),
                end_date=timezone.make_aware(datetime.combine(event_date, datetime.strptime("21:00", "%H:%M").time())),
                # НЕТ is_active!
            )
            
            self.stdout.write(f"✅ Создано мероприятие: {event.title}")
            
            num_talks = random.randint(3, 4)
            talk_start = event.start_date + timedelta(minutes=15)
            
            for j in range(num_talks):
                talk_duration = random.choice([30, 45, 60])
                talk_theme = random.choice(talk_themes)
                
                talk = Talk.objects.create(
                    event=event,
                    speaker=random.choice(speakers),
                    title=f"{talk_theme} - часть {j+1}",
                    start_time=talk_start,
                    end_time=talk_start + timedelta(minutes=talk_duration)
                )
                
                self.stdout.write(f"   🎤 Доклад: {talk.title} ({talk_start.strftime('%H:%M')}-{(talk_start + timedelta(minutes=talk_duration)).strftime('%H:%M')})")
                talk_start = talk.end_time + timedelta(minutes=10)
        
        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Успешно создано {len(event_dates)} мероприятий с {len(speakers)} спикерами!"
            )
        )
        
        self.stdout.write("\nСоздание тестовых пользователей...")
        for i in range(15):
            user, created = User.objects.get_or_create(
                telegram_id=f"test_user_{i+1}",
                defaults={
                    "first_name": f"Участник_{i+1}",
                    "role": "guest",
                    "company": random.choice(["Yandex", "Tinkoff", "Ozon", "VK", "Сбер", "Mail.ru", "Avito", "Lamoda"]),
                    "job_title": random.choice(["Junior Developer", "Middle Developer", "Senior Developer", "Team Lead", "Data Scientist", "QA Engineer"]),
                    "is_networking_active": random.choice([True, False])
                }
            )
            if created:
                self.stdout.write(f"✅ Создан пользователь: {user.first_name}")