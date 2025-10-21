#!/usr/bin/env python3
"""
Interactive Demo for Social Media Automation Tool
This script allows you to test the automation with real credentials
"""

import os
import sys
from social_media_automator import SocialMediaAutomator, PostContent

def get_user_input():
    """Get user input for testing"""
    print("🔐 Social Media Automation - Interactive Demo")
    print("=" * 50)
    print("⚠️  WARNING: This will attempt to login to real social media platforms!")
    print("   Make sure you have dedicated automation accounts.")
    print()
    
    # Get platform choice
    print("Select platform to test:")
    print("1. LinkedIn")
    print("2. Twitter")
    print("3. Both")
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice not in ['1', '2', '3']:
        print("❌ Invalid choice. Exiting.")
        return None
    
    # Get credentials
    print("\n🔑 Enter your credentials:")
    email = input("Email: ").strip()
    password = input("Password: ").strip()
    
    if not email or not password:
        print("❌ Email and password are required. Exiting.")
        return None
    
    # Get post content
    print("\n📝 Enter your post content:")
    text = input("Post text: ").strip()
    
    if not text:
        print("❌ Post text is required. Exiting.")
        return None
    
    hashtags_input = input("Hashtags (comma-separated, optional): ").strip()
    hashtags = [tag.strip() for tag in hashtags_input.split(',')] if hashtags_input else []
    
    return {
        'platform': choice,
        'email': email,
        'password': password,
        'text': text,
        'hashtags': hashtags
    }

def test_linkedin_posting(automator, content, email, password):
    """Test LinkedIn posting"""
    print("\n🔗 Testing LinkedIn posting...")
    
    try:
        # Login to LinkedIn
        print("   Logging into LinkedIn...")
        login_success = automator.login_linkedin(email, password)
        
        if not login_success:
            print("❌ LinkedIn login failed")
            return False
        
        print("✅ LinkedIn login successful")
        
        # Post content
        print("   Posting content to LinkedIn...")
        post_success = automator.post_to_linkedin(content)
        
        if post_success:
            print("✅ LinkedIn post successful!")
            return True
        else:
            print("❌ LinkedIn post failed")
            return False
            
    except Exception as e:
        print(f"❌ LinkedIn error: {str(e)}")
        return False

def test_twitter_posting(automator, content, email, password):
    """Test Twitter posting"""
    print("\n🐦 Testing Twitter posting...")
    
    try:
        # Note: Twitter login would need to be implemented
        print("   Note: Twitter login not implemented in this demo")
        print("   This would require additional Twitter-specific login logic")
        return False
        
    except Exception as e:
        print(f"❌ Twitter error: {str(e)}")
        return False

def main():
    """Main interactive demo function"""
    # Get user input
    user_input = get_user_input()
    if not user_input:
        return
    
    # Create content
    content = PostContent(
        text=user_input['text'],
        hashtags=user_input['hashtags']
    )
    
    print(f"\n📝 Created content:")
    print(f"   Text: {content.text}")
    print(f"   Hashtags: {content.hashtags}")
    
    # Confirm before proceeding
    confirm = input("\n⚠️  Proceed with automation? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Automation cancelled by user")
        return
    
    # Initialize automator
    print("\n🔧 Initializing automation tool...")
    automator = SocialMediaAutomator(headless=False)  # Set to False for debugging
    
    try:
        automator.setup_driver()
        print("✅ Browser driver setup successful")
        
        results = {}
        
        # Test selected platforms
        if user_input['platform'] in ['1', '3']:  # LinkedIn
            results['linkedin'] = test_linkedin_posting(
                automator, content, user_input['email'], user_input['password']
            )
        
        if user_input['platform'] in ['2', '3']:  # Twitter
            results['twitter'] = test_twitter_posting(
                automator, content, user_input['email'], user_input['password']
            )
        
        # Show results
        print("\n📊 Results Summary:")
        print("=" * 30)
        for platform, success in results.items():
            status = "✅ Success" if success else "❌ Failed"
            print(f"{platform.capitalize()}: {status}")
        
        # Overall result
        if any(results.values()):
            print("\n🎉 Automation completed with some successes!")
        else:
            print("\n❌ All automation attempts failed")
            
    except Exception as e:
        print(f"\n❌ Automation failed: {str(e)}")
        
    finally:
        print("\n🧹 Cleaning up...")
        automator.close()
        print("✅ Cleanup completed")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        sys.exit(1)
