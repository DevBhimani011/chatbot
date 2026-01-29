import strawberry
from typing import Optional

@strawberry.type
class WorkflowType:
    id: str
    name: str
