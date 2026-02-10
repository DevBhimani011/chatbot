import strawberry
from uuid import UUID

@strawberry.type
class WorkflowType:
    id: str
    name: str
