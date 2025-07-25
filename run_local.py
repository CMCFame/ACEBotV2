# run_local.py
"""
Script to run the Streamlit app locally for testing
"""

import subprocess
import sys
import os

def run_local_streamlit():
    """Run the Streamlit app locally"""
    print("Starting ACEBotV2 locally...")
    print("=" * 50)
    print("Make sure you have your AWS credentials set up:")
    print("1. Set AWS_ACCESS_KEY_ID environment variable")
    print("2. Set AWS_SECRET_ACCESS_KEY environment variable")
    print("3. Or have AWS credentials in ~/.aws/credentials")
    print("=" * 50)
    
    # Check if streamlit is installed
    try:
        import streamlit
        print(f"✓ Streamlit found: {streamlit.__version__}")
    except ImportError:
        print("❌ Streamlit not installed. Run: pip install streamlit")
        return
    
    # Check if AWS boto3 is available
    try:
        import boto3
        print("✓ Boto3 found for AWS Bedrock")
    except ImportError:
        print("❌ Boto3 not installed. Run: pip install boto3")
        return
    
    # Check if AWS credentials are available
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    
    if aws_access_key and aws_secret_key:
        print("✓ AWS credentials found in environment variables")
    else:
        print("⚠️  AWS credentials not found in environment. Will try default provider chain.")
        print("   Make sure you have credentials configured via:")
        print("   - Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)")
        print("   - AWS credentials file (~/.aws/credentials)")
        print("   - IAM role (if running on EC2)")
    
    print("\n" + "=" * 50)
    print("Starting Streamlit app at http://localhost:8501")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Run streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ], check=True)
    except KeyboardInterrupt:
        print("\n✓ Streamlit server stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running Streamlit: {e}")
    except FileNotFoundError:
        print("❌ Streamlit command not found. Make sure it's installed: pip install streamlit")

if __name__ == "__main__":
    run_local_streamlit()