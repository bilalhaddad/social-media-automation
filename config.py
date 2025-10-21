"""
Configuration settings for social media automation
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for social media automation"""
    
    # LinkedIn credentials
    LINKEDIN_EMAIL = os.getenv('LINKEDIN_EMAIL')
    LINKEDIN_PASSWORD = os.getenv('LINKEDIN_PASSWORD')
    
    # Twitter credentials
    TWITTER_EMAIL = os.getenv('TWITTER_EMAIL')
    TWITTER_PASSWORD = os.getenv('TWITTER_PASSWORD')
    
    # Browser settings
    HEADLESS_MODE = os.getenv('HEADLESS_MODE', 'True').lower() == 'true'
    WAIT_TIMEOUT = int(os.getenv('WAIT_TIMEOUT', '10'))
    
    # Posting settings
    DEFAULT_HASHTAGS = [
        'AI', 'Automation', 'Tech', 'Innovation', 'Digital'
    ]
    
    # Rate limiting
    MIN_POST_INTERVAL = int(os.getenv('MIN_POST_INTERVAL', '300'))  # 5 minutes
    MAX_POSTS_PER_HOUR = int(os.getenv('MAX_POSTS_PER_HOUR', '5'))
    
    # File paths
    IMAGES_DIR = os.getenv('IMAGES_DIR', './images')
    LOGS_DIR = os.getenv('LOGS_DIR', './logs')
    
    # Social media platform URLs
    PLATFORM_URLS = {
        'linkedin': 'https://www.linkedin.com/feed/',
        'twitter': 'https://twitter.com/compose/tweet',
        'facebook': 'https://www.facebook.com/',
        'instagram': 'https://www.instagram.com/'
    }
    
    # XPath selectors for different platforms
    SELECTORS = {
        'linkedin': {
            'start_post_button': "//button[contains(@aria-label, 'Start a post')]",
            'post_modal': "//div[@class='ql-editor']",
            'post_button': "//button[contains(@aria-label, 'Post')]",
            'image_upload': "//button[@aria-label='Add an image']"
        },
        'twitter': {
            'tweet_box': "//div[@data-testid='tweetTextarea_0']",
            'tweet_button': "//button[@data-testid='tweetButton']",
            'image_upload': "//input[@data-testid='fileInput']"
        }
    }
