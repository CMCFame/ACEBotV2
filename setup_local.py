# setup_local.py
"""
Setup script for local development
"""

import subprocess
import sys
import os

def setup_local_environment():
    """Setup local environment for testing"""
    print("Setting up ACEBotV2 for local development...")
    print("=" * 50)
    
    # Install requirements
    if os.path.exists("requirements.txt"):
        print("Installing requirements from requirements.txt...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
            print("✓ Requirements installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error installing requirements: {e}")
            return False
    else:
        print("No requirements.txt found. Installing basic requirements...")
        basic_requirements = [
            "streamlit",
            "boto3",
            "pandas"
        ]
        
        for req in basic_requirements:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", req], check=True)
                print(f"✓ Installed {req}")
            except subprocess.CalledProcessError as e:
                print(f"❌ Error installing {req}: {e}")
    
    # Check AWS credentials setup
    print("\n" + "=" * 50)
    print("AWS Credentials Setup")
    print("=" * 50)
    
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    
    if not aws_access_key or not aws_secret_key:
        print("⚠️  AWS credentials not found in environment variables")
        print("\nTo set them up, run these commands:")
        print("Windows:")
        print("  set AWS_ACCESS_KEY_ID=your_access_key_here")
        print("  set AWS_SECRET_ACCESS_KEY=your_secret_key_here")
        print("\nOr create a .env file in this directory with:")
        print("  AWS_ACCESS_KEY_ID=your_access_key_here")
        print("  AWS_SECRET_ACCESS_KEY=your_secret_key_here")
        
        # Create sample .env file
        env_content = """# AWS Credentials for ACEBotV2
# Replace with your actual AWS credentials
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_DEFAULT_REGION=us-east-1
"""
        with open(".env.example", "w") as f:
            f.write(env_content)
        print(f"\n✓ Created .env.example file with template")
    else:
        print("✓ AWS credentials found in environment")
    
    print(f"\n" + "=" * 50)
    print("Setup complete! To run locally:")
    print("  python run_local.py")
    print("Then open http://localhost:8501 in your browser")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    setup_local_environment()