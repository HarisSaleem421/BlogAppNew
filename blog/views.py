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
import os 
from django.core.mail import send_mail
import stripe
from datetime import datetime

@api_view(['GET'])
@permission_classes([AllowAny])
def post_list_get(request):
    posts = Post.published.all()
    serializers = PostSerializer(posts, many = True)
    return Response(serializers.data)

@api_view(['POST'])
def new_post(request):
    serializer = PostSerializer(data=request.data)
    if serializer.is_valid():
        if request.user.id != serializer.validated_data['author'].id:
            return Response({"message": "You do not have permission to post by this Author."}, 
                            status=status.HTTP_403_FORBIDDEN)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
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

        subscription = stripe.Subscription.create(
            customer = customer.stripe_customer_id,
            items = [{"plan" : request.data.get("plan_id")}]
        )

        current_period_end = datetime.fromtimestamp(subscription.current_period_end)
        
        subscription_data = {
            "customer" : customer.id,
            "stripe_subscription_id" : subscription.id,
            "status" : subscription.status,
            "plan" : request.data.get("plan_id"),
            "current_period_end" : current_period_end
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
def update_subscription(request):
    user = request.user
    customer = get_object_or_404(StripeCustomer, user = user)
    subscription_id = request.data.get("subscription_id")
    plan_id = request.data.get("plan_id")
    payment_method_id = request.data.get("payment_method_id")

    try:
        subscription = stripe.Subscription.retrieve(subscription_id)

        if payment_method_id:
            stripe.PaymentMethod.attach(
                payment_method_id, 
                customer = customer.stripe_customer_id
            )
            stripe.Customer.modify(
                customer.stripe_customer_id,
                invoice_settings = {'default_payment_method' : payment_method_id}
            )
        if plan_id:
            if 'items' in subscription and 'data' in subscription['items']:
                subscription_item_id = subscription['items']['data'][0].id
                stripe.Subscription.modify(
                    subscription_id,
                    items=[{
                        'id': subscription_item_id,
                        'plan': plan_id
                    }]
                )
            else:
                return Response({"error": "Subscription items not found."}, status=status.HTTP_400_BAD_REQUEST)

            updated_subscription = stripe.Subscription.retrieve(subscription_id)
            current_period_end = datetime.fromtimestamp(updated_subscription.current_period_end)

            subscription_instance = get_object_or_404(StripeSubscription, stripe_subscription_id = subscription_id)
            subscription_instance.status = updated_subscription.status
            subscription_instance.plan = plan_id if plan_id else subscription_instance.plan
            subscription_instance.current_period_end = current_period_end
            subscription_instance.save()

            serializer = StripeSubscriptionSerializer(subscription_instance)

            return Response(serializer.data, status= status.HTTP_200_OK)

    except stripe.error.StripeError as e:
        return Response({"error" : str(e)}, status = status.HTTP_400_BAD_REQUEST)
    except StripeSubscription.DoesNotExist:
        return Response({"error" : "Subscription Not Found"}, status = status.HTTP_404_NOT_FOUND)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def retrieve_subscription(request, subscription_id):
    try:
        stripe_subscription = stripe.Subscription.retrieve(subscription_id)

        plan_id = stripe_subscription.plan.id if stripe_subscription.plan else None

        if plan_id == "price_1PlV7fE8m3oia4xi6IAJxARU":
            plan_name = "5 Dollars Per Month"
        elif plan_id == "price_1PlVSxE8m3oia4xi8007EBw6":
            plan_name = "12 Dollars After 3 months"
        else:
            plan_name = "Unknown Plan"
        
        response_data = {
            'customer' : stripe_subscription.customer,
            'stripe_subscription_id' : stripe_subscription.id,
            'status' : stripe_subscription.status,
            'plan' : plan_id,
            'plan_name' : plan_name,
            'created_at' : datetime.fromtimestamp(stripe_subscription.current_period_end).isoformat()
        }

        return Response(response_data, status = status.HTTP_200_OK)

    except stripe.error.StripeError as e:
        return Response({"error" : str(e)}, status = status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def list_subscriptions(request):
    user = request.user
    try:
        customer = get_object_or_404(StripeCustomer, user = user)
        subscriptions = StripeSubscription.objects.filter(customer=customer)

        if not subscriptions.exists():
            return Response({"message" : "No Subscriptions Found"} , status = status.HTTP_404_NOT_FOUND)
        
        serializer = StripeSubscriptionSerializer(subscriptions, many = True)
        return Response(serializer.data, status = status.HTTP_200_OK)

    except StripeCustomer.DoesNotExist:
        return Response({"error" : "Customer Not Found"}, status= status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def cancel_subscription(request):
    user = request.user
    customer = get_object_or_404(StripeCustomer, user = user)
    subscription_id = request.data.get("subscription_id")

    try:
        subscription = stripe.Subscription.retrieve(subscription_id)

        canceled_subscription = stripe.Subscription.delete(subscription_id)

        subscription_instance = get_object_or_404(StripeSubscription,stripe_subscription_id = subscription_id)
        subscription_instance.status = 'canceled'
        subscription_instance.save()

        serializer = StripeSubscriptionSerializer(subscription_instance)
        return Response(serializer.data, status = status.HTTP_200_OK)
    except stripe.error.StripeError as e:
        return Response({"error" : str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except StripeSubscription.DoesNotExist:
        return Response ({"error" : "Subscription Not Found"} , status=status.HTTP_404_NOT_FOUND)
    except ValueError as e:
        return Response({"error" : str(e)}, status= status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def resume_subscription(request):
    user = request.user
    customer = get_object_or_404(StripeCustomer, user=user)
    subscription_id = request.data.get("subscription_id")

    try:
        subscription_instance = get_object_or_404(StripeSubscription, stripe_subscription_id = subscription_id)

        if subscription_instance.status != 'canceled':
            return Response({"error" : "Subscription is not canceled"})
        
        subscription = stripe.Subscription.create(
            customer = customer.stripe_customer_id,
            items = [{"plan" : subscription_instance.plan}]
        )

        subscription_instance.stripe_subscription_id = subscription_id
        subscription_instance.status = subscription.status
        subscription_instance.current_period_end = datetime.fromtimestamp(subscription.current_period_end)
        subscription_instance.save()

        serializer = StripeSubscriptionSerializer(subscription_instance)
        return Response(serializer.data, status = status.HTTP_200_OK)

    except stripe.error.StripeError as e:
        return Response({"error" : str(e)}, status= status.HTTP_400_BAD_REQUEST)
    except StripeSubscription.DoesNotExist:
        return Response({"error" : "Subscription Not Found"}, status = status.HTTP_404_NOT_FOUND)
    except ValueError as e:
        return Response({"error" : str(e)}, status=status.HTTP_400_BAD_REQUEST)
