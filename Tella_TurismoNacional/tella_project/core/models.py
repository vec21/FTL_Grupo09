from django.db import models
from django.contrib.auth.models import User

class Trip(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trips')
    name = models.CharField(max_length=150)
    start_date = models.DateField()
    end_date = models.DateField()
    travelers = models.PositiveIntegerField(default=1)
    budget_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.user.username})"

    @property
    def duration_days(self):
        return (self.end_date - self.start_date).days + 1

    def budget_per_day(self):
        if self.budget_total and self.duration_days > 0:
            return self.budget_total / self.duration_days
        return None

class TripDay(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='days')
    date = models.DateField()
    order = models.PositiveIntegerField(help_text="Ordem do dia dentro da viagem")
    activities = models.TextField(blank=True)
    lodging = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['order']
        unique_together = ('trip', 'order')

    def __str__(self):
        return f"Dia {self.order} - {self.trip.name}"