"""Repository layer sub-package.

Repositories handle all database interactions via async SQLAlchemy sessions.
Every query must be scoped to the current authenticated user's ID.
"""
