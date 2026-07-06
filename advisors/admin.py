# Register your models here.
from rest_framework.permissions import IsAdminUser
from django.contrib import admin
from .models import (
    Customer,
    FamilyInformation,
    MedicalDisclosure,
    ExistingInsuranceCover,
)

admin.site.register(Customer)
admin.site.register(FamilyInformation)
admin.site.register(MedicalDisclosure)
admin.site.register(ExistingInsuranceCover)