from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Customer, User, AIRequestLog, AIOutputVersion  # ADD AIOutputVersion
from .models import UserProfile
#import customer model
from .models import Customer

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        UserProfile.objects.create(user=user)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


#added serializer for customer context
class CustomerContextSerializer(serializers.ModelSerializer):
    ped = serializers.SerializerMethodField()
    existing_cover = serializers.SerializerMethodField()
    family_members_count = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = ['id', 'full_name', 'age', 'city', 'family_members_count', 'ped', 'existing_cover']

    def get_ped(self, obj):
        return list(obj.medical_disclosures.values_list('disease_name', flat=True))

    def get_existing_cover(self, obj):
        cover = obj.insurance_covers.first()
        return float(cover.coverage_amount) if cover else 0

    def get_family_members_count(self, obj):
        return obj.family_members.count()
    
    
# Module 7 - AI Logging Serializer
from .models import AIRequestLog  # make sure this import is at the top

# Customer Serializer for create/update
class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            'id', 'full_name', 'age', 'city',
            'family_members', 'medical_disclosures', 'insurance_covers'
        ]

class AIRequestLogSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = AIRequestLog
        fields = [
            'id', 'customer', 'customer_name', 'user', 'user_name',
            'log_type', 'prompt_text', 'response_text', 'model_name',
            'status', 'error_message', 'tokens_used', 'response_time',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# Module 8 - AI Output Versioning Serializer
class AIOutputVersionSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    
    class Meta:
        model = AIOutputVersion
        fields = [
            'id',
            'customer',
            'customer_name',
            'output_type',
            'version_number',
            'response_json',
            'model_used',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']