<<<<<<< HEAD
# Social Media Automation Tool

A comprehensive solution for automating social media posting to LinkedIn, Twitter, and other platforms without using APIs. This tool uses browser automation to simulate human interactions with social media platforms.

## 🚀 Features

- **Multi-Platform Support**: LinkedIn, Twitter, Facebook, Instagram
- **Browser Automation**: Uses Selenium and Playwright for reliable automation
- **Content Scheduling**: Schedule posts for specific times
- **Media Support**: Upload images and videos
- **Hashtag Management**: Automatic hashtag insertion
- **Rate Limiting**: Built-in protection against platform limits
- **Error Handling**: Robust error handling and logging
- **Queue Management**: Advanced post queue with status tracking

## 📋 Requirements

### Basic Version (Selenium)
- Python 3.8+
- Chrome/Chromium browser
- ChromeDriver

### Advanced Version (Playwright)
- Python 3.8+
- Playwright browsers

## 🛠️ Installation

### 1. Clone the repository
```bash
git clone <repository-url>
cd social-media-automation
```

### 2. Install dependencies

#### For Basic Version:
```bash
pip install -r requirements.txt
```

#### For Advanced Version:
```bash
pip install -r advanced_requirements.txt
playwright install chromium
```

### 3. Setup environment
```bash
cp env.example .env
# Edit .env with your credentials
```

## 🔧 Configuration

### Environment Variables
```env
# LinkedIn Credentials
LINKEDIN_EMAIL=your_linkedin_email@example.com
LINKEDIN_PASSWORD=your_linkedin_password

# Twitter Credentials
TWITTER_EMAIL=your_twitter_email@example.com
TWITTER_PASSWORD=your_twitter_password

# Browser Settings
HEADLESS_MODE=True
WAIT_TIMEOUT=10

# Posting Settings
MIN_POST_INTERVAL=300
MAX_POSTS_PER_HOUR=5
```

## 📖 Usage

### Basic Usage (Selenium)

```python
from social_media_automator import SocialMediaAutomator, PostContent

# Create automator
automator = SocialMediaAutomator(headless=True)
automator.setup_driver()

# Login to LinkedIn
automator.login_linkedin("your_email", "your_password")

# Create post content
content = PostContent(
    text="Check out our latest AI audit insights!",
    hashtags=["AI", "Audit", "Automation"],
    image_path="path/to/image.jpg"
)

# Post to LinkedIn
automator.post_to_linkedin(content)

# Close browser
automator.close()
```

### Advanced Usage (Playwright)

```python
import asyncio
from advanced_automator import AdvancedSocialMediaAutomator, PostContent

async def main():
    # Create automator
    automator = AdvancedSocialMediaAutomator(headless=True)
    await automator.setup()
    
    # Login to platforms
    await automator.login_linkedin("your_email", "your_password")
    
    # Create content
    content = PostContent(
        text="🚀 Exciting news! Our AI audit platform is live!",
        hashtags=["AI", "Automation", "Tech"],
        mentions=["yourcompany"],
        platform_specific={
            'linkedin': 'Check out our latest features!',
            'twitter': 'New automation features are live! 🎉'
        }
    )
    
    # Post to multiple platforms
    results = await automator.post_to_multiple_platforms(
        content, 
        ["linkedin", "twitter"]
    )
    
    print(f"Posting results: {results}")
    
    # Close browser
    await automator.close()

# Run the async function
asyncio.run(main())
```

### Content Scheduling

```python
from advanced_automator import ContentScheduler, PostContent
import asyncio

async def schedule_posts():
    scheduler = ContentScheduler()
    
    # Create content
    content = PostContent(
        text="Daily AI insights: Today we're exploring automation trends",
        hashtags=["AI", "DailyInsights", "Automation"]
    )
    
    # Schedule post for 2 hours from now
    await scheduler.add_post(content, ["linkedin", "twitter"], delay_minutes=120)
    
    # Process the queue
    await scheduler.process_queue()
    
    # Check status
    status = scheduler.get_queue_status()
    print(f"Queue status: {status}")

asyncio.run(schedule_posts())
```

## 🎯 Supported Platforms

### LinkedIn
- Text posts with hashtags
- Image uploads
- Video uploads
- Mentions and tags

### Twitter/X
- Text posts with hashtags
- Image uploads
- Mentions and replies

### Facebook (Coming Soon)
- Text posts
- Image uploads
- Video uploads

### Instagram (Coming Soon)
- Posts and stories
- Image and video uploads
- Hashtag optimization

## ⚠️ Important Considerations

### Platform Compliance
- **LinkedIn**: Strict automation policies - use responsibly
- **Twitter**: Rate limits apply - respect platform guidelines
- **General**: Always comply with platform terms of service

### Best Practices
1. **Rate Limiting**: Don't post too frequently
2. **Human-like Behavior**: Add random delays between actions
3. **Account Safety**: Use dedicated accounts for automation
4. **Content Quality**: Ensure high-quality, relevant content
5. **Monitoring**: Regularly check for account restrictions

### Legal Considerations
- Respect platform terms of service
- Don't spam or post irrelevant content
- Maintain account authenticity
- Follow local laws and regulations

## 🔒 Security

- Store credentials securely in environment variables
- Use dedicated automation accounts
- Regularly rotate passwords
- Monitor account activity
- Implement proper error handling

## 🐛 Troubleshooting

### Common Issues

1. **Login Failures**
   - Check credentials
   - Verify 2FA settings
   - Check for CAPTCHA requirements

2. **Posting Failures**
   - Verify platform selectors
   - Check for rate limits
   - Ensure content meets platform guidelines

3. **Browser Issues**
   - Update browser drivers
   - Check for browser updates
   - Verify headless mode compatibility

### Debug Mode
```python
# Run in non-headless mode for debugging
automator = SocialMediaAutomator(headless=False)
```

## 📊 Monitoring and Analytics

The tool includes built-in logging and monitoring:

```python
import logging

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automation.log'),
        logging.StreamHandler()
    ]
)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This tool is for educational and legitimate business purposes only. Users are responsible for:
- Complying with platform terms of service
- Following applicable laws and regulations
- Using the tool ethically and responsibly
- Monitoring their accounts for any issues

The authors are not responsible for any account restrictions, bans, or other consequences resulting from the use of this tool.
=======
# social-media-automation
>>>>>>> a4d01aaed593b59885f86b6e776f1ae8043c0271
