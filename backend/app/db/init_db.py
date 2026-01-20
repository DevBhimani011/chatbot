from app.db.session import get_connection


def init_db() -> None:
    """
    Create required tables if they don't exist.
    This project doesn't use a migrations framework, so we do a safe bootstrap here.
    """
    conn = get_connection()
    cur = conn.cursor()

    # UUID generation
    cur.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

    # ------------------------------------------------------
    # Linear workflows
    # ------------------------------------------------------
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS workflow (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS node (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            workflow_id UUID NOT NULL REFERENCES workflow(id) ON DELETE CASCADE,
            value TEXT NOT NULL DEFAULT '',
            position_x DOUBLE PRECISION,
            position_y DOUBLE PRECISION,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS edge (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            workflow_id UUID NOT NULL REFERENCES workflow(id) ON DELETE CASCADE,
            from_node_id UUID NOT NULL REFERENCES node(id) ON DELETE CASCADE,
            to_node_id UUID NOT NULL REFERENCES node(id) ON DELETE CASCADE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )

    # ------------------------------------------------------
    # Tree workflows (FAQ workflows)
    # ------------------------------------------------------
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tree_workflow (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tree_node (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            tree_workflow_id UUID NOT NULL REFERENCES tree_workflow(id) ON DELETE CASCADE,
            value TEXT NOT NULL DEFAULT '',
            position_x DOUBLE PRECISION,
            position_y DOUBLE PRECISION,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tree_edge (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            tree_workflow_id UUID NOT NULL REFERENCES tree_workflow(id) ON DELETE CASCADE,
            from_node_id UUID NOT NULL REFERENCES tree_node(id) ON DELETE CASCADE,
            to_node_id UUID NOT NULL REFERENCES tree_node(id) ON DELETE CASCADE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )

    # In case tables existed before, ensure new columns exist.
    # (Postgres supports IF NOT EXISTS for ADD COLUMN)
    cur.execute('ALTER TABLE node ADD COLUMN IF NOT EXISTS position_x DOUBLE PRECISION;')
    cur.execute('ALTER TABLE node ADD COLUMN IF NOT EXISTS position_y DOUBLE PRECISION;')
    cur.execute('ALTER TABLE tree_node ADD COLUMN IF NOT EXISTS position_x DOUBLE PRECISION;')
    cur.execute('ALTER TABLE tree_node ADD COLUMN IF NOT EXISTS position_y DOUBLE PRECISION;')
    cur.execute('ALTER TABLE tree_workflow ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();')

    conn.commit()
    cur.close()
    conn.close()

