from django.db import models
from django.contrib.auth.models import User


# =========================================================
# TRIP MODEL
# =========================================================

class Trip(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    source = models.CharField(
        max_length=100
    )

    destination = models.CharField(
        max_length=100
    )

    travel_date = models.DateField()

    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )

    # Vehicle type entered by the user
    # Example: Car, Bike, SUV, Bus
    vehicle_type = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    # Total seats in the vehicle
    total_seats = models.PositiveIntegerField(
        default=4
    )

    # Seats already occupied
    filled_seats = models.PositiveIntegerField(
        default=1
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # -----------------------------------------------------
    # Available seats
    # -----------------------------------------------------

    @property
    def available_seats(self):

        return max(
            0,
            self.total_seats - self.filled_seats
        )

    # -----------------------------------------------------
    # String representation
    # -----------------------------------------------------

    def __str__(self):

        return (
            f"{self.user.username} - "
            f"{self.source} to {self.destination} - "
            f"{self.vehicle_type or 'No Vehicle'}"
        )


# =========================================================
# TRIP REQUEST MODEL
# =========================================================

class TripRequest(models.Model):

    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
    )

    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name='requests'
    )

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_requests'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=['trip', 'sender'],
                name='unique_trip_request'
            )
        ]

    def __str__(self):

        return (
            f"{self.sender.username} -> "
            f"{self.trip.user.username} "
            f"({self.status})"
        )


# =========================================================
# EXPENSE MODEL
# =========================================================

class Expense(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name='expenses'
    )

    description = models.CharField(
        max_length=200
    )

    paid_by = models.CharField(
        max_length=100
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    number_of_people = models.PositiveIntegerField(
        default=1
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # -----------------------------------------------------
    # Calculate amount per person
    # -----------------------------------------------------

    def per_person_amount(self):

        if self.number_of_people > 0:
            return self.amount / self.number_of_people

        return 0

    def __str__(self):

        return self.description