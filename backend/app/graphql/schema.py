import strawberry
from app.graphql.types import WorkflowType
from app.graphql.mutations import Mutation

@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello from GraphQL"

schema = strawberry.Schema(query=Query, mutation=Mutation)
