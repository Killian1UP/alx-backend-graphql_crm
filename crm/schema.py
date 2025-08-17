import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from .models import Customer, Product, Order
from .filters import CustomerFilter, ProductFilter, OrderFilter


# ----------------------
# GraphQL Types with Relay Nodes
# ----------------------
class CustomerNode(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone", "created_at")
        filterset_class = CustomerFilter
        interfaces = (graphene.relay.Node,)


class ProductNode(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")
        filterset_class = ProductFilter
        interfaces = (graphene.relay.Node,)


class OrderNode(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "customer", "products", "order_date", "total_amount")
        filterset_class = OrderFilter
        interfaces = (graphene.relay.Node,)


# ----------------------
# Query with Filters + Ordering
# ----------------------
class Query(graphene.ObjectType):
    hello = graphene.String(default_value="Hello, GraphQL!")

    # Relay Node fields
    customer = graphene.relay.Node.Field(CustomerNode)
    product = graphene.relay.Node.Field(ProductNode)
    order = graphene.relay.Node.Field(OrderNode)

    # Filtered list queries
    all_customers = DjangoFilterConnectionField(CustomerNode, order_by=graphene.List(of_type=graphene.String))
    all_products = DjangoFilterConnectionField(ProductNode, order_by=graphene.List(of_type=graphene.String))
    all_orders = DjangoFilterConnectionField(OrderNode, order_by=graphene.List(of_type=graphene.String))

    # Custom ordering resolver
    def resolve_all_customers(self, info, **kwargs):
        qs = Customer.objects.all()
        order_by = kwargs.get("order_by")
        if order_by:
            qs = qs.order_by(*order_by)
        return qs

    def resolve_all_products(self, info, **kwargs):
        qs = Product.objects.all()
        order_by = kwargs.get("order_by")
        if order_by:
            qs = qs.order_by(*order_by)
        return qs

    def resolve_all_orders(self, info, **kwargs):
        qs = Order.objects.all()
        order_by = kwargs.get("order_by")
        if order_by:
            qs = qs.order_by(*order_by)
        return qs
