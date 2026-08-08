import psycopg2
from fastapi import HTTPException
from app.config.settings import settings


class DatabaseService:
    """
    Database service for read-only operations.
    Note: Create/Update operations are now handled by backend-api.

    Standalone on purpose: it only needs Postgres access, so it does not
    subclass BaseService (which would load the BGE embedding model).
    """

    def _get_db_connection(self):
        """Create a database connection"""
        try:
            conn = psycopg2.connect(**settings.db_config)
            return conn
        except Exception as e:
            print(f"[DB_ERROR] Failed to connect to database: {e}")
            raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

    def get_vector_ids(self, context_id: str) -> list:
        """Retrieve vector IDs for a context from the database"""
        try:
            import json

            conn = self._get_db_connection()
            cursor = conn.cursor()

            select_query = """
                SELECT "vectorIds"
                FROM user_context
                WHERE "contextId" = %s
            """

            cursor.execute(select_query, (context_id,))
            result = cursor.fetchone()

            cursor.close()
            conn.close()

            if result and result[0]:
                # Parse JSON from JSONB column
                vector_ids = result[0] if isinstance(result[0], list) else json.loads(result[0])
                print(f"[DB] Retrieved {len(vector_ids)} vector IDs for context {context_id}")
                return vector_ids
            else:
                print(f"[DB] No vector IDs found for context {context_id}")
                return []

        except Exception as e:
            print(f"[DB_ERROR] Failed to retrieve vector IDs: {e}")
            return []

    def get_all_vector_ids_by_user_profile(self, user_id: str, profile_id: str) -> list:
        """Retrieve all vector IDs for a given userId and profileId from the database"""
        try:
            import json

            conn = self._get_db_connection()
            cursor = conn.cursor()

            select_query = """
                SELECT "vectorIds"
                FROM user_context
                WHERE "userId" = %s AND "profileId" = %s AND "vectorIds" IS NOT NULL
            """

            cursor.execute(select_query, (user_id, profile_id))
            results = cursor.fetchall()

            cursor.close()
            conn.close()

            all_vector_ids = []
            for result in results:
                if result and result[0]:
                    # Parse JSON from JSONB column
                    vector_ids = result[0] if isinstance(result[0], list) else json.loads(result[0])
                    all_vector_ids.extend(vector_ids)

            print(f"[DB] Retrieved {len(all_vector_ids)} total vector IDs for userId {user_id}, profileId {profile_id}")
            return all_vector_ids

        except Exception as e:
            print(f"[DB_ERROR] Failed to retrieve all vector IDs: {e}")
            return []

    def batch_context_exists(self, context_ids: list) -> set:
        """Check which contexts exist in the database from a list of context IDs.
        Returns a set of context IDs that exist."""
        try:
            if not context_ids:
                return set()

            conn = self._get_db_connection()
            cursor = conn.cursor()

            # Use IN clause for batch validation (single query)
            placeholders = ','.join(['%s'] * len(context_ids))
            select_query = f"""
                SELECT "contextId"
                FROM user_context
                WHERE "contextId" IN ({placeholders})
            """

            cursor.execute(select_query, tuple(context_ids))
            results = cursor.fetchall()

            cursor.close()
            conn.close()

            # Return set of existing context IDs
            existing_ids = {row[0] for row in results}
            print(f"[DB] Batch validated {len(context_ids)} context IDs: {len(existing_ids)} exist, {len(context_ids) - len(existing_ids)} deleted")
            return existing_ids

        except Exception as e:
            print(f"[DB_ERROR] Failed to batch check context existence: {e}")
            return set()

# Create database service instance
database_service = DatabaseService()
