import psycopg2
import psycopg2.extras

import common


def run_query(query: str) -> list | None:
    """
    Returns TUPLES of the records returned by the query.
    :param query:
    :return:
    """

    global cursor, connection
    try:
        # Connect to the PostgreSQL database
        connection = psycopg2.connect(
            dbname=common.SUPABASE_NAME,
            user=common.SUPABASE_USER,
            password=common.SUPABASE_PASSWORD,
            host=common.SUPABASE_HOST,
            port=common.SUPABASE_PORT
        )

        # Fetch results using standard cursor
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            return rows

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()
