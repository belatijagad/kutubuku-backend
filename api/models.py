from django.db import models
from django.contrib.auth.models import AbstractUser

class Consumable(models.Model):
    name = models.TextField()
    description = models.TextField()
    price = models.IntegerField()

    total_sold = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0)
    total_reviews = models.IntegerField(default=0)

    total_favorites = models.IntegerField(default=0)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-total_sold']

class CustomUser(AbstractUser):
    money = models.IntegerField(default=0)
    experience = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    favorite_consumables = models.ManyToManyField(Consumable, blank=True)

class Review(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    consumable = models.ForeignKey(Consumable, on_delete=models.CASCADE)
    review_text = models.TextField()
    rating = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'consumable']

    def __str__(self):
        return f"Review by {self.user.username} on {self.consumable.name}"
    
