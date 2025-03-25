"""
Console formatting utilities for the LinkedIn AI News Bot
"""

import os
import sys
import time
from datetime import datetime

# ANSI color codes
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Console:
    """Console formatting utilities for better terminal output"""
    
    @staticmethod
    def clear():
        """Clear the console"""
        # For Windows
        if os.name == 'nt':
            os.system('cls')
        # For Mac and Linux
        else:
            os.system('clear')
    
    @staticmethod
    def header(text):
        """Print a header in the console"""
        width = min(os.get_terminal_size().columns, 80)
        print("\n" + "=" * width)
        print(f"{Colors.HEADER}{Colors.BOLD}{text.center(width)}{Colors.ENDC}")
        print("=" * width)
    
    @staticmethod
    def section(text):
        """Print a section header in the console"""
        width = min(os.get_terminal_size().columns, 80)
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'-' * 4} {text} {'-' * (width - len(text) - 6)}{Colors.ENDC}")
    
    @staticmethod
    def info(text):
        """Print info message"""
        print(f"{Colors.CYAN}[INFO]{Colors.ENDC} {text}")
    
    @staticmethod
    def success(text):
        """Print success message"""
        print(f"{Colors.GREEN}[SUCCESS]{Colors.ENDC} {text}")
    
    @staticmethod
    def warning(text):
        """Print warning message"""
        print(f"{Colors.YELLOW}[WARNING]{Colors.ENDC} {text}")
    
    @staticmethod
    def error(text):
        """Print error message"""
        print(f"{Colors.RED}[ERROR]{Colors.ENDC} {text}")
    
    @staticmethod
    def debug(text):
        """Print debug message (only in verbose mode)"""
        if os.environ.get('DEBUG'):
            print(f"{Colors.BLUE}[DEBUG]{Colors.ENDC} {text}")
    
    @staticmethod
    def progress_bar(percent, width=50):
        """Print a progress bar"""
        filled_width = int(width * percent / 100)
        bar = '█' * filled_width + '░' * (width - filled_width)
        print(f"\r{Colors.BLUE}Progress: |{bar}| {percent:.1f}%{Colors.ENDC}", end='')
    
    @staticmethod
    def status_update(update_number, hours_left, minutes_left, percent_complete, current_time, target_time, context="Next post"):
        """Print a formatted status update"""
        width = min(os.get_terminal_size().columns, 80)
        filled = int((percent_complete / 100) * 40)  # 40-char progress bar
        bar = "█" * filled + "░" * (40 - filled)
        
        # Format time remaining
        if hours_left < 1:
            time_remaining = f"{int(minutes_left)} minutes"
        else:
            time_remaining = f"{int(hours_left)}h {int(minutes_left)}m"
        
        print("\n" + "━" * width)
        print(f"{Colors.BOLD}{Colors.YELLOW}STATUS UPDATE #{update_number}{Colors.ENDC}".center(width))
        print("━" * width)
        print(f"{Colors.CYAN}⏳ Waiting:{Colors.ENDC} {time_remaining} until {context}")
        print(f"{Colors.CYAN}🕒 Current time:{Colors.ENDC} {current_time}")
        print(f"{Colors.CYAN}🏁 Target time:{Colors.ENDC} {target_time}")
        print(f"{Colors.CYAN}📊 Progress:{Colors.ENDC} {percent_complete:.1f}% complete")
        print(f"\n{bar} {percent_complete:.1f}%\n")
        print("━" * width + "\n")
    
    @staticmethod
    def day_header(day_number, total_days):
        """Print a day header"""
        width = min(os.get_terminal_size().columns, 80)
        print("\n" + "═" * width)
        print(f"{Colors.BOLD}{Colors.GREEN}DAY {day_number} OF {total_days}{Colors.ENDC}".center(width))
        print("═" * width)
    
    @staticmethod
    def article_info(article):
        """Print article information in a formatted box"""
        width = min(os.get_terminal_size().columns, 80)
        title = article['title']
        source = article.get('source', 'Unknown source')
        score = article.get('relevance_score', 0)
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}SELECTED ARTICLE{Colors.ENDC}")
        print("┌" + "─" * (width - 2) + "┐")
        
        # Print title (with word wrapping)
        words = title.split()
        line = ""
        for word in words:
            if len(line + word) + 1 <= width - 6:  # -6 for margins and space
                line += word + " "
            else:
                print(f"│ {Colors.BOLD}{line.ljust(width - 6)}{Colors.ENDC} │")
                line = word + " "
        if line:
            print(f"│ {Colors.BOLD}{line.ljust(width - 6)}{Colors.ENDC} │")
        
        print("│" + " " * (width - 2) + "│")
        print(f"│ Source: {Colors.YELLOW}{source}{Colors.ENDC}{' ' * (width - 11 - len(source))}│")
        print(f"│ Score: {Colors.GREEN}{score:.1f}{Colors.ENDC}{' ' * (width - 10 - len(str(score)))}│")
        print("└" + "─" * (width - 2) + "┘")
    
    @staticmethod
    def app_banner():
        """Print application banner"""
        banner = """
 _     _       _        _ ___ _  _    _   ___    _  _                 ___      _   
| |   (_)_ _  | |___  _| |_ _| \| |  /_\ |_ _|  | \| |_____ __ ___ __| _ ) ___| |_ 
| |__ | | ' \ | / / || | || || .` | / _ \ | |   | .` / -_) V  V / '_ \ _ \/ _ \  _|
|____|/ |_||_|_\_\\_,_|_|___|_|\_|/_/ \_\___| |_|\_\___|\_/\_/| .__/___/\___/\__|
    |__/                                                      |_|                  
        """
        print(f"{Colors.CYAN}{banner}{Colors.ENDC}")
        print(f"{Colors.BOLD}AI-powered LinkedIn News Posting Bot{Colors.ENDC}".center(80))
        print("\n")