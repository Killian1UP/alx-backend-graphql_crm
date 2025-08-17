import re
from django.db import transaction
from django.utils import timezone
import graphene
from graphene_django import DjangoObjectType
from graphql import GraphQLError

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
    message = graphene.String()

    def mutate(self, info, name, email, phone=None):
        # Email uniqueness
        if Customer.objects.filter(email=email).exists():
            raise GraphQLError("Email already exists")

        # Phone validation
        if phone:
            phone_pattern = re.compile(r"^(\+?\d{7,15}|\d{3}-\d{3}-\d{4})$")
            if not phone_pattern.match(phone):
                raise GraphQLError("Invalid phone format (expected +1234567890 or 123-456-7890)")

        customer = Customer.objects.create(name=name, email=email, phone=phone)
        return CreateCustomer(customer=customer, message="Customer created successfully")


class BulkCreateCustomers(graphene.Mutation):
    class CustomerInput(graphene.InputObjectType):
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String()

    class Arguments:
        customers = graphene.List(CustomerInput, required=True)

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
    message = graphene.String()

    def mutate(self, info, name, price, stock=0):
        if price <= 0:
            raise GraphQLError("Price must be greater than zero")
        if stock < 0:
            raise GraphQLError("Stock cannot be negative")

        product = Product.objects.create(name=name, price=price, stock=stock)
        return CreateProduct(product=product, message="Product created successfully")


class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.ID(required=True)
        product_ids = graphene.List(graphene.ID, required=True)
        order_date = graphene.DateTime(required=False)

    order = graphene.Field(OrderType)
    message = graphene.String()

    def mutate(self, info, customer_id, product_ids, order_date=None):
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            raise GraphQLError("Invalid customer ID")

        if not product_ids:
            raise GraphQLError("At least one product must be selected")

        products = Product.objects.filter(id__in=product_ids)
        if products.count() != len(product_ids):
            raise GraphQLError("One or more product IDs are invalid")

        if not order_date:
            order_date = timezone.now()

        order = Order.objects.create(customer=customer, order_date=order_date)

        # Associate products
        order.products.set(products)
        order.total_amount = sum(p.price for p in products)
        order.save()

        return CreateOrder(order=order, message="Order created successfully")


# ----------------------
# Root Mutation
# ----------------------
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()


# Queries (basic)
class Query(graphene.ObjectType):
    hello = graphene.String(default_value="Hello, GraphQL!")
    customers = graphene.List(CustomerType)
    products = graphene.List(ProductType)
    orders = graphene.List(OrderType)

    def resolve_customers(root, info):
        return Customer.objects.all()

    def resolve_products(root, info):
        return Product.objects.all()

    def resolve_orders(root, info):
        return Order.objects.select_related("customer").prefetch_related("products")

