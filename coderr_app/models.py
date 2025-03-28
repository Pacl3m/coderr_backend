from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    file = models.FileField(
        upload_to="profile_pictures/", blank=True, null=True)
    location = models.CharField(max_length=100, blank=True)
    tel = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    working_hours = models.CharField(max_length=50, blank=True)
    type = models.CharField(max_length=50, choices=[(
        "business", "Business"), ("customer", "Customer")])
    created_at = models.DateTimeField(auto_now_add=True)


class Offer(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    image = models.FileField(upload_to="offer_images/", null=True, blank=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class OfferDetail(models.Model):
    offer = models.ForeignKey(
        Offer, on_delete=models.CASCADE, related_name="details", null=False, default=1
    )
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, default=1)
    title = models.CharField(max_length=255)
    revisions = models.IntegerField()
    delivery_time_in_days = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField()  # Liste von Features
    offer_type = models.CharField(
        max_length=50,
        choices=[("basic", "Basic"), ("standard", "Standard"),
                 ("premium", "Premium")],
        default="basic"
    )

    def __str__(self):
        return f"{self.offer.title} - {self.title}"


class Order(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'In Bearbeitung'),
        ('completed', 'Abgeschlossen'),
        ('cancelled', 'Abgebrochen'),
    ]

    customer_user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='customer_offers', null=True, blank=True)
    business_user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='business_offers', null=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    revisions = models.PositiveIntegerField(null=True, blank=True)
    delivery_time_in_days = models.PositiveIntegerField(null=True, blank=True)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    features = models.JSONField(null=True, blank=True)
    offer_type = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='in_progress', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.status}"


class Review(models.Model):
    business_user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="received_reviews"
    )
    reviewer = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="written_reviews"
    )
    rating = models.PositiveIntegerField()  # Annahme: 1 bis 5 Sterne
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class BaseInfo(models.Model):
    review_count = models.IntegerField()
    average_rating = models.IntegerField()
    business_profile_count = models.IntegerField()
    offer_count = models.IntegerField()
