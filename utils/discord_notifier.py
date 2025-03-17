"""
Discord notification module for the LinkedIn AI News Bot
"""

import os
import requests

class DiscordNotifier:
    """Class for sending notifications to Discord"""
    
    def __init__(self, webhook_url=None):
        """Initialize with webhook URL"""
        self.webhook_url = webhook_url or os.environ.get('DISCORD_WEBHOOK_URL')
        self.enabled = bool(self.webhook_url)
        
        if not self.enabled:
            print("Discord notifications disabled (no webhook URL provided)")
    
    def send_notification(self, message):
        """Send a notification to Discord using webhook"""
        if not self.enabled:
            print("Discord notification skipped (not enabled)")
            return False
        
        try:
            data = {"content": message}
            response = requests.post(self.webhook_url, json=data)
            if response.status_code == 204:
                print("Discord notification sent successfully")
                return True
            else:
                print(f"Failed to send Discord notification: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        except Exception as e:
            print(f"Error sending Discord notification: {str(e)}")
            return False
    
    def send_post_success(self, article_title, quality_score, post_time):
        """Send notification about successful post"""
        message = f"✅ LinkedIn Post Success!\n\n**Article:** {article_title}\n**Quality Score:** {quality_score}/9\n**Posted at:** {post_time}"
        return self.send_notification(message)
    
    def send_post_failure(self, article_title, failure_time):
        """Send notification about failed post"""
        message = f"❌ LinkedIn Post Failed!\n\n**Article:** {article_title}\n**Failed at:** {failure_time}"
        return self.send_notification(message)
    
    def send_bot_started(self, days):
        """Send notification about bot startup"""
        message = f"🤖 LinkedIn AI News Bot started for {days} days"
        return self.send_notification(message)
    
    def send_schedule_update(self, day, hours, scheduled_time):
        """Send notification about post scheduling"""
        message = f"📅 Post Scheduled\n\nDay {day}: Will post in {hours:.1f} hours\nScheduled time: {scheduled_time}"
        return self.send_notification(message)
    
    def send_day_complete(self, day, hours_until_next, next_day_time):
        """Send notification about day completion"""
        message = f"🔄 Day {day} Complete\n\nWaiting {hours_until_next:.1f} hours until day {day+1}\nNext day begins at: {next_day_time}"
        return self.send_notification(message)
    
    def send_analytics(self, analytics_data):
        """Send analytics data"""
        analytics_message = "📊 **LinkedIn AI News Bot Analytics**\n\n"
        for key, value in analytics_data.items():
            analytics_message += f"**{key}**: {value}\n"
        
        return self.send_notification(analytics_message)
    
    def send_status_update(self, update_number, hours_left, minutes_left, percent_complete, current_time, target_time, context="Next post"):
        """Send a status update notification with progress information
        
        Args:
            update_number (int): The number of this update in sequence
            hours_left (int/float): Hours remaining until event
            minutes_left (int/float): Minutes remaining (fraction of hour)
            percent_complete (float): Percentage of waiting completed (0-100)
            current_time (str): Current time as formatted string
            target_time (str): Target completion time as formatted string
            context (str): Context of what we're waiting for (e.g., "Next post" or "Day 3")
        
        Returns:
            bool: Success status of notification
        """
        # Create progress bar using block characters
        progress_bar_length = 20
        filled_blocks = int((percent_complete / 100) * progress_bar_length)
        empty_blocks = progress_bar_length - filled_blocks
        progress_bar = "█" * filled_blocks + "░" * empty_blocks
        
        # Format the time remaining in a readable way
        if hours_left < 1:
            time_remaining = f"{int(minutes_left)} minutes"
        else:
            time_remaining = f"{int(hours_left)}h {int(minutes_left)}m"
        
        message = (
            f"⏱️ **Status Update #{update_number}**\n\n"
            f"⏳ Waiting: {time_remaining} until {context}\n"
            f"🕒 Current time: `{current_time}`\n"
            f"🏁 Target time: `{target_time}`\n"
            f"📊 Progress: `{percent_complete:.1f}%` complete\n"
            f"```\n{progress_bar} {percent_complete:.1f}%\n```"
        )
        
        return self.send_notification(message)