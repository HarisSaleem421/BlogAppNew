from .models import Post, Author, StripeCustomer, StripeSubscription
from .serializers import *
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail 
from django.conf import settings
from django.contrib.auth import logout as author_logout , authenticate
import os 
from django.core.mail import send_mail
import stripe

@api_view(['GET'])
@permission_classes([AllowAny])
def post_list_get(request):
    posts = Post.published.all()
    serializers = PostSerializer(posts, many = True)
    return Response(serializers.data)

@api_view(['POST'])
def new_post(request):
    if request.user.id != post.author.id:
            return Response({"message": "You do not have permission to post by this Author."}, status=status.HTTP_403_FORBIDDEN)
    serializer = PostSerializer(data= request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET','PATCH','DELETE'])
def post_get(request, id):
    try:
        post = Post.published.get(pk = id)
    except Post.DoesNotExist:
        return Response(status= status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = PostSerializer(post)
        return Response(serializer.data)
    elif request.method == 'PATCH':
        if request.user.id != post.author.id:
            return Response({"message": "You do not have permission to edit this post."}, status=status.HTTP_403_FORBIDDEN)
        serializer = PostSerializer(post, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        if request.user.id != post.author.id:
            return Response({"message": "You do not have permission to delete this post."}, status=status.HTTP_403_FORBIDDEN)
        serializer = PostSerializer(post)
        data = serializer.data
        post.delete()
        return Response(data, status=status.HTTP_204_NO_CONTENT)
    
    
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    serializer = AuthorSerializer(data = request.data)
    if serializer.is_valid():
        user = serializer.save()
        try:
            send_mail('BlogApp Registration', 'You are registered to BlogApp.\nThank you for registering!', 'haris.saleem@zweidevs.com', [user.email], fail_silently=False)
        except Exception as e:
            return Response ({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"message": "User Registered Successfully"}, status = status.HTTP_201_CREATED)
    return Response({"message": "User Creation Failed", "errors" : serializer.errors}, status= status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def author_posts(request, author_id):
    author = get_object_or_404(Author , pk = author_id)
    posts = Post.objects.filter(author = author)
    serializer = PostSerializer(posts, many = True)
    return Response(serializer.data, status= status.HTTP_200_OK)

@api_view(['GET'])
def all_users(request):
    authors = Author.objects.all()
    serializer = AuthorSerializer(authors, many= True)
    return Response(serializer.data, status= status.HTTP_200_OK)

@api_view(['GET'])
def loggedin_user(request):
    user = request.user
    if not user:
        return Response({"message" : "No User is Logged in"})
    serializer = AuthorSerializer(user)
    return Response(serializer.data, status= status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    serializer = PasswordResetRequestSerializer(data = request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message" : "Password Reset Email Sent Successfully"}, status= status.HTTP_200_OK)
    return Response(serializer.error, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    serializer = PasswordResetConfirmSerializer(data = request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message" : "Password has been Reset Sussessfully"}, status= status.HTTP_200_OK)
    return Response(serializer.errors, status= status.HTTP_400_BAD_REQUEST)

# @api_view(['POST'])
# def logout_user(request):
#     try:
#         refresh_token = request.data.get("refresh")
#         if refresh_token:
#             token = RefreshToken(refresh_token)
#             # token.delete()
#             token.blacklist()
#         author_logout(request)

#         return Response({"message" : "Logged Out Successfully"}, status=status.HTTP_200_OK)
#     except Exception as e:
#         return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST) 

# @api_view(['POST'])  
# def logout_user(request, format=None):
#     print('token>>>>>>>>>>>>>>>>...', request.user.token.refresh_token['access_token'])
#     request.user.auth_token.delete()
#     return Response({"message" : "Logged Out Successfully"}, status=status.HTTP_200_OK)

# @api_view(['POST'])  
# def logout_user(request):
#     try:
#         refresh_token = request.data["refresh_token"]
#         print("got refresh_token")
#         if not refresh_token:
#             return Response({"error": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)
#         print("got refresh_token")
#         token = RefreshToken(refresh_token)
#         token.blacklist()

#         return Response({"message" : "Logged Out Successfully"},status=status.HTTP_205_RESET_CONTENT)
#     except Exception as e:
#         return Response({"exception error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# class LogoutView(APIView):
#     permission_classes = (IsAuthenticated,)

#     def post(self, request):
#         try:
#             print("in try block")
#             refresh_token = request.data["refresh_token"]
#             print("after getting refresh token")
#             token = RefreshToken(refresh_token)
#             token.blacklist()

#             return Response(status=status.HTTP_205_RESET_CONTENT)
#         except Exception as e:
#             return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def register_customer(request):
    user = request.user
    if StripeCustomer.objects.filter(user=user).exists():
        return Response({"error" : "Customer already exists"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        stripe_customer = stripe.Customer.create(
            email = user.email,
            name = f"{user.first_name} {user.last_name}"
        )

        customer = StripeCustomer.objects.create(
            user = user,
            stripe_customer_id = stripe_customer.id
        )

        serializer = StripeCustomerSerializer(customer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except stripe.error.StripeError as e:
        return Response({"error" : str(e)}, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
def create_subscription(request):
    user = request.user
    customer = get_object_or_404(StripeCustomer, user = user)
    payment_method_id = request.data.get("payment_method_id")

    try:

        if payment_method_id:
            stripe.PaymentMethod.attach(
                payment_method_id,
                customer = customer.stripe_customer_id
            )    
            stripe.Customer.modify(
                customer.stripe_customer_id,
                invoice_settings = {'default_payment_method' : payment_method_id}
            )
            print("modify done")

        subscription = stripe.Subscription.create(
            customer = customer.stripe_customer_id,
            items = [{"plan" : request.data.get("plan_id")}]
        )
        subscription_data = {
            "customer" : customer.id,
            "stripe_subscription_id" : subscription.id,
            "status" : subscription.status,
            "plan" : request.data.get("plan_id"),
            "current_period_end" : subscription.current_period_end
        }

        serializer = StripeSubscriptionSerializer(data = subscription_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except stripe.error.StripeError as e:
        return Response({"error" : str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def create_payment_method(request):
    try:
        test_token = "tok_visa" 
        payment_method = stripe.PaymentMethod.create(
            type="card",
            card={"token": test_token},
        )
        
        return Response({
            'payment_method_id': payment_method.id,
            'status': 'success'
        })
    
    except stripe.error.StripeError as e:
        return Response({
            'error': str(e),
            'status': 'failed'
        }, status=400)
