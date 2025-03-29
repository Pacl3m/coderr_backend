from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    """
    Erweiterung des Django AbstractUser-Modells um zusätzliche Felder.

    Attribute:
        file (FileField): Optionales Profilbild.
        location (CharField): Standort des Nutzers.
        tel (CharField): Telefonnummer des Nutzers.
        description (TextField): Beschreibung des Nutzers.
        working_hours (CharField): Arbeitszeiten des Nutzers.
        type (CharField): Nutzer-Typ (Business oder Customer).
        created_at (DateTimeField): Erstellungsdatum des Accounts.
    """
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
    """
    Repräsentiert ein Angebot eines Nutzers.

    Attribute:
        user (ForeignKey): Der Anbieter des Angebots.
        title (CharField): Titel des Angebots.
        image (FileField): Optionales Angebotsbild.
        description (TextField): Beschreibung des Angebots.
        created_at (DateTimeField): Zeitpunkt der Erstellung.
        updated_at (DateTimeField): Zeitpunkt der letzten Aktualisierung.
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    image = models.FileField(upload_to="offer_images/", null=True, blank=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class OfferDetail(models.Model):
    """
    Details zu einem Angebot, z. B. verschiedene Preismodelle.

    Attribute:
        offer (ForeignKey): Das zugehörige Angebot.
        user (ForeignKey): Der Ersteller des Angebots.
        title (CharField): Titel des Angebots.
        revisions (IntegerField): Anzahl der erlaubten Überarbeitungen.
        delivery_time_in_days (IntegerField): Lieferzeit in Tagen.
        price (DecimalField): Preis des Angebots.
        features (JSONField): Zusätzliche Features als JSON-Daten.
        offer_type (CharField): Typ des Angebots (basic, standard, premium).
    """
    offer = models.ForeignKey(
        Offer, on_delete=models.CASCADE, related_name="details", null=False, default=1
    )
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, default=1)
    title = models.CharField(max_length=255)
    revisions = models.IntegerField()
    delivery_time_in_days = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField()
    offer_type = models.CharField(
        max_length=50,
        choices=[("basic", "Basic"), ("standard", "Standard"),
                 ("premium", "Premium")],
        default="basic"
    )


class Order(models.Model):
    """
    Bestellung eines Angebots durch einen Kunden.

    Attribute:
        customer_user (ForeignKey): Der Kunde, der die Bestellung aufgibt.
        business_user (ForeignKey): Der Anbieter des Angebots.
        title (CharField): Titel der Bestellung.
        revisions (PositiveIntegerField): Anzahl erlaubter Überarbeitungen.
        delivery_time_in_days (PositiveIntegerField): Lieferzeit in Tagen.
        price (DecimalField): Preis der Bestellung.
        features (JSONField): Details zum Angebot.
        offer_type (CharField): Typ des bestellten Angebots.
        status (CharField): Status der Bestellung (z. B. in_progress, completed).
        created_at (DateTimeField): Zeitpunkt der Erstellung.
        updated_at (DateTimeField): Zeitpunkt der letzten Aktualisierung.
    """
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


class Review(models.Model):
    """
    Bewertungen für Geschäftsprofile.

    Attribute:
        business_user (ForeignKey): Das bewertete Geschäftsprofil.
        reviewer (ForeignKey): Der Benutzer, der die Bewertung abgegeben hat.
        rating (PositiveIntegerField): Bewertungswert (z. B. 1-5 Sterne).
        description (TextField): Beschreibung der Bewertung.
        created_at (DateTimeField): Zeitpunkt der Erstellung.
        updated_at (DateTimeField): Zeitpunkt der letzten Aktualisierung.
    """
    business_user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="received_reviews"
    )
    reviewer = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="written_reviews"
    )
    rating = models.PositiveIntegerField()
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class BaseInfo(models.Model):
    """
    Statistische Informationen über die Plattform.

    Attribute:
        review_count (IntegerField): Gesamtanzahl der Bewertungen.
        average_rating (IntegerField): Durchschnittliche Bewertung.
        business_profile_count (IntegerField): Anzahl der Business-Profile.
        offer_count (IntegerField): Gesamtanzahl der Angebote.
    """
    review_count = models.IntegerField()
    average_rating = models.IntegerField()
    business_profile_count = models.IntegerField()
    offer_count = models.IntegerField()
