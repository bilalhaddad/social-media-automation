#!/usr/bin/env python3
"""
Social Media Automation Tool
Automates posting to LinkedIn and other social media platforms without APIs
"""

import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import schedule

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class PostContent:
    """Data class for post content"""
    text: str
    image_path: Optional[str] = None
    hashtags: List[str] = None
    scheduled_time: Optional[datetime] = None
    
    def __post_init__(self):
        if self.hashtags is None:
            self.hashtags = []

class SocialMediaAutomator:
    """Main class for social media automation"""
    
    def __init__(self, headless: bool = True):
        self.driver = None
        self.headless = headless
        self.wait_timeout = 10
        
    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # Additional options for better automation
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User agent to appear more like a real user
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def login_linkedin(self, email: str, password: str) -> bool:
        """Login to LinkedIn"""
        try:
            print(f"🌐 Navigating to LinkedIn login page...")
            self.driver.get("https://www.linkedin.com/login")
            
            # Wait for login form
            print("⏳ Waiting for login form...")
            email_field = WebDriverWait(self.driver, self.wait_timeout).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            password_field = self.driver.find_element(By.ID, "password")
            
            # Enter credentials
            print("📝 Entering credentials...")
            email_field.clear()
            email_field.send_keys(email)
            password_field.clear()
            password_field.send_keys(password)
            
            # Click login button
            print("🔐 Clicking login button...")
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Wait for successful login (check for feed or profile)
            print("⏳ Waiting for login confirmation...")
            WebDriverWait(self.driver, self.wait_timeout).until(
                lambda driver: "feed" in driver.current_url or "mynetwork" in driver.current_url or "challenge" in driver.current_url
            )
            
            # Check if we hit a challenge (2FA, captcha, etc.)
            if "challenge" in self.driver.current_url:
                print("⚠️  LinkedIn challenge detected (2FA, captcha, etc.)")
                print("   Manual intervention may be required")
                return False
            
            logger.info("Successfully logged into LinkedIn")
            return True
            
        except TimeoutException:
            logger.error("LinkedIn login failed - timeout")
            print("❌ Login timeout - LinkedIn may have changed their interface")
            return False
        except Exception as e:
            logger.error(f"LinkedIn login failed: {str(e)}")
            print(f"❌ Login error: {str(e)}")
            return False
    
    def post_to_linkedin(self, content: PostContent) -> bool:
        """Post content to LinkedIn"""
        try:
            print("🌐 Navigating to LinkedIn feed...")
            # Navigate to LinkedIn feed
            self.driver.get("https://www.linkedin.com/feed/")
            
            # Wait for the "Start a post" button
            print("⏳ Looking for 'Start a post' button...")
            start_post_button = WebDriverWait(self.driver, self.wait_timeout).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Start a post')]"))
            )
            start_post_button.click()
            
            # Wait for the post modal
            print("⏳ Waiting for post composer...")
            post_modal = WebDriverWait(self.driver, self.wait_timeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, "ql-editor"))
            )
            
            # Enter post text
            print("📝 Entering post text...")
            post_modal.send_keys(content.text)
            
            # Add hashtags if provided
            if content.hashtags:
                hashtag_text = " ".join([f"#{tag}" for tag in content.hashtags])
                print(f"🏷️  Adding hashtags: {hashtag_text}")
                post_modal.send_keys(f" {hashtag_text}")
            
            # Handle image upload if provided
            if content.image_path:
                print("📷 Uploading image...")
                self._upload_image_linkedin(content.image_path)
            
            # Click post button
            print("📤 Clicking post button...")
            post_button = WebDriverWait(self.driver, self.wait_timeout).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Post')]"))
            )
            post_button.click()
            
            # Wait for post to be submitted
            print("⏳ Waiting for post submission...")
            time.sleep(3)
            
            logger.info("Successfully posted to LinkedIn")
            print("✅ LinkedIn post successful!")
            return True
            
        except TimeoutException:
            logger.error("LinkedIn posting failed - timeout")
            print("❌ LinkedIn posting timeout - interface may have changed")
            return False
        except Exception as e:
            logger.error(f"LinkedIn posting failed: {str(e)}")
            print(f"❌ LinkedIn posting error: {str(e)}")
            return False
    
    def _upload_image_linkedin(self, image_path: str):
        """Upload image to LinkedIn post"""
        try:
            # Find and click the image upload button
            image_button = self.driver.find_element(By.XPATH, "//button[@aria-label='Add an image']")
            image_button.click()
            
            # Find file input and upload image
            file_input = self.driver.find_element(By.XPATH, "//input[@type='file']")
            file_input.send_keys(image_path)
            
            # Wait for image to upload
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Image upload failed: {str(e)}")
    
    def post_to_twitter(self, content: PostContent) -> bool:
        """Post content to Twitter/X"""
        try:
            self.driver.get("https://twitter.com/compose/tweet")
            
            # Wait for tweet composer
            tweet_box = WebDriverWait(self.driver, self.wait_timeout).until(
                EC.presence_of_element_located((By.XPATH, "//div[@data-testid='tweetTextarea_0']"))
            )
            
            # Enter tweet text
            tweet_box.send_keys(content.text)
            
            # Add hashtags if provided
            if content.hashtags:
                hashtag_text = " ".join([f"#{tag}" for tag in content.hashtags])
                tweet_box.send_keys(f" {hashtag_text}")
            
            # Click tweet button
            tweet_button = WebDriverWait(self.driver, self.wait_timeout).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='tweetButton']"))
            )
            tweet_button.click()
            
            time.sleep(2)
            logger.info("Successfully posted to Twitter")
            return True
            
        except Exception as e:
            logger.error(f"Twitter posting failed: {str(e)}")
            return False
    
    def schedule_post(self, content: PostContent, platforms: List[str], delay_minutes: int = 0):
        """Schedule a post for later"""
        if delay_minutes > 0:
            time.sleep(delay_minutes * 60)
        
        for platform in platforms:
            if platform.lower() == "linkedin":
                self.post_to_linkedin(content)
            elif platform.lower() == "twitter":
                self.post_to_twitter(content)
            else:
                logger.warning(f"Platform {platform} not supported")
    
    def close(self):
        """Close the browser driver"""
        if self.driver:
            self.driver.quit()

class PostScheduler:
    """Schedule and manage social media posts"""
    
    def __init__(self):
        self.automator = SocialMediaAutomator()
        self.scheduled_posts = []
    
    def add_post(self, content: PostContent, platforms: List[str], delay_minutes: int = 0):
        """Add a post to the schedule"""
        self.scheduled_posts.append({
            'content': content,
            'platforms': platforms,
            'delay_minutes': delay_minutes
        })
    
    def run_scheduled_posts(self):
        """Execute all scheduled posts"""
        self.automator.setup_driver()
        
        try:
            for post_data in self.scheduled_posts:
                self.automator.schedule_post(
                    post_data['content'],
                    post_data['platforms'],
                    post_data['delay_minutes']
                )
        finally:
            self.automator.close()

def main():
    """Example usage with demo mode"""
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Check if credentials are configured
    linkedin_email = os.getenv('LINKEDIN_EMAIL', '')
    linkedin_password = os.getenv('LINKEDIN_PASSWORD', '')
    
    # Check if using demo credentials
    if 'your_linkedin_email@example.com' in linkedin_email or not linkedin_email:
        print("🎯 Running in DEMO MODE - No real posting will occur")
        print("=" * 60)
        print("📝 To use with real platforms:")
        print("1. Edit .env file with your actual credentials")
        print("2. Run this script again")
        print()
        
        # Demo mode - just show what would happen
        content = PostContent(
            text="🚀 Demo: Check out our latest AI audit insights! This would be posted to social media platforms.",
            hashtags=["AI", "Audit", "Automation", "Tech", "Demo"],
            image_path=None
        )
        
        print("📝 Demo Content Created:")
        print(f"   Text: {content.text}")
        print(f"   Hashtags: {', '.join(content.hashtags)}")
        print()
        print("✅ Demo completed successfully!")
        print("   The automation tool is ready for real use with proper credentials.")
        return
    
    # Real mode - attempt actual posting
    print("🚀 Social Media Automation - REAL MODE")
    print("=" * 50)
    
    # Create post content
    content = PostContent(
        text="Check out our latest AI audit insights! #AI #Audit #Automation",
        hashtags=["AI", "Audit", "Automation", "Tech"],
        image_path=None  # Optional: path to image file
    )
    
    print(f"📝 Posting content:")
    print(f"   Text: {content.text}")
    print(f"   Hashtags: {', '.join(content.hashtags)}")
    
    # Create automator
    automator = SocialMediaAutomator(headless=True)
    
    try:
        automator.setup_driver()
        print("✅ Browser setup successful")
        
        # Try LinkedIn login and posting
        print("\n🔗 Attempting LinkedIn login...")
        if automator.login_linkedin(linkedin_email, linkedin_password):
            print("✅ LinkedIn login successful")
            print("📤 Posting to LinkedIn...")
            if automator.post_to_linkedin(content):
                print("✅ LinkedIn post successful!")
            else:
                print("❌ LinkedIn post failed")
        else:
            print("❌ LinkedIn login failed")
        
        # Try Twitter (if credentials available)
        twitter_email = os.getenv('TWITTER_EMAIL', '')
        twitter_password = os.getenv('TWITTER_PASSWORD', '')
        
        if twitter_email and twitter_password and 'your_twitter_email@example.com' not in twitter_email:
            print("\n🐦 Attempting Twitter posting...")
            if automator.post_to_twitter(content):
                print("✅ Twitter post successful!")
            else:
                print("❌ Twitter post failed")
        
    except Exception as e:
        print(f"❌ Automation failed: {str(e)}")
        
    finally:
        automator.close()
        print("\n🧹 Cleanup completed")

if __name__ == "__main__":
    main()
