from dj_rest_auth.registration.serializers import RegisterSerializer as BaseRegisterSerializer
from rest_framework import serializers

from .models import Membership, User


class UserDetailSerializer(serializers.ModelSerializer):
    """Serializer for the current user (used by dj-rest-auth /me endpoint)."""

    memberships = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "full_name", "memberships"]
        read_only_fields = ["id", "email"]

    def get_memberships(self, obj):
        return MembershipSerializer(
            obj.memberships.filter(is_active=True).select_related("tenant"),
            many=True,
        ).data


class RegisterSerializer(BaseRegisterSerializer):
    username = None  # Email-only auth, no username field
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)

    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data["first_name"] = self.validated_data.get("first_name", "")
        data["last_name"] = self.validated_data.get("last_name", "")
        return data

    def save(self, request):
        user = super().save(request)
        user.first_name = self.validated_data.get("first_name", "")
        user.last_name = self.validated_data.get("last_name", "")
        user.save()
        return user


class MembershipSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source="tenant.name", read_only=True)
    tenant_slug = serializers.CharField(source="tenant.slug", read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)
    user_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = Membership
        fields = [
            "id", "user", "user_email", "user_name", "tenant", "tenant_name",
            "tenant_slug", "role", "is_active", "created_at",
        ]
        read_only_fields = ["id", "user", "user_email", "user_name", "tenant", "tenant_name", "tenant_slug", "created_at"]


class InviteMemberSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=["admin", "member"], default="member")


class ChangeMemberRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=["owner", "admin", "member"])
