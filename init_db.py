import os
import django
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'polling.settings')
django.setup()

def init_database():
    try:
        # Make migrations
        call_command('makemigrations')
        
        # Apply migrations
        call_command('migrate')
        
        print("Database initialization successful!")
    except Exception as e:
        print(f"Database initialization failed: {str(e)}")

if __name__ == "__main__":
    init_database() 