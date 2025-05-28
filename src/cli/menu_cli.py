"""
Main CLI Interface for Arcadia Platform
Provides terminal-based user interface with colorful ASCII art and intuitive navigation
"""
import uuid
import time
import os
import sys
from typing import Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import track
from rich import print as rprint
from colorama import init, Fore, Back, Style

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__))))
from services.auth_service import auth_service, AuthenticationError
from services.game_service import game_service, InsufficientTokensError, GameNotFoundError
from models.database import User

class ArcadiaTerminal:
    """
    Main terminal interface for Arcadia Platform
    Implements the classic arcade aesthetic in terminal form
    """
    
    def __init__(self):
        self.console = Console()
        self.current_user: Optional[User] = None
        self.current_token: Optional[str] = None
        self.running = True
    
    def clear_screen(self):
        """Clear the terminal screen"""
        import subprocess
        import sys
        try:
            if os.name == 'nt':
                subprocess.run(['cls'], shell=True, check=True)
            else:
                subprocess.run(['clear'], check=True)
        except subprocess.CalledProcessError:
            # Fallback to printing newlines if clear command fails
            print('\n' * 50)
    
    def print_logo(self):
        """Print the Arcadia logo in ASCII art"""
        logo = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║     {Fore.YELLOW}█████╗ {Fore.MAGENTA}██████╗  {Fore.CYAN}██████╗ {Fore.GREEN}█████╗ {Fore.RED}██████╗ {Fore.BLUE}██╗ {Fore.YELLOW}█████╗                     ║
║    {Fore.YELLOW}██╔══██╗{Fore.MAGENTA}██╔══██╗{Fore.CYAN}██╔════╝{Fore.GREEN}██╔══██╗{Fore.RED}██╔══██╗{Fore.BLUE}██║{Fore.YELLOW}██╔══██╗                    ║
║    {Fore.YELLOW}███████║{Fore.MAGENTA}██████╔╝{Fore.CYAN}██║     {Fore.GREEN}███████║{Fore.RED}██║  ██║{Fore.BLUE}██║{Fore.YELLOW}███████║                    ║
║    {Fore.YELLOW}██╔══██║{Fore.MAGENTA}██╔══██╗{Fore.CYAN}██║     {Fore.GREEN}██╔══██║{Fore.RED}██║  ██║{Fore.BLUE}██║{Fore.YELLOW}██╔══██║                    ║
║    {Fore.YELLOW}██║  ██║{Fore.MAGENTA}██║  ██║{Fore.CYAN}╚██████╗{Fore.GREEN}██║  ██║{Fore.RED}██████╔╝{Fore.BLUE}██║{Fore.YELLOW}██║  ██║                    ║
║    {Fore.YELLOW}╚═╝  ╚═╝{Fore.MAGENTA}╚═╝  ╚═╝{Fore.CYAN} ╚═════╝{Fore.GREEN}╚═╝  ╚═╝{Fore.RED}╚═════╝ {Fore.BLUE}╚═╝{Fore.YELLOW}╚═╝  ╚═╝                    ║
║                                                                              ║
║                    {Fore.WHITE}{Style.BRIGHT}🎮 ONLINE ARCADE PLATFORM 🎮{Style.RESET_ALL}                          ║
║                  {Fore.CYAN}Relive the 80s Arcade Experience{Style.RESET_ALL}                        ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
        print(logo)
    
    def print_status_bar(self):
        """Print current user status"""
        if self.current_user:
            status = f"""
{Fore.GREEN}┌─────────────────────────────────────────────────────────────────────┐
│ {Fore.YELLOW}👤 User: {self.current_user.username:<20} {Fore.CYAN}🪙 Tokens: {self.current_user.tokens:<10} {Fore.MAGENTA}📅 Online{Fore.GREEN} │
└─────────────────────────────────────────────────────────────────────┘{Style.RESET_ALL}
"""
        else:
            status = f"""
{Fore.RED}┌─────────────────────────────────────────────────────────────────────┐
│ {Fore.WHITE}Not logged in - Please register or login to access games{Fore.RED}        │
└─────────────────────────────────────────────────────────────────────┘{Style.RESET_ALL}
"""
        print(status)
    
    def get_input(self, prompt: str, password: bool = False) -> str:
        """Get user input with styling"""
        if password:
            import getpass
            return getpass.getpass(f"{Fore.CYAN}🔐 {prompt}: {Style.RESET_ALL}")
        else:
            return input(f"{Fore.CYAN}➤ {prompt}: {Style.RESET_ALL}")
    
    def print_menu(self, title: str, options: list, subtitle: str = ""):
        """Print a styled menu"""
        print(f"\n{Fore.YELLOW}╔{'═' * (len(title) + 4)}╗")
        print(f"║ {title} ║")
        print(f"╚{'═' * (len(title) + 4)}╝{Style.RESET_ALL}")
        
        if subtitle:
            print(f"{Fore.CYAN}{subtitle}{Style.RESET_ALL}\n")
        
        for i, option in enumerate(options, 1):
            print(f"{Fore.WHITE}{i}. {option}{Style.RESET_ALL}")
    
    def show_welcome_screen(self):
        """Show the main welcome screen"""
        self.clear_screen()
        self.print_logo()
        print(f"{Fore.CYAN}Welcome to Arcadia - The ultimate retro arcade experience!")
        print(f"Experience classic games, compete on leaderboards, and create your own arcade games!{Style.RESET_ALL}\n")
    
    def login_menu(self):
        """Handle user login"""
        self.clear_screen()
        self.print_logo()
        print(f"{Fore.YELLOW}🔑 LOGIN TO ARCADIA{Style.RESET_ALL}")
        
        try:
            email = self.get_input("Email")
            password = self.get_input("Password", password=True)
            
            print(f"\n{Fore.YELLOW}Authenticating...{Style.RESET_ALL}")
            success, message, token, user = auth_service.authenticate_user(email, password)
            
            if success:
                self.current_user = user
                self.current_token = token
                print(f"{Fore.GREEN}✅ {message}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}Welcome back, {user.username}! 🎮{Style.RESET_ALL}")
                time.sleep(2)
                return True
            else:
                print(f"{Fore.RED}❌ {message}{Style.RESET_ALL}")
                input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
                return False
                
        except Exception as e:
            print(f"{Fore.RED}❌ Login failed: {str(e)}{Style.RESET_ALL}")
            input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
            return False
    
    def register_menu(self):
        """Handle user registration"""
        self.clear_screen()
        self.print_logo()
        print(f"{Fore.YELLOW}📝 REGISTER FOR ARCADIA{Style.RESET_ALL}")
        
        try:
            print(f"{Fore.CYAN}Create your arcade profile:{Style.RESET_ALL}")
            email = self.get_input("Email")
            username = self.get_input("Username")
            password = self.get_input("Password", password=True)
            confirm_password = self.get_input("Confirm Password", password=True)
            
            if password != confirm_password:
                print(f"{Fore.RED}❌ Passwords do not match!{Style.RESET_ALL}")
                input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
                return False
            
            print(f"\n{Fore.YELLOW}Creating your account...{Style.RESET_ALL}")
            success, message, user = auth_service.register_user(email, username, password)
            
            if success:
                print(f"{Fore.GREEN}✅ {message}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}Welcome to Arcadia, {username}! You start with {user.tokens} tokens! 🪙{Style.RESET_ALL}")
                input(f"{Fore.YELLOW}Press Enter to continue to login...{Style.RESET_ALL}")
                return True
            else:
                print(f"{Fore.RED}❌ {message}{Style.RESET_ALL}")
                input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
                return False
                
        except Exception as e:
            print(f"{Fore.RED}❌ Registration failed: {str(e)}{Style.RESET_ALL}")
            input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
            return False
    
    def main_menu(self):
        """Show the main game menu for logged-in users"""
        while True:
            self.clear_screen()
            self.print_logo()
            self.print_status_bar()
            
            self.print_menu(
                "🎮 MAIN ARCADE MENU",
                [
                    "🕹️  Play Games",
                    "🏆 Leaderboards", 
                    "👤 Profile & Stats",
                    "🪙 Buy Tokens",
                    "🎨 Creator Hub",
                    "⚙️  Settings",
                    "🚪 Logout"
                ],
                "Choose your adventure in the arcade!"
            )
            
            try:
                choice = input(f"\n{Fore.CYAN}Select option (1-7): {Style.RESET_ALL}")
                
                if choice == "1":
                    self.games_menu()
                elif choice == "2":
                    self.leaderboards_menu()
                elif choice == "3":
                    self.profile_menu()
                elif choice == "4":
                    self.tokens_menu()
                elif choice == "5":
                    self.creator_menu()
                elif choice == "6":
                    self.settings_menu()
                elif choice == "7":
                    self.logout()
                    break
                else:
                    print(f"{Fore.RED}Invalid option. Please try again.{Style.RESET_ALL}")
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Goodbye! Thanks for playing Arcadia! 👋{Style.RESET_ALL}")
                break
    
    def games_menu(self):
        """Show available games"""
        self.clear_screen()
        self.print_logo()
        self.print_status_bar()
        
        print(f"{Fore.YELLOW}🕹️  ARCADE GAMES LIBRARY{Style.RESET_ALL}\n")
        
        # Get available games
        games = game_service.get_available_games(self.current_user)
        
        if not games:
            print(f"{Fore.RED}No games available at the moment.{Style.RESET_ALL}")
            input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
            return
        
        # Display games in a table
        table = Table(title="🎮 Available Games", show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=3)
        table.add_column("Title", style="cyan", width=20)
        table.add_column("Type", style="green", width=12)
        table.add_column("Cost", style="yellow", width=8)
        table.add_column("Difficulty", style="red", width=10)
        table.add_column("Status", style="white", width=25)
        
        for i, game in enumerate(games, 1):
            difficulty_stars = "⭐" * game["difficulty"]
            cost_display = f"{game['token_cost']} 🪙" if game['token_cost'] > 0 else "FREE"
            status_color = "green" if game["can_play"] else "red"
            status = "✅ Available" if game["can_play"] else "❌ " + game["reason"]
            
            table.add_row(
                str(i),
                game["title"],
                game["type"].replace("_", " ").title(),
                cost_display,
                difficulty_stars,
                f"[{status_color}]{status}[/{status_color}]"
            )
        
        self.console.print(table)
        
        print(f"\n{Fore.CYAN}Enter game number to play, or 0 to go back:{Style.RESET_ALL}")
        
        try:
            choice = int(input(f"{Fore.CYAN}➤ Choice: {Style.RESET_ALL}"))
            
            if choice == 0:
                return
            elif 1 <= choice <= len(games):
                selected_game = games[choice - 1]
                if selected_game["can_play"]:
                    self.play_game(selected_game)
                else:
                    print(f"{Fore.RED}Cannot play this game: {selected_game['reason']}{Style.RESET_ALL}")
                    input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Invalid game number.{Style.RESET_ALL}")
                input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
                
        except ValueError:
            print(f"{Fore.RED}Please enter a valid number.{Style.RESET_ALL}")
            input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    def play_game(self, game_info: Dict):
        """Play a selected game"""
        self.clear_screen()
        self.print_logo()
        
        print(f"{Fore.YELLOW}🎮 PLAYING: {game_info['title'].upper()}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Type: {game_info['type'].replace('_', ' ').title()}")
        print(f"Difficulty: {'⭐' * game_info['difficulty']}")
        print(f"Cost: {game_info['token_cost']} tokens{Style.RESET_ALL}\n")
        
        # Start game session
        game_id = uuid.UUID(game_info["id"])
        success, message, session_info = game_service.start_game_session(self.current_user.id, game_id)
        
        if not success:
            print(f"{Fore.RED}❌ {message}{Style.RESET_ALL}")
            input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
            return
        
        print(f"{Fore.GREEN}✅ {message}")
        if session_info["tokens_spent"] > 0:
            print(f"Tokens spent: {session_info['tokens_spent']}")
            print(f"Remaining tokens: {session_info['remaining_tokens']}")
        print(f"{Style.RESET_ALL}")
        
        input(f"{Fore.YELLOW}Press Enter to start the game...{Style.RESET_ALL}")
        
        # Simulate game play
        print(f"\n{Fore.CYAN}🎮 Game Starting...{Style.RESET_ALL}")
        
        # Simulate game with progress bar
        game_result = game_service.simulate_game_play(
            uuid.UUID(session_info["session_id"]), 
            session_info["difficulty"]
        )
        
        # Show game events
        for event in game_result["events"]:
            print(f"{Fore.YELLOW}⚡ {event}{Style.RESET_ALL}")
            time.sleep(0.5)
        
        print(f"\n{Fore.GREEN}🏁 GAME COMPLETE!{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Final Score: {game_result['score']}")
        print(f"Duration: {game_result['duration']} seconds")
        print(f"Completed: {'✅ Yes' if game_result['completed'] else '❌ No'}{Style.RESET_ALL}")
        
        # End game session
        success, message, achievements = game_service.end_game_session(
            uuid.UUID(session_info["session_id"]),
            game_result["score"],
            game_result["duration"],
            game_result["completed"]
        )
        
        if achievements:
            print(f"\n{Fore.YELLOW}🎉 ACHIEVEMENTS UNLOCKED!{Style.RESET_ALL}")
            for achievement in achievements:
                print(f"{Fore.MAGENTA}{achievement}{Style.RESET_ALL}")
        
        # Update current user tokens (refresh from database)
        auth_success, updated_user = auth_service.validate_session(self.current_token)
        if auth_success:
            self.current_user = updated_user
        
        input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    def leaderboards_menu(self):
        """Show leaderboards"""
        self.clear_screen()
        self.print_logo()
        print(f"{Fore.YELLOW}🏆 ARCADE LEADERBOARDS{Style.RESET_ALL}\n")
        
        leaderboard = game_service.get_leaderboard(limit=10)
        
        if not leaderboard:
            print(f"{Fore.RED}No scores recorded yet. Be the first to play!{Style.RESET_ALL}")
            input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
            return
        
        table = Table(title="🏆 Top Players", show_header=True, header_style="bold yellow")
        table.add_column("Rank", style="bold", width=6)
        table.add_column("Player", style="cyan", width=20)
        table.add_column("Score", style="green", width=10)
        table.add_column("Game", style="magenta", width=20)
        table.add_column("Date", style="dim", width=12)
        
        for entry in leaderboard:
            rank_emoji = "🥇" if entry["rank"] == 1 else "🥈" if entry["rank"] == 2 else "🥉" if entry["rank"] == 3 else "👤"
            table.add_row(
                f"{rank_emoji} #{entry['rank']}",
                entry["username"],
                f"{entry['score']:,}",
                entry["game"],
                entry["date"]
            )
        
        self.console.print(table)
        input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    def profile_menu(self):
        """Show user profile and statistics"""
        self.clear_screen()
        self.print_logo()
        print(f"{Fore.YELLOW}👤 PLAYER PROFILE: {self.current_user.username.upper()}{Style.RESET_ALL}\n")
        
        stats = game_service.get_user_statistics(self.current_user.id)
        
        # Profile info
        table = Table(title="📊 Your Gaming Statistics", show_header=True, header_style="bold cyan")
        table.add_column("Statistic", style="white", width=25)
        table.add_column("Value", style="green", width=15)
        
        table.add_row("🎮 Total Games Played", str(stats["total_games_played"]))
        table.add_row("🏆 Total Score", f"{stats['total_score']:,}")
        table.add_row("✅ Games Completed", str(stats["completed_games"]))
        table.add_row("📈 Completion Rate", f"{stats['completion_rate']}%")
        table.add_row("🪙 Tokens Spent", str(stats["total_tokens_spent"]))
        table.add_row("🏅 Achievements", str(stats["achievements_earned"]))
        table.add_row("🎨 Games Created", str(stats["games_created"]))
        table.add_row("💰 Creator Revenue", f"${stats['creator_revenue']:.2f}")
        
        self.console.print(table)
        
        # Best scores
        if stats["best_scores"]:
            print(f"\n{Fore.YELLOW}🏆 Your Best Scores:{Style.RESET_ALL}")
            for score_entry in stats["best_scores"][:5]:  # Show top 5
                print(f"{Fore.CYAN}  {score_entry['game']}: {Fore.GREEN}{score_entry['score']:,} points{Style.RESET_ALL}")
        
        input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    def tokens_menu(self):
        """Token purchase menu"""
        self.clear_screen()
        self.print_logo()
        self.print_status_bar()
        
        print(f"{Fore.YELLOW}🪙 TOKEN SHOP{Style.RESET_ALL}\n")
        print(f"{Fore.CYAN}Purchase tokens to play premium games and unlock special features!{Style.RESET_ALL}\n")
        
        packages = [
            {"tokens": 50, "price": 4.99, "bonus": 0},
            {"tokens": 100, "price": 9.99, "bonus": 10},
            {"tokens": 250, "price": 19.99, "bonus": 50},
            {"tokens": 500, "price": 34.99, "bonus": 100},
        ]
        
        table = Table(title="💰 Token Packages", show_header=True, header_style="bold yellow")
        table.add_column("#", width=3)
        table.add_column("Tokens", style="cyan", width=10)
        table.add_column("Bonus", style="green", width=10)
        table.add_column("Total", style="magenta", width=10)
        table.add_column("Price", style="yellow", width=10)
        
        for i, package in enumerate(packages, 1):
            total_tokens = package["tokens"] + package["bonus"]
            bonus_text = f"+{package['bonus']}" if package["bonus"] > 0 else "-"
            table.add_row(
                str(i),
                str(package["tokens"]),
                bonus_text,
                str(total_tokens),
                f"${package['price']}"
            )
        
        self.console.print(table)
        
        print(f"\n{Fore.CYAN}Select package (1-{len(packages)}) or 0 to go back:{Style.RESET_ALL}")
        
        try:
            choice = int(input(f"{Fore.CYAN}➤ Choice: {Style.RESET_ALL}"))
            
            if choice == 0:
                return
            elif 1 <= choice <= len(packages):
                package = packages[choice - 1]
                total_tokens = package["tokens"] + package["bonus"]
                
                print(f"\n{Fore.YELLOW}📦 Selected Package:{Style.RESET_ALL}")
                print(f"{Fore.CYAN}  Tokens: {package['tokens']} + {package['bonus']} bonus = {total_tokens} total")
                print(f"  Price: ${package['price']}{Style.RESET_ALL}")
                
                confirm = input(f"\n{Fore.YELLOW}Confirm purchase? (y/N): {Style.RESET_ALL}").lower()
                
                if confirm == 'y':
                    # Simulate payment processing
                    print(f"\n{Fore.YELLOW}💳 Processing payment...{Style.RESET_ALL}")
                    time.sleep(2)
                    
                    success, message = game_service.purchase_tokens(
                        self.current_user.id, total_tokens, package["price"]
                    )
                    
                    if success:
                        print(f"{Fore.GREEN}✅ {message}")
                        print(f"🪙 You now have {self.current_user.tokens + total_tokens} tokens!{Style.RESET_ALL}")
                        
                        # Update current user
                        auth_success, updated_user = auth_service.validate_session(self.current_token)
                        if auth_success:
                            self.current_user = updated_user
                    else:
                        print(f"{Fore.RED}❌ {message}{Style.RESET_ALL}")
                    
                    input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
                else:
                    print(f"{Fore.YELLOW}Purchase cancelled.{Style.RESET_ALL}")
                    time.sleep(1)
            else:
                print(f"{Fore.RED}Invalid package number.{Style.RESET_ALL}")
                time.sleep(1)
                
        except ValueError:
            print(f"{Fore.RED}Please enter a valid number.{Style.RESET_ALL}")
            time.sleep(1)
    
    def creator_menu(self):
        """Creator Hub menu (simplified for terminal)"""
        self.clear_screen()
        self.print_logo()
        print(f"{Fore.YELLOW}🎨 CREATOR HUB{Style.RESET_ALL}\n")
        print(f"{Fore.CYAN}Welcome to the Creator Hub! Here you can manage your published games.")
        print(f"(Full game creation tools coming in future releases){Style.RESET_ALL}\n")
        
        stats = game_service.get_user_statistics(self.current_user.id)
        
        print(f"{Fore.YELLOW}📊 Your Creator Stats:{Style.RESET_ALL}")
        print(f"{Fore.CYAN}  Games Created: {stats['games_created']}")
        print(f"  Total Revenue: ${stats['creator_revenue']:.2f}")
        print(f"  Revenue Share: 35%{Style.RESET_ALL}")  # Using hardcoded value for now
        
        input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    def settings_menu(self):
        """Settings menu"""
        self.clear_screen()
        self.print_logo()
        print(f"{Fore.YELLOW}⚙️  SETTINGS{Style.RESET_ALL}\n")
        
        self.print_menu(
            "User Settings",
            [
                "🔑 Change Password",
                "📊 View Account Info", 
                "🗑️  Delete Account",
                "🔙 Back to Main Menu"
            ]
        )
        
        try:
            choice = input(f"\n{Fore.CYAN}Select option (1-4): {Style.RESET_ALL}")
            
            if choice == "1":
                self.change_password()
            elif choice == "2":
                self.view_account_info()
            elif choice == "3":
                self.delete_account()
            elif choice == "4":
                return
            else:
                print(f"{Fore.RED}Invalid option.{Style.RESET_ALL}")
                time.sleep(1)
                
        except KeyboardInterrupt:
            return
    
    def change_password(self):
        """Change user password"""
        print(f"\n{Fore.YELLOW}🔑 CHANGE PASSWORD{Style.RESET_ALL}")
        
        try:
            old_password = self.get_input("Current Password", password=True)
            new_password = self.get_input("New Password", password=True)
            confirm_password = self.get_input("Confirm New Password", password=True)
            
            if new_password != confirm_password:
                print(f"{Fore.RED}❌ Passwords do not match!{Style.RESET_ALL}")
                input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
                return
            
            success, message = auth_service.change_password(
                self.current_user.id, old_password, new_password
            )
            
            if success:
                print(f"{Fore.GREEN}✅ {message}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}❌ {message}{Style.RESET_ALL}")
            
            input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error changing password: {str(e)}{Style.RESET_ALL}")
            input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    def view_account_info(self):
        """View account information"""
        print(f"\n{Fore.YELLOW}📊 ACCOUNT INFORMATION{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Email: {self.current_user.email}")
        print(f"Username: {self.current_user.username}")
        print(f"Account Created: {self.current_user.created_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"Last Login: {self.current_user.last_login.strftime('%Y-%m-%d %H:%M') if self.current_user.last_login else 'Never'}")
        print(f"Subscription: {'Active' if self.current_user.subscription_active else 'Inactive'}")
        print(f"Current Tokens: {self.current_user.tokens}{Style.RESET_ALL}")
        
        input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    def delete_account(self):
        """Delete user account (placeholder)"""
        print(f"\n{Fore.RED}🗑️  DELETE ACCOUNT{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}This feature is not available in the terminal version.")
        print(f"Contact support for account deletion requests.{Style.RESET_ALL}")
        
        input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    def logout(self):
        """Logout current user"""
        if self.current_token:
            auth_service.logout_user(self.current_token)
        
        self.current_user = None
        self.current_token = None
        
        print(f"\n{Fore.GREEN}✅ Logged out successfully!")
        print(f"{Fore.CYAN}Thanks for playing Arcadia! See you next time! 👋{Style.RESET_ALL}")
        time.sleep(2)
    
    def run(self):
        """Main application loop"""
        self.show_welcome_screen()
        
        while self.running:
            if not self.current_user:
                # Show login/register menu
                self.print_menu(
                    "🎮 WELCOME TO ARCADIA",
                    [
                        "🔑 Login",
                        "📝 Register", 
                        "❌ Exit"
                    ],
                    "Please login or register to access the arcade!"
                )
                
                try:
                    choice = input(f"\n{Fore.CYAN}Select option (1-3): {Style.RESET_ALL}")
                    
                    if choice == "1":
                        self.login_menu()
                    elif choice == "2":
                        self.register_menu()
                    elif choice == "3":
                        print(f"\n{Fore.YELLOW}Thanks for visiting Arcadia! Goodbye! 👋{Style.RESET_ALL}")
                        self.running = False
                    else:
                        print(f"{Fore.RED}Invalid option. Please try again.{Style.RESET_ALL}")
                        time.sleep(1)
                        self.clear_screen()
                        self.print_logo()
                        
                except KeyboardInterrupt:
                    print(f"\n{Fore.YELLOW}Goodbye! Thanks for visiting Arcadia! 👋{Style.RESET_ALL}")
                    self.running = False
            else:
                # Show main menu for logged-in users
                self.main_menu()
                self.running = False

def main():
    """Entry point for the CLI application"""
    try:
        terminal = ArcadiaTerminal()
        terminal.run()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Application interrupted. Goodbye! 👋{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}Application error: {str(e)}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Please check your database connection and try again.{Style.RESET_ALL}")

if __name__ == "__main__":
    main()