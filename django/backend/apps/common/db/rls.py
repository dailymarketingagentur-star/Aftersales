from django.db import migrations


class EnableRLS(migrations.operations.base.Operation):
    """Migration operation to enable Row-Level Security on a table."""

    reversible = True

    def __init__(self, table_name):
        self.table_name = table_name

    def state_forwards(self, app_label, state):
        pass

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        schema_editor.execute(f"ALTER TABLE {self.table_name} ENABLE ROW LEVEL SECURITY;")
        schema_editor.execute(f"ALTER TABLE {self.table_name} FORCE ROW LEVEL SECURITY;")
        schema_editor.execute(
            f"CREATE POLICY tenant_isolation ON {self.table_name} "
            f"USING (tenant_id::text = current_setting('app.current_tenant_id', true));"
        )

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        schema_editor.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {self.table_name};")
        schema_editor.execute(f"ALTER TABLE {self.table_name} DISABLE ROW LEVEL SECURITY;")

    def describe(self):
        return f"Enable RLS on {self.table_name}"
