#!/usr/bin/env python3
"""
Google Jobs API Integration Setup Script
Automates the complete setup process for Google Jobs API integration
"""

import subprocess
import sys
import os
import asyncio

def run_command(command, description):
    """Run a shell command and return success status"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description}: SUCCESS")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description}: FAILED")
            if result.stderr.strip():
                print(f"   Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description}: FAILED - {str(e)}")
        return False

async def test_api_integration():
    """Test the Google Jobs API integration"""
    print("\n🧪 Testing Google Jobs API Integration...")
    
    try:
        # Add current directory to Python path
        sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))
        
        from services.google_jobs_api import GoogleJobsAPIService
        
        api_service = GoogleJobsAPIService()
        
        # Test connection
        if not api_service.test_api_connection():
            print("❌ API connection test failed")
            return False
        
        # Test job search
        jobs = await api_service.search_jobs(
            keywords="software engineer",
            location="India",
            limit=2
        )
        
        if jobs:
            print(f"✅ API Integration Test: SUCCESS - Found {len(jobs)} jobs")
            return True
        else:
            print("⚠️ API Integration Test: No jobs found (but API is working)")
            return True
            
    except Exception as e:
        print(f"❌ API Integration Test: FAILED - {str(e)}")
        return False

def main():
    """Main setup process"""
    print("🚀 Google Jobs API Integration Setup")
    print("=" * 50)
    
    setup_steps = [
        {
            "command": "pip install aiohttp requests",
            "description": "Installing required Python packages",
            "required": True
        },
        {
            "command": "python run_migrations.py",
            "description": "Running database migrations",
            "required": True
        }
    ]
    
    # Execute setup steps
    all_success = True
    for step in setup_steps:
        success = run_command(step["command"], step["description"])
        if not success and step["required"]:
            all_success = False
            print(f"\n❌ Required step failed: {step['description']}")
            if input("\nContinue anyway? (y/N): ").lower() != 'y':
                break
    
    # Test the integration
    print("\n" + "=" * 50)
    test_success = asyncio.run(test_api_integration())
    
    # Final status
    print("\n" + "=" * 50)
    if all_success and test_success:
        print("🎉 Setup Complete! Google Jobs API is ready to use")
        print("\n📋 Next Steps:")
        print("   1. Start your FastAPI backend server")
        print("   2. Open the frontend admin panel")
        print("   3. Go to Admin Panel > Job Sources > API Integration tab")
        print("   4. Test the Google Jobs API integration")
        print("\n💡 API Details:")
        print("   • Source: Google Jobs via SerpAPI")
        print("   • Rate Limit: 100 requests/month (free tier)")
        print("   • Status: Active and ready to use")
    else:
        print("❌ Setup had issues. Please check the errors above.")
        print("\n🔧 Manual steps to try:")
        print("   1. Install dependencies: pip install aiohttp requests")
        print("   2. Run migrations: python run_migrations.py")
        print("   3. Test API: python test_google_jobs_api.py")

if __name__ == "__main__":
    main()
