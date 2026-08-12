from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import User  # NEW - Module 7


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # ADD THIS LINE
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - Profile"


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
    annual_income = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    #new fields added for the customer model
    #decimal field is a field to hold decimal numbers for the money
    premium_budget = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    preferred_hospitals = models.TextField(blank=True, null=True)

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
    
    #added
    policy_number = models.CharField(max_length=50, unique=True, null=True, blank=True) 
    def __str__(self):
        return f"{self.provider_name} - {self.customer.full_name}"

# MODULE 5: QUALIFICATION INSIGHTS
class QualificationInsight(models.Model):
    RISK_BAND_CHOICES = [
        ("Low", "Low Risk"),
        ("Moderate", "Moderate Risk"),
        ("High", "High Risk"),
    ]
    
    #Links QualificationInsight to a Customer (one customer can have many insights)
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="qualification_insights"
    )
    risk_band = models.CharField(max_length=20, choices=RISK_BAND_CHOICES)
    confidence = models.FloatField()
    insights = models.JSONField()
    triggered_rules = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.customer.full_name} - {self.risk_band}"
    
# MODULE 7: AI Logging
class AIRequestLog(models.Model):
    LOG_TYPES = [
        ("chat", "Chat"),
        ("question_suggestion", "Question Suggestion"),
        ("qualification_insight", "Qualification Insight"),
    ]

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="ai_logs"
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    log_type = models.CharField(max_length=50, choices=LOG_TYPES)
    prompt_text = models.TextField()
    response_text = models.TextField(blank=True)
    model_name = models.CharField(max_length=100, default="gemini-flash-latest")
    status = models.CharField(max_length=20, default="success")
    error_message = models.TextField(blank=True, null=True)
    tokens_used = models.IntegerField(blank=True, null=True)
    response_time = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)



    def __str__(self):
        return f"{self.customer.full_name} - {self.log_type} ({self.status})"


# Module 8 - AI Output Versioning
class AIOutputVersion(models.Model):
    OUTPUT_TYPES = [
        ('question_suggestion', 'Question Suggestion'),
        ('missing_info', 'Missing Information'),
        ('qualification', 'Qualification Insights'),
        ('chat', 'AI Chat'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='ai_output_versions')
    output_type = models.CharField(max_length=50, choices=OUTPUT_TYPES)
    version_number = models.IntegerField(default=1)
    response_json = models.JSONField()
    model_used = models.CharField(max_length=100, default='gemini-pro')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['customer', 'output_type', 'version_number']
    
    def __str__(self):
        return f"{self.output_type} v{self.version_number} - {self.customer.full_name}"


#added
# ADD THIS TO YOUR models.py (at the end, after AIOutputVersion)

class Policy(models.Model):
    """
    Model for policies created/sold by agents to customers.
    Different from ExistingInsuranceCover (which are customer's existing policies).
    """
    POLICY_TYPE_CHOICES = [
        ("Life", "Life Insurance"),
        ("Health", "Health Insurance"),
        ("Auto", "Auto Insurance"),
        ("Home", "Home Insurance"),
        ("Travel", "Travel Insurance"),
        ("Other", "Other"),
    ]
    
    STATUS_CHOICES = [
        ("Draft", "Draft"),
        ("Quoted", "Quoted"),
        ("Proposed", "Proposed"),
        ("Active", "Active"),
        ("Lapsed", "Lapsed"),
        ("Declined", "Declined"),
    ]

    # Core fields
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="policies"
    )
    agent = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_policies"
    )  # Agent who created this policy
    
    # Policy details
    policy_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    policy_type = models.CharField(max_length=20, choices=POLICY_TYPE_CHOICES)
    description = models.TextField(blank=True, null=True)
    
    # Financial details
    premium = models.DecimalField(max_digits=12, decimal_places=2)
    coverage_amount = models.DecimalField(max_digits=12, decimal_places=2)
    term_years = models.IntegerField(default=20)
    
    # Dates
    proposal_date = models.DateField(auto_now_add=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Draft")
    notes = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['agent', '-created_at']),
            models.Index(fields=['customer', '-created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.customer.full_name} - {self.policy_type} ({self.status})"