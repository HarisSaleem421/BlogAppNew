import os
import stripe
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework import status

stripe.api_key = os.environ.get('VST_STRIPE_SECRET_KEY')

class Stripe():
    def fetch_products(self):
        return stripe.Product.list(limit=3)

    def fetch_prices(self, product):
        return stripe.Price.list(product=product)
    
    def product_detail(self, price_id):
       price = stripe.Price.retrieve(price_id)
       return stripe.Product.retrieve(price['product'])

    def create_payment_method(self):
        return stripe.PaymentMethod.create(
        type="card",
        card={
            "number": "4242424242424242",
            "exp_month": 8,
            "exp_year": 2024,
            "cvc": "0976",
        },
        metadata={
            "name": "Ali Zain",
            "zip_or_postalCode": 1235
        }
        )

    def create_customer(self,email):
        try:
            customer = stripe.Customer.create(
                email=email,
            )
            return customer
        except Exception as e:
            raise ValueError(e._message)

    def attach_payment_method(self,customer,payment_method_id):
        try:
            return stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer,
            )
        except stripe.error.CardError as e:
            error_message = str(e._message)
            print(error_message, "56")
            raise ValueError(e._message)
        except stripe.error.InvalidRequestError as e:
            print(e._message, "55")
            raise ValueError(e._message)

    def fetch_customer(self,customer):
        try:
            return stripe.Customer.retrieve(customer)
        except stripe.error.InvalidRequestError as e:
            raise ValueError(e._message)

    def update_customer(self,customer, payment_method_id):
        try:
            return stripe.Customer.modify(
                customer,
                invoice_settings = {
                "default_payment_method": payment_method_id
                }
            )
        except stripe.error.InvalidRequestError as e:
            raise ValueError(e._message)

    def fetch_payment_object(self,payment):
        """ get payment object from stripe """
        return stripe.PaymentMethod.retrieve(payment)

    def create_subscription(self, customer, price_id):
        try:
            sub = stripe.Subscription.create(
                customer=customer,
                items=[
                    {"price": price_id,
                    },
                ],
                )
            return sub
        except stripe.error.InvalidRequestError as e:
            raise ValueError(e._message)

    def retrieve_subscription(self,sub_id):
        try:
            sub = stripe.Subscription.retrieve(
                    sub_id
            )
            return sub
        except Exception as e:
            raise ValueError(e.message)

    def update_subscription(self,sub_id,sub_item_id,price_id):
        try:
            return stripe.Subscription.modify(
                sub_id,
                items=[{
                'id': sub_item_id,
            'price': price_id,
            }]
            )
        except stripe.error.InvalidRequestError as e:
            raise ValueError(e._message)

    def cancel_subscription(self, sub_id, status):
        try:
            stripe.Subscription.modify(
            sub_id,
            metadata={"cancel_at_period_end": status})
        except stripe.error.InvalidRequestError as e:
            raise ValueError(e._message)
