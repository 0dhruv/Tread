"""
Automated setup script for the Stock Trading Platform.
Checks prerequisites and helps initialize the application.
"""
import os
import sys
import subprocess
from pathlib import Path


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def check_python_version():
    """Check if Python version is 3.9+"""
    print("✓ Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("✗ Python 3.9+ is required")
        return False
    print(f"  Python {version.major}.{version.minor}.{version.micro} detected")
    return True


def check_postgresql():
    """Check if PostgreSQL is accessible"""
    print("\n✓ Checking PostgreSQL...")
    try:
        result = subprocess.run(
            ['psql', '--version'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"  {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print("✗ PostgreSQL not found")
    print("  Please install PostgreSQL from https://www.postgresql.org/download/")
    return False


def create_env_file():
    """Create .env file from template"""
    print("\n✓ Creating environment file...")
    
    if Path('.env').exists():
        print("  .env already exists, skipping...")
        return True
    
    if not Path('.env.example').exists():
        print("✗ .env.example not found")
        return False
    
    # Copy template
    with open('.env.example', 'r') as f:
        content = f.read()
    
    with open('.env', 'w') as f:
        f.write(content)
    
    print("  Created .env file")
    print("  Please edit .env and add your database URL and API keys")
    return True


def install_dependencies():
    """Install Python dependencies"""
    print("\n✓ Installing dependencies...")
    print("  This may take a few minutes...\n")
    
    try:
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
            check=True
        )
        print("\n  Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("\n✗ Failed to install dependencies")
        return False


def initialize_database():
    """Initialize database tables"""
    print("\n✓ Initializing database...")
    
    try:
        from app.database import init_db
        init_db()
        print("  Database initialized successfully")
        return True
    except Exception as e:
        print(f"\n✗ Failed to initialize database: {e}")
        print("  Please check your DATABASE_URL in .env")
        return False


def main():
    """Main setup routine"""
    print_header("Stock Trading Platform - Setup")
    
    # Check prerequisites
    if not check_python_version():
        return
    
    if not check_postgresql():
        print("\nSetup cannot continue without PostgreSQL.")
        print("Please install PostgreSQL and run this script again.")
        return
    
    # Create environment file
    if not create_env_file():
        print("\nPlease create .env file manually and run setup again.")
        return
    
    # Install dependencies
    if not install_dependencies():
        print("\nSetup failed. Please check error messages above.")
        return
    
    # Initialize database
    print("\n" + "=" * 60)
    response = input("Initialize database now? (y/n): ")
    if response.lower() == 'y':
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        if not initialize_database():
            print("\nDatabase initialization failed.")
            print("You can initialize it later by running:")
            print("  python -c \"from app.database import init_db; init_db()\"")
    
    # Success message
    print_header("Setup Complete!")
    
    print("Next steps:")
    print("\n1. Configure your .env file with:")
    print("   - DATABASE_URL (PostgreSQL connection)")
    print("   - GOOGLE_API_KEY (from https://makersuite.google.com/app/apikey)")
    
    print("\n2. Collect stock data:")
    print("   python scripts/collect_data.py --stocks 20 --days 90")
    
    print("\n3. Run the application:")
    print("   uvicorn main:app --reload")
    
    print("\n4. Visit http://localhost:8000")
    
    print("\nFor detailed instructions, see SETUP.md")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
