import graphene
from crm.schema import Query as CRMQuery, Mutation as CRMMutation


class Query(CRMQuery, graphene.ObjectType):
    """Root Query – aggregates queries from the CRM app (and others in future)."""
    pass


class Mutation(CRMMutation, graphene.ObjectType):
    """Root Mutation – aggregates mutations from the CRM app (and others in future)."""
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)

