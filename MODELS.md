# Модели данных

### Модели:

1. User - профили пользователей
2. Event - мероприятия
3. Talk - доклады
4. Question - вопросы спикерам
5. Donation - донаты
6. NetworkingMatch - знакомства
7. Broadcast - рассылки
8. UserEvent - участие в мероприятиях

## Детали моделей

1. User (Пользователь)

```python
class User(models.Model):
    ROLE_CHOICES = [
        ('guest', 'Гость'),
        ('speaker', 'Спикер'),
        ('organizer', 'Организатор'),
    ]

    telegram_id = models.CharField(max_length=100, unique=True)
    username = models.CharField(max_length=100, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='guest')
    phone = models.CharField(max_length=20, blank=True)
    company = models.CharField(max_length=100, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    is_networking_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} ({self.telegram_id})"
```

Назначение: Хранение всех пользователей бота (гости, спикеры, организаторы)

2. Event (Мероприятие)

```python
class Event(models.Model):
    title = models.CharField(max_length=200)
    date = models.DateField()
    location = models.CharField(max_length=200)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_events')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.date}"
```

Назначение: Информация о каждом мероприятии

3. Talk (Доклад)

```python
class Talk(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='talks')
    speaker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='talks')
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'start_time']

    def __str__(self):
        return f"{self.title} - {self.speaker.first_name}"
```

Назначение: Расписание докладов внутри мероприятия

4. Question (Вопрос)

```python
class Question(models.Model):
    talk = models.ForeignKey(Talk, on_delete=models.CASCADE, related_name='questions')
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='asked_questions')
    text = models.TextField()
    is_answered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Вопрос от {self.from_user.first_name}"
```

Назначение: Вопросы от гостей к спикерам

5. Donation (Донат)

```python
class Donation(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='donations')
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='donations')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Донат {self.amount} от {self.from_user.first_name}"
```

Назначение: История донатов на мероприятия

6. NetworkingMatch (Знакомство)

```python
class NetworkingMatch(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('accepted', 'Принято'),
        ('rejected', 'Отклонено'),
    ]

    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='initiated_matches')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_matches')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user1', 'user2']

    def __str__(self):
        return f"{self.user1.first_name} ↔ {self.user2.first_name}"
```

Назначение: Сопоставления пользователей для нетворкинга

7. Broadcast (Рассылка)

```python
class Broadcast(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='broadcasts')
    message = models.TextField()
    sent_by = models.ForeignKey(User, on_delete=models.CASCADE)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"Рассылка от {self.sent_at}"
```

Назначение: История массовых уведомлений от организаторов

8. UserEvent (Участие пользователя в мероприятии)

```python
class UserEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attended_events')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='participants')
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'event']

    def __str__(self):
        return f"{self.user.first_name} на {self.event.title}"
```

Назначение: Связь пользователей с мероприятиями (кто на каком мероприятии)

## Ключевые связи:

User - Event (через UserEvent) - кто на каком мероприятии
User - Talk - кто спикер в каком докладе
Talk - Question - вопросы к конкретному докладу
User - Question - кто задал вопрос
User - NetworkingMatch - кто с кем знакомится
Event - Donation - донаты на конкретное мероприятие
Event - Broadcast - рассылки по мероприятию
