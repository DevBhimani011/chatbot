import strawberry
from app.db.session import get_connection
from app.graphql.types import WorkflowType

@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_workflow(self, name: str) -> WorkflowType:
        conn = get_connection()
        cur = conn.cursor()
        try:
            # 1. Create Workflow
            cur.execute(
                "INSERT INTO workflow (name) VALUES (%s) RETURNING id, name",
                (name,)
            )
            wf_row = cur.fetchone()
            wf_id = wf_row[0]
            wf_name = wf_row[1]

            # 2. Create Initial Node
            # We use default position (100, 100) and empty value as per previous logic
            cur.execute(
                """
                INSERT INTO node (workflow_id, value, position_x, position_y)
                VALUES (%s, %s, %s, %s)
                """,
                (wf_id, "", 100, 100)
            )

            conn.commit()
            return WorkflowType(id=str(wf_id), name=wf_name)
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()
