from django.db import models


class User(models.Model):
    ROLE_CHOICES = [
        ("guest", "Гость"),
        ("speaker", "Спикер"),
        ("organizer", "Организатор"),
    ]

    telegram_id = models.CharField(max_length=100, unique=True)
    username = models.CharField(max_length=100, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="guest")
    phone = models.CharField(max_length=20, blank=True)
    company = models.CharField(max_length=100, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    is_networking_active = models.BooleanField(default=False)
    is_subscribed = models.BooleanField(default=False, verbose_name="Подписка на уведомления")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return f"{self.first_name} ({self.telegram_id})"


class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Мероприятие"
        verbose_name_plural = "Мероприятия"

    def __str__(self):
        return self.title

class Talk(models.Model):
    speaker = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=False, verbose_name="Активный доклад")

    class Meta:
        verbose_name = "Доклад"
        verbose_name_plural = "Доклады"
        ordering = ["start_time"]

    def __str__(self):
        return f"{self.title} by {self.speaker.first_name}"


class Question(models.Model):
    talk = models.ForeignKey(Talk, on_delete=models.CASCADE, related_name="questions")
    from_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="asked_questions"
    )
    text = models.TextField()
    is_answered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"
        ordering = ["created_at"]

    def __str__(self):
        return f"Вопрос от {self.from_user.first_name}"


class Donation(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="donations")
    from_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="donations"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Донат"
        verbose_name_plural = "Донаты"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Донат {self.amount} от {self.from_user.first_name}"


class NetworkingMatch(models.Model):
    STATUS_CHOICES = [
        ("pending", "Ожидает"),
        ("accepted", "Принято"),
        ("rejected", "Отклонено"),
    ]

    user1 = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="initiated_matches"
    )
    user2 = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="received_matches"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Знакомство"
        verbose_name_plural = "Знакомства"
        unique_together = ["user1", "user2"]

    def __str__(self):
        return f"{self.user1.first_name} ↔ {self.user2.first_name}"


class Broadcast(models.Model):
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="broadcasts"
    )
    message = models.TextField()
    sent_by = models.ForeignKey(User, on_delete=models.CASCADE)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        ordering = ["-sent_at"]

    def __str__(self):
        return f"Рассылка от {self.sent_at}"


class SpeakerApplication(models.Model):
    STATUS_CHOICES = [
        ("pending", "На рассмотрении"),
        ("approved", "Одобрена"), 
        ("rejected", "Отклонена"),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="speaker_applications")
    topic = models.CharField(max_length=200, verbose_name="Тема доклада")
    description = models.TextField(verbose_name="Описание доклада")
    duration = models.PositiveIntegerField(
        verbose_name="Продолжительность (мин)", 
        help_text="Рекомендуется 15-45 минут"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default="pending"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, verbose_name="Заметки организатора")
    
    class Meta:
        verbose_name = "Заявка спикера"
        verbose_name_plural = "Заявки спикеров"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.topic} - {self.user.first_name} ({self.get_status_display()})"