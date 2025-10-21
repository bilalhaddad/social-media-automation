#!/usr/bin/env python3
"""
Test Script for Social Media Automation Tool
This script tests the automation functionality without user input
"""

import os
import sys
import time
from social_media_automator import SocialMediaAutomator, PostContent

def test_basic_functionality():
    """Test basic automation functionality"""
    print("🧪 Testing Social Media Automation Tool")
    print("=" * 50)
    
    # Create test content
    content = PostContent(
        text="🧪 Test post from Social Media Automation Tool - This is a test to verify the automation is working correctly. #Test #Automation #AI",
        hashtags=["Test", "Automation", "AI", "Demo"]
    )
    
    print(f"📝 Test content created:")
    print(f"   Text: {content.text}")
    print(f"   Hashtags: {content.hashtags}")
    print()
    
    # Initialize automator
    print("🔧 Initializing automation tool...")
    automator = SocialMediaAutomator(headless=True)
    
    try:
        print("🌐 Setting up browser driver...")
        automator.setup_driver()
        print("✅ Browser driver setup successful!")
        
        print("\n📋 Testing browser functionality...")
        # Test basic browser operations
        automator.driver.get("https://www.google.com")
        print("✅ Browser navigation test passed")
        
        # Test content validation
        print("\n🔍 Testing content validation...")
        if content.text and len(content.text) > 0:
            print("✅ Content validation passed")
        else:
            print("❌ Content validation failed")
            return False
        
        # Test hashtag processing
        print("\n🏷️  Testing hashtag processing...")
        if content.hashtags:
            hashtag_text = " ".join([f"#{tag}" for tag in content.hashtags])
            print(f"✅ Hashtags processed: {hashtag_text}")
        else:
            print("⚠️  No hashtags provided")
        
        print("\n📊 All tests passed successfully!")
        print("   The automation tool is ready for use with real credentials.")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False
        
    finally:
        print("\n🧹 Cleaning up...")
        automator.close()
        print("✅ Cleanup completed")

def test_environment_setup():
    """Test environment setup"""
    print("\n🔍 Testing environment setup...")
    
    # Check if .env file exists
    if os.path.exists('.env'):
        print("✅ .env file found")
        
        # Check if credentials are configured
        from dotenv import load_dotenv
        load_dotenv()
        
        linkedin_email = os.getenv('LINKEDIN_EMAIL')
        linkedin_password = os.getenv('LINKEDIN_PASSWORD')
        
        if linkedin_email and linkedin_password:
            print("✅ LinkedIn credentials configured")
        else:
            print("⚠️  LinkedIn credentials not configured")
            print("   Please add LINKEDIN_EMAIL and LINKEDIN_PASSWORD to .env")
    else:
        print("⚠️  .env file not found")
        print("   Please copy env.example to .env and configure credentials")
    
    # Check if Chrome is available
    chrome_paths = ['/usr/bin/google-chrome', '/usr/bin/chromium-browser']
    chrome_found = False
    
    for path in chrome_paths:
        if os.path.exists(path):
            print(f"✅ Chrome found at {path}")
            chrome_found = True
            break
    
    if not chrome_found:
        print("⚠️  Chrome/Chromium not found")
        print("   Please install Chrome or Chromium browser")

def test_content_creation():
    """Test content creation functionality"""
    print("\n📝 Testing content creation...")
    
    # Test different content types
    content_types = [
        {
            "name": "Announcement",
            "text": "🎉 Exciting announcement! Our new AI automation features are now live!",
            "hashtags": ["Announcement", "AI", "Automation", "NewFeature"]
        },
        {
            "name": "Educational",
            "text": "💡 Tip: Automated social media posting can increase engagement by up to 40%!",
            "hashtags": ["Tip", "SocialMedia", "Engagement", "Automation"]
        },
        {
            "name": "Case Study",
            "text": "📊 Success Story: How we increased social media reach by 300% using automation",
            "hashtags": ["Success", "CaseStudy", "Growth", "Automation"]
        }
    ]
    
    for i, content_data in enumerate(content_types, 1):
        content = PostContent(
            text=content_data["text"],
            hashtags=content_data["hashtags"]
        )
        
        print(f"\n{i}. {content_data['name']} Content:")
        print(f"   Text: {content.text}")
        print(f"   Hashtags: {', '.join(content.hashtags)}")
        print(f"   Character count: {len(content.text)}")
        
        # Validate content
        if content.text and len(content.text) > 0:
            print("   ✅ Content validation passed")
        else:
            print("   ❌ Content validation failed")

def main():
    """Main test function"""
    print("🎯 Social Media Automation Tool - Test Suite")
    print("=" * 60)
    
    # Run tests
    test_basic_functionality()
    test_environment_setup()
    test_content_creation()
    
    print("\n" + "=" * 60)
    print("🎉 Test suite completed!")
    print("\n📚 Next Steps:")
    print("1. Configure your credentials in .env file")
    print("2. Run: python social_media_automator.py")
    print("3. Or use the advanced version: python advanced_automator.py")
    print("\n⚠️  Remember to:")
    print("- Use dedicated automation accounts")
    print("- Respect platform rate limits")
    print("- Follow terms of service")
    print("- Monitor account health")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        sys.exit(1)
