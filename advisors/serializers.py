from rest_framework import serializers
from django.contrib.auth.models import User
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