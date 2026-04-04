import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import random
from datetime import datetime

# Load .env when present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Initialize bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

QUESTIONS_FILE = "questions.json"

def load_questions():
    if os.path.exists(QUESTIONS_FILE):
        with open(QUESTIONS_FILE, "r") as f:
            data = json.load(f)
            # Handle both formats: array or object with questions key
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "questions" in data:
                return data["questions"]
    return []

class QuizGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_question = None
        self.answers = {}
        self.correct_answer = None
        self.questions = load_questions()
        self.used_questions = set()  # Track used questions in current game
        self.game_active = False

        # New game mode variables
        self.registered_players = {}  # user_id -> {"name": str, "nickname": str, "role": "villager"/"imposter", "points": int}
        self.current_imposter = None  # user_id of current imposter
        self.win_threshold = 20  # Points needed to win
        self.accusation_votes = {}  # Current round accusation votes voter_id -> target_user_id
        self.round_active = False  # Whether a question round is active
        self.registration_open = False  # Whether registration is currently open
        self.accusation_open = False  # Whether accusation phase is open after a question


    def adjust_player_points(self, player_id, delta):
        player = self.registered_players.get(player_id)
        if not player:
            return 0

        current_points = player.get("points", 0) + delta
        player["points"] = max(0, current_points)

        return player["points"]

    @app_commands.command(name="newgame", description="Open registration for a new game")
    @app_commands.describe(
        win_threshold="Points needed to win (default: 20)"
    )
    async def new_game(self, interaction: discord.Interaction, win_threshold: int = 20):
        """Open registration for a new game"""
        if self.game_active:
            await interaction.response.send_message("A game is already active! Use /endgame to finish it first.", ephemeral=True)
            return

        self.registration_open = True
        self.game_active = False
        self.active_question = None
        self.answers = {}
        self.correct_answer = None
        self.registered_players = {}
        self.current_imposter = None
        self.win_threshold = win_threshold
        self.accusation_votes = {}
        self.round_active = False
        self.accusation_open = False
        self.used_questions = set()

        embed = discord.Embed(
            title="🎮 New Game Registration Open!",
            description="A trivia social deduction game is starting soon.",
            color=discord.Color.purple()
        )
        embed.add_field(
            name="How to Play",
            value="• Use `/register` to join the game\n• Use `/question` to view questions privately\n• The imposter gets private answers\n• Answer with `/answer <number>`\n• Use `/accuse <player>` after a round if you suspect the imposter",
            inline=False
        )
        embed.add_field(name="Registration", value="Use `/register` to join now!", inline=False)
        embed.add_field(name="Win Condition", value=f"First player to reach **{self.win_threshold}** points wins.", inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="register",  description="Register for the current game")
    @app_commands.describe(nickname="Your desired nickname for the game")
    async def register_player(self, interaction: discord.Interaction, nickname: str):
        """Register a player for the game"""
        if self.game_active:
            await interaction.response.send_message("Game has already started! Wait for the next game.", ephemeral=True)
            return

        if not self.registration_open:
            await interaction.response.send_message(
                "❌ There is no open registration right now. Use /newgame to start a new game or /rules for instructions.",
                ephemeral=True
            )
            return

      
        user_id = interaction.user.id
        user_name = interaction.user.name

        if user_id in self.registered_players:
            await interaction.response.send_message("You're already registered!", ephemeral=True)
            return

        self.registered_players[user_id] = {
            "name": user_name,
            "nickname": nickname,
            "role": None,  # Will be assigned when game starts
            "points": 0
        }

        embed = discord.Embed(
            title="✅ Registered!",
            description=f"**{user_name}** has joined the game as **{nickname}**!",
            color=discord.Color.green()
        )
        embed.add_field(name="Your Nickname", value=f"**{nickname}**", inline=False)
        embed.add_field(name="Total Players", value=str(len(self.registered_players)), inline=True)
        embed.add_field(name="All in?", value="Type `/question` to begin!", inline=False)
        embed.add_field(name="Accuse Tip", value="Use `/accuse <nickname>` to accuse a player.", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="question", description="View the current question privately")
    async def question_command(self, interaction: discord.Interaction):
        """View the current question privately"""
        if not self.game_active and not self.registration_open:
            await interaction.response.send_message(
                "❌ No active game. Use /newgame to start a game.",
                ephemeral=True
            )
            return

        # if self.registration_open and len(self.registered_players) < 2:
        #     await interaction.response.send_message(
        #         "❌ Need at least 2 players registered to start the game. Use /register or /rules for instructions.",
        #         ephemeral=True
        #     )
        #     return

        current_user_id = interaction.user.id

        if current_user_id not in self.registered_players:
            await interaction.response.send_message(
                "❌ You are not registered in the current game.",
                ephemeral=True
            )
            return

        if not self.game_active and self.registration_open:
            # Start the game
            import random
            player_ids = list(self.registered_players.keys())
            self.current_imposter = random.choice(player_ids)
            for user_id, player_data in self.registered_players.items():
                player_data["role"] = "imposter" if user_id == self.current_imposter else "villager"
                player_data.setdefault("points", 0)

            self.game_active = True
            self.registration_open = False
            self.accusation_open = False

        if not self.round_active:
            # Announce the new round publicly before the private question message
            round_embed = discord.Embed(
                title="🟢 Round Started!",
                description="A new question is available. Use `/question` to view it privately.",
                color=discord.Color.blue()
            )
            await interaction.channel.send(embed=round_embed)
            await self.ask_next_question(interaction.channel)


        user_id = interaction.user.id
        player_data = self.registered_players.get(user_id, {})
        role = player_data.get("role", "villager")

        # Send question privately via ephemeral
        embed = discord.Embed(
            title="🎭 Your Role & Question",
            color=discord.Color.red() if role == "imposter" else discord.Color.green()
        )
        embed.description = f"{player_data.get('nickname', 'Unknown')}: You are a **{role.upper()}**!"
        embed.add_field(
            name="Question",
            value=self.active_question,
            inline=False
        )
        if role == "imposter":
            embed.add_field(
                name="Correct Answer",
                value=f"**{self.correct_answer}**",
                inline=False
            )
        embed.add_field(
            name="How to Answer",
            value="Use `/answer <number>` in the channel.",
            inline=False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    


    async def ask_next_question(self, channel):
        """Set up the next question"""
        if not self.game_active:
            return

        if len(self.registered_players) == 0:
            await self.end_game(channel, "draw")
            return

        available_questions = [q for q in self.questions if q.get("id", q.get("question")) not in self.used_questions]

        if not available_questions:
            top_player, tie = self.find_top_player()

            if tie or top_player is None:
                await self.end_game(channel, "draw")
            else:
                await self.end_game(channel, top_player)
            return

        # Select random question
        import random
        question_data = random.choice(available_questions)

        # Mark as used
        question_id = question_data.get("id", question_data.get("question"))
        self.used_questions.add(question_id)

        self.active_question = question_data["question"]
        self.correct_answer = question_data["answer"]
        self.answers = {}
        self._last_channel = channel
        self.round_active = True
        self.accusation_open = False
        self.accusation_votes = {}  # Reset accusation votes for new round

    
    def find_top_player(self):
        """Find the player with the most points"""
        # All questions used - determine winner by highest points
        top_player = None
        top_score = -1
        tie = False
        for user_id, player_data in self.registered_players.items():
            points = player_data.get("points", 0)
            if points > top_score:
                top_player = user_id
                top_score = points
                tie = False
            elif points == top_score:
                tie = True
        return top_player, tie


    @app_commands.command(name="endgame", description="End the current game or cancel registration")
    async def end_game_command(self, interaction: discord.Interaction):
        """End the current game or cancel registration"""
        if not self.game_active and not self.registration_open:
            await interaction.response.send_message(
                "❌ There is no active game or registration. Use /newgame to start a new game.",
                ephemeral=True
            )
            return

        if not self.game_active and self.registration_open:
            self.registration_open = False
            self.registered_players = {}
            self.accusation_votes = {}
            self.round_active = False
            self.accusation_open = False
            await interaction.response.send_message("✅ Registration cancelled. Use /newgame when you are ready to start again.", ephemeral=True)
            return

        top_player, tie = self.find_top_player()
        await self.end_game(interaction.channel, top_player if not tie else "draw")
        await interaction.response.send_message("Game ended!", ephemeral=True)
    
    async def end_game(self, channel, winner):
        """End the game and show final results"""
        if not self.game_active:
            return

        self.game_active = False

        if winner == "draw":
            title = "🤝 Game Ended in a Draw!"
            color = discord.Color.grey()
            description = "No clear winner this time!"
        elif winner in self.registered_players:
            player_nickname = self.registered_players[winner]["nickname"]
            title = f"🏆 {player_nickname} Wins!"
            color = discord.Color.gold()
            description = f"{player_nickname} reached {self.win_threshold} points first and wins the game!"
        else:
            title = "🏁 Game Ended"
            color = discord.Color.blue()
            description = "The game is over."

        embed = discord.Embed(
            title=title,
            description=description,
            color=color
        )

        player_lines = []
        for user_id, player_data in self.registered_players.items():
            role = player_data.get("role", "villager")
            points = player_data.get("points", 0)
            player_lines.append(f"• **{player_data['nickname']}** — {role.title()} — {points} pts")

        embed.add_field(
            name="Final Player Standings",
            value="\n".join(player_lines) if player_lines else "No players",
            inline=False
        )

        await channel.send(embed=embed)

        # Reset game state
        self.registered_players = {}
        self.current_imposter = None
        self.accusation_votes = {}
        self.used_questions = set()
        self.active_question = None
        self.round_active = False
        self.registration_open = False
        self.accusation_open = False
    
    
    @app_commands.command(name="answer", description="Submit your numerical answer")
    @app_commands.describe(value="Your numerical answer")
    async def submit_answer(self, interaction: discord.Interaction, value: float):
        """Submit an answer to the active question"""
        if not self.game_active or not self.round_active:
            await interaction.response.send_message("❌ No active question!", ephemeral=True)
            return

        user_id = interaction.user.id
        user_name = interaction.user.name

        # Check if player is registered
        if user_id not in self.registered_players:
            await interaction.response.send_message("❌ You're not in the game!", ephemeral=True)
            return

        if user_id in self.answers:
            await interaction.response.send_message("❌ You've already submitted an answer this round!", ephemeral=True)
            return

        self.answers[user_id] = {
            "name": self.registered_players[user_id]["name"],
            "nickname": self.registered_players[user_id]["nickname"],
            "answer": value,
            "difference": abs(value - self.correct_answer),
            "role": self.registered_players[user_id]["role"]
        }

        await interaction.response.send_message(f"✅ Your answer **{value}** has been submitted!", ephemeral=True)

        # Send public update on answer count
        answered_count = len(self.answers)
        total_players = len(self.registered_players)
        remaining = total_players - answered_count
        
        answer_embed = discord.Embed(
            title="📝 Answer Submitted!",
            description=f"**{self.registered_players[user_id]['nickname']}** has submitted their answer.",
            color=discord.Color.blue()
        )
        answer_embed.add_field(
            name="Progress",
            value=f"✅ Answered: {answered_count}/{total_players}\n⏳ Remaining: {remaining}",
            inline=False
        )
        
        await interaction.channel.send(embed=answer_embed)

        # Check if all registered players have answered
        if len(self.answers) >= len(self.registered_players):
            await self.end_question_auto()

    @app_commands.command(name="accuse", description="Accuse a player of being the imposter")
    @app_commands.describe(player_name="Nickname of the player to accuse")
    async def accuse_player(self, interaction: discord.Interaction, player_name: str):
        """Vote to accuse a player of being the imposter"""
        if not self.game_active:
            await interaction.response.send_message(
                "❌ No active game. Use /newgame to start a new game.",
                ephemeral=True
            )
            return

        if not self.round_active and not self.accusation_open:
            await interaction.response.send_message(
                "❌ Accusations are not open right now. Answer the current question or use /question to start the next one.",
                ephemeral=True
            )
            return

        voter_id = interaction.user.id

        if voter_id not in self.registered_players:
            await interaction.response.send_message("❌ You're not in the game!", ephemeral=True)
            return

        if voter_id in self.accusation_votes:
            await interaction.response.send_message("❌ You've already accused once this round!", ephemeral=True)
            return

        target_user_id = None
        for uid, data in self.registered_players.items():
            if data["nickname"].lower() == player_name.lower():
                target_user_id = uid
                break

        if not target_user_id:
            await interaction.response.send_message(f"❌ Player '{player_name}' not found!", ephemeral=True)
            return

        if target_user_id == voter_id:
            await interaction.response.send_message("❌ You cannot accuse yourself!", ephemeral=True)
            return

        self.accusation_votes[voter_id] = target_user_id

        vote_counts = {}
        for voted_user_id in self.accusation_votes.values():
            vote_counts[voted_user_id] = vote_counts.get(voted_user_id, 0) + 1

        majority_needed = len(self.registered_players) // 2 + 1

        if vote_counts.get(target_user_id, 0) >= majority_needed:
            accused_data = self.registered_players[target_user_id]
            accused_nickname = accused_data["nickname"]
            accused_role = accused_data["role"]
            voters = [self.registered_players[vid]["nickname"] for vid, tid in self.accusation_votes.items() if tid == target_user_id]

            result_embed = discord.Embed(
                title="🕵️ Accusation Resolved",
                color=discord.Color.purple()
            )
            result_embed.add_field(name="Accused Player", value=f"**{accused_nickname}**", inline=False)
            result_embed.add_field(name="Votes", value=f"{vote_counts[target_user_id]}/{majority_needed}", inline=False)
            result_embed.add_field(name="Voters", value=", ".join(voters) if voters else "None", inline=False)

            if accused_role == "imposter":
                self.adjust_player_points(target_user_id, -5)
                for voter, target in self.accusation_votes.items():
                    if target == target_user_id:
                        self.adjust_player_points(voter, 5)

                available_targets = [uid for uid in self.registered_players if uid != self.current_imposter]
                import random
                if available_targets:
                    self.current_imposter = random.choice(available_targets)

                for uid, player_data in self.registered_players.items():
                    player_data["role"] = "imposter" if uid == self.current_imposter else "villager"

                result_embed.add_field(name="Result", value=f"Correct! The imposter was **{accused_nickname}**.", inline=False)
                result_embed.add_field(name="Imposter Penalty", value="-5 points", inline=True)
                result_embed.add_field(name="Correct Voters", value="+5 points each", inline=True)

                # New imposter can check /myrole for current question info
            else:
                for voter, target in self.accusation_votes.items():
                    if target == target_user_id:
                        self.adjust_player_points(voter, -3)

                result_embed.add_field(name="Result", value=f"Wrong accusation! **{accused_nickname}** was not the imposter.", inline=False)
                result_embed.add_field(name="Penalty", value="-3 points for each incorrect voter", inline=False)

            self.accusation_votes = {}
            self.accusation_open = False

            leaderboard = "\n".join(
                f"• **{data['nickname']}** — {data.get('points', 0)} pts" for data in self.registered_players.values()
            )
            result_embed.add_field(name="Leaderboard", value=leaderboard or "No players", inline=False)

            await interaction.response.send_message(embed=result_embed)

            # Check for win condition after accusation scoring
            winner_id = None
            for user_id, player_data in self.registered_players.items():
                if player_data.get("points", 0) >= self.win_threshold:
                    winner_id = user_id
                    break

            if winner_id:
                await self.end_game(interaction.channel, winner_id)
        else:
            await interaction.response.send_message(
                f"✅ Vote recorded for {player_name}. Current votes: {vote_counts.get(target_user_id, 0)}/{majority_needed} needed.",
                ephemeral=True
            )
    
    @app_commands.command(name="endquestion", description="End the current question and award points")
    async def end_question(self, interaction: discord.Interaction):
        """End the question and calculate scores"""
        if not self.game_active or not self.round_active:
            await interaction.response.send_message("❌ No active question to end!", ephemeral=True)
            return
        
        await interaction.response.defer()
        await self.end_question_auto()
        await interaction.followup.send("Question ended!")
    
    async def end_question_auto(self):
        """End question and award player points"""
        if not self.active_question:
            return

        if not self.answers:
            self.active_question = None
            self.round_active = False
            self.accusation_open = True
            self.accusation_votes = {}

            no_answer_embed = discord.Embed(
                title="⏹️ Question Ended",
                description="The question was ended without any answers.",
                color=discord.Color.orange()
            )
            no_answer_embed.add_field(name="Next Step", value="Use `/question` to start the next round or `/accuse <player>` if you suspect the imposter.", inline=False)

            if hasattr(self, '_last_channel'):
                await self._last_channel.send(embed=no_answer_embed)
            return

        sorted_answers = sorted(
            self.answers.items(),
            key=lambda x: x[1]["difference"]
        )

        embed = discord.Embed(
            title="✅ Question Ended!",
            description=f"Correct Answer: **{self.correct_answer}**",
            color=discord.Color.green()
        )

        results_text = ""
        winner_id = None

        for idx, (user_id, answer_data) in enumerate(sorted_answers[:3]):
            points = [3, 2, 1][idx]
            medal = ["🥇", "🥈", "🥉"][idx]
            self.adjust_player_points(user_id, points)

            difference = answer_data["difference"]
            results_text += f"{medal} **{answer_data['nickname']}** - Answer: {answer_data['answer']} (Off by {difference}) - +{points} pts\n"

            if self.registered_players[user_id]["points"] >= self.win_threshold and winner_id is None:
                winner_id = user_id

        if len(sorted_answers) > 3:
            results_text += "\n**Other Answers:**\n"
            for user_id, answer_data in sorted_answers[3:]:
                difference = answer_data["difference"]
                results_text += f"• **{answer_data['nickname']}** - Answer: {answer_data['answer']} (Off by {difference})\n"

        embed.add_field(name="Results", value=results_text, inline=False)

        current_scores = "\n".join(
            f"• **{data['nickname']}** — {data['points']} pts" for data in self.registered_players.values()
        )
        embed.add_field(name=f"Current Points ({{self.win_threshold}} to win)", value=current_scores or "No players", inline=False)

        if hasattr(self, '_last_channel'):
            channel = self._last_channel
            await channel.send(embed=embed)

        self.active_question = None
        self.answers = {}
        self.round_active = False
        self.accusation_open = True
        self.accusation_votes = {}

        if winner_id:
            await self.end_game(channel, winner_id)
        else:
            summary_embed = discord.Embed(
                title="📌 Round Complete",
                description="Points have been awarded. Use `/accuse <player>` if you suspect the imposter, or `/question` to start the next round.",
                color=discord.Color.blue()
            )
            summary_embed.add_field(name="Next Step", value="Use `/accuse` now or `/question` when ready for the next question.", inline=False)
            await channel.send(embed=summary_embed)
    
    
    @app_commands.command(name="status", description="Check if a question is active")
    async def status(self, interaction: discord.Interaction):
        """Check game status"""
        embed = discord.Embed(
            title="📊 Game Status",
            color=discord.Color.blue()
        )

        # Game status
        embed.add_field(name="Registration Open", value="✅ Yes" if self.registration_open else "❌ No", inline=True)
        if self.game_active:
            embed.add_field(name="Game State", value="✅ Active", inline=True)
            embed.add_field(name="Round State", value="✅ Active" if self.round_active else "❌ Inactive", inline=True)
            embed.add_field(name="Accusation Phase", value="✅ Open" if self.accusation_open else "❌ Closed", inline=True)
            embed.add_field(name="Registered Players", value=str(len(self.registered_players)), inline=True)
            
            if self.active_question:
                embed.add_field(name="Active Question", value=self.active_question[:100] + "..." if len(self.active_question) > 100 else self.active_question, inline=False)
                embed.add_field(name="Answers Received", value=f"{len(self.answers)}/{len(self.registered_players)}", inline=True)

            score_lines = "\n".join(
                f"• {data['nickname']}: {data.get('points', 0)} pts" for data in self.registered_players.values()
            )
            embed.add_field(name="Player Points", value=score_lines or "No players yet", inline=False)
        else:
            embed.add_field(name="Game State", value="❌ Inactive", inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="rules", description="Show game flow and instructions")
    async def rules(self, interaction: discord.Interaction):
        """Show game rules and command flow"""
        embed = discord.Embed(
            title="📜 Game Rules",
            description="Follow the flow: /newgame → /register → /question → /answer → /endquestion / /accuse → /question",
            color=discord.Color.green()
        )
        embed.add_field(name="1. Start a Game", value="Use `/newgame [points]` to open registration.", inline=False)
        embed.add_field(name="2. Register", value="Players join by using `/register`.", inline=False)
        embed.add_field(name="3. Begin Question", value="Use `/question` to view questions privately.", inline=False)
        embed.add_field(name="4. Answer", value="Submit answers with `/answer <number>`. The question ends when everyone answers or someone uses `/endquestion`.", inline=False)
        embed.add_field(name="5. Accuse", value="If you suspect the imposter after a round, use `/accuse <player>`. Points can change after a correct or wrong accusation.", inline=False)
        embed.add_field(name="6. Continue", value="After points are awarded, use `/question` to start the next round or `/endgame` to finish.", inline=False)
        embed.add_field(name="Quick Tip", value="If `/question` is used after a finished game, start a new match with `/newgame`.", inline=False)
        embed.add_field(
            name="Goal of the Game",
            value=f"Be the first player to reach the win threshold ({self.win_threshold}) by answering questions accurately and successfully accusing the imposter.",
            inline=False
        )
        embed.add_field(
            name="Imposters Rules",
            value="Imposters see the correct answer but can be accused to lose their imposter status. Accusing correctly earns all voters +5 points, and -5 to the imposter. Accusing wrong earns voters -3 points.",
            inline=False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="help", description="Show all available commands")
    async def show_help(self, interaction: discord.Interaction):
        """Show all available commands"""
        embed = discord.Embed(
            title="🎮 GeniusAmongUs Bot Commands",
            description="An Among Us-style social deduction trivia game!",
            color=discord.Color.blue()
        )

        # Game Setup Commands
        embed.add_field(
            name="🎯 Game Setup",
            value="• `/newgame [points]` - Open registration for a new game\n• `/register` - Join the current game\n• `/question` - View questions privately\n• `/endgame` - End the current game or cancel registration",
            inline=False
        )

        # Gameplay Commands
        embed.add_field(
            name="🎲 Gameplay",
            value="• `/answer <number>` - Submit your numerical answer\n• `/accuse <player>` - Accuse the suspected imposter\n• `/endquestion` - End the current question and award points\n• `/status` - Check current game status\n• `/rules` - Show game flow and command instructions",
            inline=False
        )

        embed.set_footer(text="Use /status to check current game state")

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup():
    quiz_game = QuizGame(bot)
    await bot.add_cog(quiz_game)

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)
    print(f"Bot is ready as {bot.user}")

async def main():
    async with bot:
        await setup()
        # Add your token here
        token = os.getenv("DISCORD_BOT_TOKEN")
        if not token:
            print("❌ Error: DISCORD_BOT_TOKEN environment variable not set!")
            print("Please set your bot token in the environment or .env file")
            return
        await bot.start(token)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
