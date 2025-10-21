#!/usr/bin/env python3
"""
Quick Start Script for Social Media Automation
This script provides a simple way to get started with the automation tool
"""

import os
import sys
from datetime import datetime
from social_media_automator import SocialMediaAutomator, PostContent

def create_sample_content():
    """Create sample content for testing"""
    return PostContent(
        text="🚀 Exciting news! Our AI audit platform now supports automated social media posting! This is a test post to demonstrate the automation capabilities. #AI #Automation #Tech #Innovation",
        hashtags=["AI", "Automation", "Tech", "Innovation", "Demo"]
    )

def check_environment():
    """Check if environment is properly set up"""
    print("🔍 Checking environment setup...")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("⚠️  .env file not found. Creating from template...")
        if os.path.exists('env.example'):
            os.system('cp env.example .env')
            print("✅ Created .env file from template")
            print("📝 Please edit .env file with your credentials")
            return False
        else:
            print("❌ env.example file not found")
            return False
    
    print("✅ .env file found")
    return True

def run_automation_demo():
    """Run automation demo"""
    print("🚀 Social Media Automation - Quick Start")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        print("\n📚 Setup Instructions:")
        print("1. Edit .env file with your social media credentials")
        print("2. Run this script again")
        return
    
    # Create sample content
    content = create_sample_content()
    
    print(f"\n📝 Sample content created:")
    print(f"   Text: {content.text}")
    print(f"   Hashtags: {content.hashtags}")
    
    # Ask user if they want to proceed
    print("\n⚠️  This will attempt to login to social media platforms!")
    print("   Make sure you have the credentials configured in .env")
    
    proceed = input("\nProceed with automation? (y/N): ").strip().lower()
    if proceed != 'y':
        print("❌ Automation cancelled")
        return
    
    # Initialize automator
    print("\n🔧 Initializing automation tool...")
    automator = SocialMediaAutomator(headless=True)
    
    try:
        automator.setup_driver()
        print("✅ Browser driver setup successful")
        
        # Load credentials from .env
        from dotenv import load_dotenv
        load_dotenv()
        
        linkedin_email = os.getenv('LINKEDIN_EMAIL')
        linkedin_password = os.getenv('LINKEDIN_PASSWORD')
        
        if not linkedin_email or not linkedin_password:
            print("❌ LinkedIn credentials not found in .env file")
            print("   Please add LINKEDIN_EMAIL and LINKEDIN_PASSWORD to .env")
            return
        
        # Test LinkedIn posting
        print("\n🔗 Testing LinkedIn posting...")
        print("   Logging into LinkedIn...")
        
        login_success = automator.login_linkedin(linkedin_email, linkedin_password)
        
        if not login_success:
            print("❌ LinkedIn login failed")
            print("   Please check your credentials and try again")
            return
        
        print("✅ LinkedIn login successful")
        
        print("   Posting content to LinkedIn...")
        post_success = automator.post_to_linkedin(content)
        
        if post_success:
            print("✅ LinkedIn post successful!")
            print("🎉 Automation completed successfully!")
        else:
            print("❌ LinkedIn post failed")
            print("   This might be due to rate limits or content restrictions")
        
    except Exception as e:
        print(f"❌ Automation failed: {str(e)}")
        print("   Please check your setup and try again")
        
    finally:
        print("\n🧹 Cleaning up...")
        automator.close()
        print("✅ Cleanup completed")

def show_usage_examples():
    """Show usage examples"""
    print("\n📚 Usage Examples:")
    print("=" * 30)
    
    print("\n1. Basic Usage:")
    print("""
from social_media_automator import SocialMediaAutomator, PostContent

# Create automator
automator = SocialMediaAutomator(headless=True)
automator.setup_driver()

# Login
automator.login_linkedin("your_email", "your_password")

# Create content
content = PostContent(
    text="Your post text here",
    hashtags=["tag1", "tag2"]
)

# Post
automator.post_to_linkedin(content)
automator.close()
""")
    
    print("\n2. Advanced Usage with Scheduling:")
    print("""
from advanced_automator import AdvancedSocialMediaAutomator, PostContent
import asyncio

async def main():
    automator = AdvancedSocialMediaAutomator(headless=True)
    await automator.setup()
    
    content = PostContent(
        text="Your post text",
        hashtags=["AI", "Automation"]
    )
    
    results = await automator.post_to_multiple_platforms(
        content, ["linkedin", "twitter"]
    )
    
    await automator.close()

asyncio.run(main())
""")

def main():
    """Main function"""
    print("🎯 Social Media Automation Tool - Quick Start")
    print("=" * 60)
    
    # Show menu
    print("\nSelect an option:")
    print("1. Run automation demo")
    print("2. Show usage examples")
    print("3. Check environment setup")
    print("4. Exit")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == '1':
        run_automation_demo()
    elif choice == '2':
        show_usage_examples()
    elif choice == '3':
        check_environment()
    elif choice == '4':
        print("👋 Goodbye!")
        return
    else:
        print("❌ Invalid choice")
        return
    
    # Ask if user wants to continue
    print("\n" + "=" * 60)
    continue_choice = input("Would you like to try another option? (y/N): ").strip().lower()
    if continue_choice == 'y':
        main()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)
