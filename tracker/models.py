from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    preferred_language = models.CharField(max_length=5, default='ar')

    def __str__(self):
        return f"{self.user.username}'s Profile"


class Book(models.Model):
    STATUS_CHOICES = [
        ('want_to_read', 'أرغب بقراءته'),
        ('currently_reading', 'قيد القراءة'),
        ('completed', 'مكتمل'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='books')
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    total_pages = models.PositiveIntegerField()
    pages_read = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='want_to_read')
    rating = models.PositiveIntegerField(default=0)
    review = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def progress_percentage(self):
        if self.total_pages > 0:
            return min(100, round((self.pages_read / self.total_pages) * 100))
        return 0


class Habit(models.Model):
    DURATION_CHOICES = [
        ('month', 'لمدة شهر واحدة'),
        ('forever', 'على الدوام'),
    ]

    COLOR_CHOICES = [
        ('#159B78', 'أخضر (Teal)'),
        ('#6254C7', 'بنفسجي (Purple)'),
        ('#F4BE62', 'ذهبي (Gold)'),
        ('#123B5D', 'أزرق داكن (Navy)'),
        ('#E74C3C', 'أحمر (Red)'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='habits')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateField(default=timezone.now)
    start_time = models.TimeField(default="08:00")
    end_time = models.TimeField(default="09:00")
    duration_type = models.CharField(max_length=20, choices=DURATION_CHOICES, default='forever')
    color = models.CharField(max_length=20, choices=COLOR_CHOICES, default='#159B78')
    active = models.BooleanField(default=True)
    paused_at = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def calculate_yearly_completion_rate(self):
        today = timezone.now().date()
        start_of_year = date(today.year, 1, 1)
        actual_start = max(self.start_date, start_of_year)

        if not self.active and self.paused_at:
            if (today - self.paused_at).days >= 30:
                self.logs.all().delete()
                self.start_date = today
                self.paused_at = None
                self.save()
                return 0

        total_days = (today - actual_start).days + 1
        if total_days <= 0:
            return 0

        completed_logs = self.logs.filter(completed=True, completed_on__gte=actual_start).count()
        return min(100, round((completed_logs / total_days) * 100))


# --- هذا النموذج هو الذي كان مفقوداً أو غير محفوظ ---
class HabitLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='habit_logs')
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name='logs')
    completed_on = models.DateField(default=timezone.now)
    completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'habit', 'completed_on')

    def __str__(self):
        return f"{self.habit.name} - {self.completed_on} - {self.completed}"