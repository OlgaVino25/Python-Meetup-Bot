# management/commands/generate_networking_profiles.py
from django.core.management.base import BaseCommand
from app_core.models import User, NetworkingProfile
import random

class Command(BaseCommand):
    help = 'Генерация тестовых анкет для знакомств'

    def handle(self, *args, **options):
        # Создаем тестовые анкеты для существующих пользователей
        users = User.objects.all()[:10]  # Берем первых 10 пользователей
        
        interests_list = [
            "Python, Django, веб-разработка, стартапы",
            "Машинное обучение, Data Science, нейросети",
            "Базы данных, оптимизация, высокие нагрузки",
            "DevOps, Docker, Kubernetes, облачные технологии", 
            "Мобильная разработка, кроссплатформенные приложения",
            "Тестирование, QA, автоматизация тестов",
            "Архитектура, микросервисы, проектирование систем",
            "Карьера в IT, менторство, развитие команд",
            "Open source, сообщество, контрибьюция",
            "Предпринимательство, продуктовый менеджмент"
        ]
        
        companies = ["Yandex", "Tinkoff", "Ozon", "VK", "Сбер", "Mail.ru", "Avito", "Lamoda"]
        job_titles = ["Junior Developer", "Middle Developer", "Senior Developer", "Team Lead", "Architect"]
        
        for i, user in enumerate(users):
            profile, created = NetworkingProfile.objects.get_or_create(
                user=user,
                defaults={
                    'name': user.first_name,
                    'company': random.choice(companies),
                    'job_title': random.choice(job_titles),
                    'interests': interests_list[i % len(interests_list)],
                    'contact_consent': random.choice([True, False]),
                    'is_visible': True
                }
            )
            
            if created:
                self.stdout.write(f"✅ Создана анкета для {user.first_name}")