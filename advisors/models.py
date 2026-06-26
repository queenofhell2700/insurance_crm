from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User


class Customer(models.Model):
    GENDER_CHOICES = [
        ("M", "Male"),
        ("F", "Female"),
        ("O", "Other"),
    ]

    full_name = models.CharField(max_length=255)
    age = models.IntegerField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    city = models.CharField(max_length=100)
    occupation = models.CharField(max_length=100)
    annual_income = models.DecimalField(max_digits=12, decimal_places=2)
    assigned_to = models.ForeignKey(
        User, on_delete=models.CASCADE
    )  # Security: only assigned user sees this
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name


class FamilyInformation(models.Model):
    RELATIONSHIP_CHOICES = [
        ("Spouse", "Spouse"),
        ("Child", "Child"),
        ("Parent", "Parent"),
        ("Sibling", "Sibling"),
        ("Other", "Other"),
    ]

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="family_members"
    )
    name = models.CharField(max_length=255)
    relationship = models.CharField(max_length=50, choices=RELATIONSHIP_CHOICES)
    age = models.IntegerField()
    existing_illness = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.relationship}) - {self.customer.full_name}"


class MedicalDisclosure(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="medical_disclosures"
    )
    disease_name = models.CharField(max_length=255)
    diagnosis_date = models.DateField()
    medication_details = models.TextField()
    hospitalization_history = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.disease_name} - {self.customer.full_name}"


class ExistingInsuranceCover(models.Model):
    POLICY_TYPE_CHOICES = [
        ("Term", "Term Insurance"),
        ("Whole Life", "Whole Life"),
        ("Endowment", "Endowment"),
        ("ULiP", "Unit Linked Insurance Plan"),
        ("Other", "Other"),
    ]

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="insurance_covers"
    )
    provider_name = models.CharField(max_length=255)
    coverage_amount = models.DecimalField(max_digits=12, decimal_places=2)
    policy_type = models.CharField(max_length=50, choices=POLICY_TYPE_CHOICES)
    claim_history = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.provider_name} - {self.customer.full_name}"
