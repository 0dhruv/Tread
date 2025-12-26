import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_database():
    try:
        # Connect to default postgres database
        con = psycopg2.connect(
            user="postgres",
            password="Dhruv@123",
            host="localhost",
            port="5432",
            database="postgres"
        )
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = con.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'stock_trading'")
        exists = cursor.fetchone()
        
        if not exists:
            print("Creating database stock_trading...")
            cursor.execute("CREATE DATABASE stock_trading")
            print("Database created successfully.")
        else:
            print("Database stock_trading already exists.")
            
        cursor.close()
        con.close()
        return True
        
    except Exception as e:
        print(f"Error creating database: {e}")
        return False

if __name__ == "__main__":
    create_database()
