from rest_framework import serializers
from .models import Post, Author, StripeCustomer, StripeSubscription
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from rest_framework.authtoken.models import Token

Author = get_user_model()

class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['id', 'title', 'slug', 'body', 'author', 'publish', 'created', 'updated', 'status']

class AuthorSerializer(serializers.ModelSerializer):
        class Meta:
            model = Author
            fields = ['id','email','first_name','last_name', 'password']
            extra_kwargs = {'password':{'write_only': True}}

        def create(self, validated_data):
            user = Author.objects.create_user(email=validated_data['email'], password=validated_data['password'], first_name = validated_data.get('first_name', ''), last_name = validated_data.get('last_name', ''))
            Token.objects.create(user=user)
            return user


            """
            return Response({"message": "","data":""})
            """

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only= True)

    def validate(self, data):
        user = authenticate(email = data['email'], password = data['password'])
        if user is None:
            raise serializers.ValidationError('Invalid Credentials')
        return {'user': user}

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validated_email(self, value):
        if not Author.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user with this email address exists")
        return value

    def save(self):
        email = self.validated_data['email']
        user = Author.objects.get(email=email)
        token = default_token_generator.make_token(user)
        reset_link = f"http://localhost:8000/password_reset?token={token}&uid={user.pk}"

        send_mail(
            'Password Reset Request',
            f'Click the link below to reset password:\n{reset_link}',
            'haris.saleem@zweidevs.com',
            [email],
            fail_silently=False
        )

class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    uid = serializers.IntegerField()
    new_password = serializers.CharField()

    def validate(self, data):
        user = Author.objects.get(pk=data['uid'])
        if not default_token_generator.check_token(user, data['token']):
            raise serializers.ValidationError("Invalid token")
        return data

    def save(self):
        user = Author.objects.get(pk=self.validated_data['uid'])
        user.set_password(self.validated_data['new_password'])
        user.save()


class StripeCustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = StripeCustomer
        fields = ['user', 'stripe_customer_id', 'created_at']

class StripeSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StripeSubscription
        fields = ['customer', 'stripe_subscription_id', 'status', 'plan', 'created_at', 'current_period_end']

