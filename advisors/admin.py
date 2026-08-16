# Register your models here.
from rest_framework.permissions import IsAdminUser
from django.contrib import admin
from .models import (
    Customer,
    FamilyInformation,
    MedicalDisclosure,
    ExistingInsuranceCover,
)

#added
from .models import Policy
@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = ['policy_number', 'customer', 'policy_type', 'status', 'premium', 'coverage_amount']
    list_filter = ['status', 'policy_type', 'created_at']
    search_fields = ['policy_number', 'customer__full_name']
    readonly_fields = ['created_at', 'updated_at', 'proposal_date']

admin.site.register(Customer)
admin.site.register(FamilyInformation)
admin.site.register(MedicalDisclosure)
admin.site.register(ExistingInsuranceCover)