"""
CounterFlow v1.0.0 — Database Migrations
==========================================
Reserved for future schema migration scripts.
Not used in v1.0.0 — database is fully managed
by SQLAlchemy's create_all() on startup.

If the schema needs to change in a future version
(e.g. adding a new column to counterflow_products),
write a migration function here and call it from
counterflow_init_db() in database.py AFTER create_all().

Example migration pattern:

    def counterflow_migrate_v1_to_v2(session):
        \"\"\"
        CounterFlow v1 → v2 migration.
        Adds counterflow_discount column to counterflow_products.
        Safe to run multiple times (checks column existence first).
        \"\"\"
        from sqlalchemy import text, inspect
        counterflow_inspector = inspect(session.bind)
        counterflow_cols = [
            c['name'] for c in
            counterflow_inspector.get_columns('counterflow_products')
        ]
        if 'counterflow_discount' not in counterflow_cols:
            session.execute(text(
                'ALTER TABLE counterflow_products '
                'ADD COLUMN counterflow_discount REAL DEFAULT 0.0'
            ))
            session.commit()
"""

# No migrations needed for CounterFlow v1.0.0
