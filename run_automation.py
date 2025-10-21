#!/usr/bin/env python3
"""
Main Runner Script for Social Media Automation Tool
This script provides easy access to all automation features
"""

import os
import sys
import subprocess
from datetime import datetime

def show_menu():
    """Show main menu"""
    print("🚀 Social Media Automation Tool")
    print("=" * 50)
    print("Choose an option:")
    print()
    print("📋 DEMO & TESTING:")
    print("  1. Run demo (no real posting)")
    print("  2. Run test suite")
    print("  3. Check environment setup")
    print()
    print("🔧 AUTOMATION:")
    print("  4. Run basic automation")
    print("  5. Run advanced automation (Playwright)")
    print("  6. Interactive demo with real credentials")
    print()
    print("📚 DOCUMENTATION:")
    print("  7. Show usage examples")
    print("  8. View README")
    print("  9. View implementation guide")
    print()
    print("  0. Exit")
    print()

def run_demo():
    """Run the demo script"""
    print("🎯 Running demo...")
    subprocess.run([sys.executable, "demo.py"])

def run_test_suite():
    """Run the test suite"""
    print("🧪 Running test suite...")
    subprocess.run([sys.executable, "test_automation.py"])

def check_environment():
    """Check environment setup"""
    print("🔍 Checking environment setup...")
    
    # Check if .env exists
    if os.path.exists('.env'):
        print("✅ .env file found")
    else:
        print("⚠️  .env file not found")
        print("   Creating from template...")
        if os.path.exists('env.example'):
            subprocess.run(['cp', 'env.example', '.env'])
            print("✅ Created .env file from template")
            print("📝 Please edit .env file with your credentials")
        else:
            print("❌ env.example file not found")
    
    # Check Chrome
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
    
    # Check Python packages
    try:
        import selenium
        print(f"✅ Selenium {selenium.__version__} installed")
    except ImportError:
        print("❌ Selenium not installed")
        print("   Run: pip install -r requirements.txt")
    
    try:
        import playwright
        print(f"✅ Playwright installed")
    except ImportError:
        print("⚠️  Playwright not installed")
        print("   Run: pip install -r advanced_requirements.txt")

def run_basic_automation():
    """Run basic automation"""
    print("🔧 Running basic automation...")
    print("⚠️  Make sure you have configured credentials in .env file")
    
    # Check if .env exists
    if not os.path.exists('.env'):
        print("❌ .env file not found. Please configure credentials first.")
        return
    
    # Load credentials
    from dotenv import load_dotenv
    load_dotenv()
    
    linkedin_email = os.getenv('LINKEDIN_EMAIL')
    linkedin_password = os.getenv('LINKEDIN_PASSWORD')
    
    if not linkedin_email or not linkedin_password:
        print("❌ LinkedIn credentials not found in .env file")
        print("   Please add LINKEDIN_EMAIL and LINKEDIN_PASSWORD to .env")
        return
    
    # Run automation
    print("🚀 Starting automation...")
    subprocess.run([sys.executable, "social_media_automator.py"])

def run_advanced_automation():
    """Run advanced automation"""
    print("🚀 Running advanced automation...")
    print("⚠️  Make sure you have configured credentials in .env file")
    
    # Check if .env exists
    if not os.path.exists('.env'):
        print("❌ .env file not found. Please configure credentials first.")
        return
    
    # Run automation
    print("🚀 Starting advanced automation...")
    subprocess.run([sys.executable, "advanced_automator.py"])

def run_interactive_demo():
    """Run interactive demo"""
    print("🎮 Running interactive demo...")
    subprocess.run([sys.executable, "interactive_demo.py"])

def show_usage_examples():
    """Show usage examples"""
    print("📚 Usage Examples:")
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

def view_readme():
    """View README"""
    print("📖 Opening README...")
    if os.path.exists('README.md'):
        subprocess.run(['cat', 'README.md'])
    else:
        print("❌ README.md not found")

def view_implementation_guide():
    """View implementation guide"""
    print("📖 Opening implementation guide...")
    if os.path.exists('implementation_guide.md'):
        subprocess.run(['cat', 'implementation_guide.md'])
    else:
        print("❌ implementation_guide.md not found")

def main():
    """Main function"""
    while True:
        show_menu()
        
        try:
            choice = input("Enter your choice (0-9): ").strip()
            
            if choice == '0':
                print("👋 Goodbye!")
                break
            elif choice == '1':
                run_demo()
            elif choice == '2':
                run_test_suite()
            elif choice == '3':
                check_environment()
            elif choice == '4':
                run_basic_automation()
            elif choice == '5':
                run_advanced_automation()
            elif choice == '6':
                run_interactive_demo()
            elif choice == '7':
                show_usage_examples()
            elif choice == '8':
                view_readme()
            elif choice == '9':
                view_implementation_guide()
            else:
                print("❌ Invalid choice. Please try again.")
            
            if choice != '0':
                input("\nPress Enter to continue...")
                print("\n" + "=" * 50)
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            input("Press Enter to continue...")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        sys.exit(1)
