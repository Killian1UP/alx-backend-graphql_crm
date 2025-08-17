import re
from django.db import transaction
from django.utils import timezone
import graphene
from graphene_django import DjangoObjectType

from .models import Customer, Product, Order


# ----------------------
# GraphQL Types
# ----------------------
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone")


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "customer", "products", "order_date", "total_amount")


# ----------------------
# Mutations
# ----------------------
class CreateCustomer(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String(required=False)

    customer = graphene.Field(CustomerType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, name, email, phone=None):
        # Check for duplicate email
        if Customer.objects.filter(email=email).exists():
            return CreateCustomer(success=False, message="Email already exists.")

        # Validate phone format if provided
        if phone:
            phone_pattern = re.compile(r"^(\+?\d{7,15}|\d{3}-\d{3}-\d{4})$")
            if not phone_pattern.match(phone):
                return CreateCustomer(success=False, message="Invalid phone format.")

        customer = Customer.objects.create(name=name, email=email, phone=phone)
        return CreateCustomer(customer=customer, success=True, message="Customer created successfully.")


class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        customers = graphene.List(
            graphene.NonNull(
                graphene.InputObjectType(
                    "CustomerInput",
                    name=graphene.String(required=True),
                    email=graphene.String(required=True),
                    phone=graphene.String()
                )
            )
        )

    created_customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, customers):
        created = []
        errors = []

        with transaction.atomic():
            for idx, data in enumerate(customers):
                if Customer.objects.filter(email=data.email).exists():
                    errors.append(f"Row {idx+1}: Email already exists ({data.email})")
                    continue

                if data.phone:
                    phone_pattern = re.compile(r"^(\+?\d{7,15}|\d{3}-\d{3}-\d{4})$")
                    if not phone_pattern.match(data.phone):
                        errors.append(f"Row {idx+1}: Invalid phone format ({data.phone})")
                        continue

                customer = Customer.objects.create(
                    name=data.name,
                    email=data.email,
                    phone=data.phone
                )
                created.append(customer)

        return BulkCreateCustomers(created_customers=created, errors=errors)


class CreateProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Float(required=True)
        stock = graphene.Int(required=False, default_value=0)

    product = graphene.Field(ProductType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, name, price, stock=0):
        if price <= 0:
            return CreateProduct(success=False, message="Price must be positive.")
        if stock < 0:
            return CreateProduct(success=False, message="Stock cannot be negative.")

        product = Product.objects.create(name=name, price=price, stock=stock)
        return CreateProduct(product=product, success=True, message="Product created successfully.")


class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.ID(required=True)
        product_ids = graphene.List(graphene.ID, required=True)
        order_date = graphene.DateTime(required=False)

    order = graphene.Field(OrderType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, customer_id, product_ids, order_date=None):
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            return CreateOrder(success=False, message="Invalid customer ID.")

        if not product_ids:
            return CreateOrder(success=False, message="At least one product must be selected.")

        products = Product.objects.filter(id__in=product_ids)
        if products.count() != len(product_ids):
            return CreateOrder(success=False, message="One or more product IDs are invalid.")

        if not order_date:
            order_date = timezone.now()

        order = Order.objects.create(customer=customer, order_date=order_date)

        order.products.set(products)
        total_amount = sum(p.price for p in products)
        order.total_amount = total_amount
        order.save()

        return CreateOrder(order=order, success=True, message="Order created successfully.")


# ----------------------
# Root Mutation Class
# ----------------------
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()


# Attach to Schema
class Query(graphene.ObjectType):
    # You can extend with queries (like fetching customers, products, etc.)
    hello = graphene.String(default_value="Hello, GraphQL!")


schema = graphene.Schema(query=Query, mutation=Mutation)
