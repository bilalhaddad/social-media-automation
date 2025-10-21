#!/usr/bin/env python3
"""
Advanced Social Media Automation with Playwright
More reliable and faster than Selenium
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from playwright.async_api import async_playwright, Browser, Page
import schedule
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class PostContent:
    """Enhanced post content with more options"""
    text: str
    image_path: Optional[str] = None
    video_path: Optional[str] = None
    hashtags: List[str] = None
    mentions: List[str] = None
    scheduled_time: Optional[datetime] = None
    platform_specific: Dict[str, str] = None
    
    def __post_init__(self):
        if self.hashtags is None:
            self.hashtags = []
        if self.mentions is None:
            self.mentions = []
        if self.platform_specific is None:
            self.platform_specific = {}

class AdvancedSocialMediaAutomator:
    """Advanced social media automation using Playwright"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.context = None
        self.pages = {}
        
    async def setup(self):
        """Setup Playwright browser"""
        self.playwright = await async_playwright().start()
        
        # Browser options
        browser_options = {
            'headless': self.headless,
            'args': [
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled'
            ]
        }
        
        self.browser = await self.playwright.chromium.launch(**browser_options)
        
        # Create context with realistic user agent
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        
    async def login_linkedin(self, email: str, password: str) -> bool:
        """Login to LinkedIn with enhanced error handling"""
        try:
            page = await self.context.new_page()
            self.pages['linkedin'] = page
            
            await page.goto("https://www.linkedin.com/login")
            
            # Wait for login form
            await page.wait_for_selector("#username", timeout=10000)
            
            # Fill credentials
            await page.fill("#username", email)
            await page.fill("#password", password)
            
            # Click login
            await page.click("button[type='submit']")
            
            # Wait for successful login
            await page.wait_for_url("**/feed/**", timeout=15000)
            
            logger.info("Successfully logged into LinkedIn")
            return True
            
        except Exception as e:
            logger.error(f"LinkedIn login failed: {str(e)}")
            return False
    
    async def post_to_linkedin(self, content: PostContent) -> bool:
        """Enhanced LinkedIn posting with better error handling"""
        try:
            page = self.pages.get('linkedin')
            if not page:
                logger.error("LinkedIn page not available")
                return False
            
            await page.goto("https://www.linkedin.com/feed/")
            
            # Wait for start post button
            await page.wait_for_selector("button[aria-label*='Start a post']", timeout=10000)
            await page.click("button[aria-label*='Start a post']")
            
            # Wait for post modal
            await page.wait_for_selector(".ql-editor", timeout=10000)
            
            # Build post text
            post_text = content.text
            
            # Add hashtags
            if content.hashtags:
                hashtag_text = " ".join([f"#{tag}" for tag in content.hashtags])
                post_text += f" {hashtag_text}"
            
            # Add mentions
            if content.mentions:
                mention_text = " ".join([f"@{mention}" for mention in content.mentions])
                post_text += f" {mention_text}"
            
            # Add platform-specific content
            if 'linkedin' in content.platform_specific:
                post_text += f" {content.platform_specific['linkedin']}"
            
            # Enter post text
            await page.fill(".ql-editor", post_text)
            
            # Handle image upload
            if content.image_path:
                await self._upload_image_linkedin(page, content.image_path)
            
            # Handle video upload
            if content.video_path:
                await self._upload_video_linkedin(page, content.video_path)
            
            # Post the content
            await page.click("button[aria-label*='Post']")
            
            # Wait for post confirmation
            await page.wait_for_timeout(3000)
            
            logger.info("Successfully posted to LinkedIn")
            return True
            
        except Exception as e:
            logger.error(f"LinkedIn posting failed: {str(e)}")
            return False
    
    async def _upload_image_linkedin(self, page: Page, image_path: str):
        """Upload image to LinkedIn post"""
        try:
            # Click image upload button
            await page.click("button[aria-label='Add an image']")
            
            # Wait for file input and upload
            async with page.expect_file_chooser() as fc_info:
                await page.click("button[aria-label='Add an image']")
            file_chooser = await fc_info.value
            await file_chooser.set_files(image_path)
            
            # Wait for upload to complete
            await page.wait_for_timeout(2000)
            
        except Exception as e:
            logger.error(f"Image upload failed: {str(e)}")
    
    async def _upload_video_linkedin(self, page: Page, video_path: str):
        """Upload video to LinkedIn post"""
        try:
            # Click video upload button
            await page.click("button[aria-label='Add a video']")
            
            # Wait for file input and upload
            async with page.expect_file_chooser() as fc_info:
                await page.click("button[aria-label='Add a video']")
            file_chooser = await fc_info.value
            await file_chooser.set_files(video_path)
            
            # Wait for upload to complete
            await page.wait_for_timeout(5000)
            
        except Exception as e:
            logger.error(f"Video upload failed: {str(e)}")
    
    async def post_to_twitter(self, content: PostContent) -> bool:
        """Enhanced Twitter posting"""
        try:
            page = await self.context.new_page()
            await page.goto("https://twitter.com/compose/tweet")
            
            # Wait for tweet composer
            await page.wait_for_selector("[data-testid='tweetTextarea_0']", timeout=10000)
            
            # Build tweet text
            tweet_text = content.text
            
            # Add hashtags
            if content.hashtags:
                hashtag_text = " ".join([f"#{tag}" for tag in content.hashtags])
                tweet_text += f" {hashtag_text}"
            
            # Add mentions
            if content.mentions:
                mention_text = " ".join([f"@{mention}" for mention in content.mentions])
                tweet_text += f" {mention_text}"
            
            # Enter tweet text
            await page.fill("[data-testid='tweetTextarea_0']", tweet_text)
            
            # Handle image upload
            if content.image_path:
                await self._upload_image_twitter(page, content.image_path)
            
            # Post tweet
            await page.click("[data-testid='tweetButton']")
            
            # Wait for post confirmation
            await page.wait_for_timeout(2000)
            
            logger.info("Successfully posted to Twitter")
            return True
            
        except Exception as e:
            logger.error(f"Twitter posting failed: {str(e)}")
            return False
    
    async def _upload_image_twitter(self, page: Page, image_path: str):
        """Upload image to Twitter"""
        try:
            # Click media upload button
            await page.click("[data-testid='fileInput']")
            
            # Upload file
            async with page.expect_file_chooser() as fc_info:
                await page.click("[data-testid='fileInput']")
            file_chooser = await fc_info.value
            await file_chooser.set_files(image_path)
            
            # Wait for upload
            await page.wait_for_timeout(2000)
            
        except Exception as e:
            logger.error(f"Twitter image upload failed: {str(e)}")
    
    async def post_to_multiple_platforms(self, content: PostContent, platforms: List[str]) -> Dict[str, bool]:
        """Post to multiple platforms simultaneously"""
        results = {}
        
        tasks = []
        for platform in platforms:
            if platform.lower() == "linkedin":
                tasks.append(self.post_to_linkedin(content))
            elif platform.lower() == "twitter":
                tasks.append(self.post_to_twitter(content))
        
        # Execute posts concurrently
        if tasks:
            results_list = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, platform in enumerate(platforms):
                if i < len(results_list):
                    results[platform] = not isinstance(results_list[i], Exception)
                else:
                    results[platform] = False
        
        return results
    
    async def close(self):
        """Close browser and cleanup"""
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()

class ContentScheduler:
    """Advanced content scheduling with queue management"""
    
    def __init__(self):
        self.automator = AdvancedSocialMediaAutomator()
        self.post_queue = []
        self.post_history = []
        
    async def add_post(self, content: PostContent, platforms: List[str], delay_minutes: int = 0):
        """Add post to queue"""
        scheduled_time = datetime.now() + timedelta(minutes=delay_minutes)
        
        post_data = {
            'content': content,
            'platforms': platforms,
            'scheduled_time': scheduled_time,
            'status': 'pending'
        }
        
        self.post_queue.append(post_data)
        logger.info(f"Added post to queue for {scheduled_time}")
    
    async def process_queue(self):
        """Process all pending posts"""
        await self.automator.setup()
        
        try:
            # Login to platforms
            # Note: You'll need to implement login methods for each platform
            
            current_time = datetime.now()
            
            for post_data in self.post_queue:
                if post_data['status'] == 'pending' and post_data['scheduled_time'] <= current_time:
                    try:
                        results = await self.automator.post_to_multiple_platforms(
                            post_data['content'],
                            post_data['platforms']
                        )
                        
                        post_data['status'] = 'completed'
                        post_data['results'] = results
                        self.post_history.append(post_data)
                        
                        logger.info(f"Posted to platforms: {results}")
                        
                    except Exception as e:
                        post_data['status'] = 'failed'
                        post_data['error'] = str(e)
                        logger.error(f"Post failed: {str(e)}")
                        
        finally:
            await self.automator.close()
    
    def get_queue_status(self) -> Dict:
        """Get current queue status"""
        return {
            'pending': len([p for p in self.post_queue if p['status'] == 'pending']),
            'completed': len([p for p in self.post_queue if p['status'] == 'completed']),
            'failed': len([p for p in self.post_queue if p['status'] == 'failed']),
            'total': len(self.post_queue)
        }

async def main():
    """Example usage"""
    # Create content
    content = PostContent(
        text="🚀 Exciting news! Our AI audit platform now supports automated social media posting!",
        hashtags=["AI", "Automation", "Tech", "Innovation"],
        mentions=["yourcompany"],
        platform_specific={
            'linkedin': 'Check out our latest features!',
            'twitter': 'New automation features are live! 🎉'
        }
    )
    
    # Create scheduler
    scheduler = ContentScheduler()
    
    # Add posts to queue
    await scheduler.add_post(content, ["linkedin", "twitter"], delay_minutes=0)
    
    # Process queue
    await scheduler.process_queue()
    
    # Check status
    status = scheduler.get_queue_status()
    print(f"Queue status: {status}")

if __name__ == "__main__":
    asyncio.run(main())
