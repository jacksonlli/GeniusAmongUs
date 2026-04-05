# Discord Among Us Trivia Bot

A Discord bot that hosts **Among Us-style social deduction trivia games** with a streamlined round flow: `/newgame`, `/register`, `/ready`, `/answer`, `/endquestion`, `/accuse`, and `/endgame`.

## Game Overview

This bot combines numerical trivia with hidden-role deduction. One player is secretly the imposter each match and receives the correct answer privately, while everyone competes for points.

- 🤫 **Hidden Roles:** An imposter sees the answer privately for each question
- 🎭 **Role DM:** Players receive role assignment DMs when the first question starts
- 🧠 **Point-Based Play:** Earn personal points for closest answers
- 🗳️ **Optional Accusations:** Use `/accuse <player>` after a round if you suspect the imposter
- 🏆 **Win Condition:** First player to reach the points threshold wins

## Features

✨ **Game Features:**
- **Fast setup:** `/newgame` opens registration, `/ready` begins play
- **Private role delivery:** The imposter gets answers via DM
- **Answer-based scoring:** Top answers earn rewards each round
- **Accusation mechanic:** Correct accusations boost voters, wrong ones penalize them
- **Flexible flow:** Continue with `/ready` or finish with `/endgame`

🎯 **Scoring System:**
- **1st place:** 3 points
- **2nd place:** 2 points
- **3rd place:** 1 point
- **Win Threshold:** First player to reach the configured target wins

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- Discord Server (with admin permissions)
- Discord Bot Token

### 1. Create a Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to "Bot" section and click "Add Bot"
4. Under TOKEN, click "Copy" to copy your bot token
5. Save this token safely - you'll need it next

### 2. Configure Bot Permissions

In the Developer Portal:
1. Go to "OAuth2" → "URL Generator"
2. Select scopes: `bot`
3. Select permissions:
   - Send Messages
   - Embed Links
   - Read Message History
4. Copy the generated URL and open it to add bot to your server

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Bot (Interactive)

Run the setup script to configure everything:

```bash
python setup.py
```

This will:
- ✅ Check if dependencies are installed
- ✅ Validate your files
- ✅ Help you configure the Discord bot token
- ✅ Run tests to verify everything works

### 5. Manual Setup (Alternative)

If you prefer manual setup, follow these steps:

**Option A: Using .env file (Recommended)**
Create a `.env` file in the project directory:
```
DISCORD_BOT_TOKEN=your_bot_token_here
```

**Option B: Set Environment Variable (Windows PowerShell)**
```powershell
$env:DISCORD_BOT_TOKEN="your_bot_token_here"
python bot.py
```

**Option C: Set Environment Variable (Windows CMD)**
```cmd
set DISCORD_BOT_TOKEN=your_bot_token_here
python bot.py
```

### 5. Run the Bot

```bash
python bot.py
```

You should see:
```
Synced X command(s)
Bot is ready as YourBotName#0000
```

### 6. Test the Bot Logic (Optional)

Before connecting to Discord, you can test the bot's core functionality:

```bash
python test_bot.py
```

This will test:
- ✅ Question loading from `questions.json`
- ✅ Scoring system logic
- ✅ Score persistence
- ✅ Game simulation
- ✅ Bot token configuration

Expected output: `5/6 tests passed` (bot token test fails until configured)

## Commands

### `/newgame [points]`
Open registration for a new game.
- `points` optional: points needed to win (default: 100)
- Use /newgame to begin the new match.

### `/register`
Join the open game registration.

### `/ready`
Ready up to start the game or begin the next question once all players are prepared.

### `/question`
View your private role and question for the current round.

### `/answer <number>`
Submit your numerical answer to the active question.

### `/endquestion`
End the current question early and award points.

### `/accuse <player>`
Accuse a player of being the imposter after the round.

### `/endgame`
End the current game or cancel an open registration.

### `/rules`
Show the game flow and instructions.

### `/status`
Check current registration and game status.

### `/help`
Show all available commands.

## How It Works

### Game Setup
1. Start registration with `/newgame`.
2. Players join with `/register`.
3. Begin the first round with `/ready`.
4. Each player uses `/question` to reveal their private role and question.

### Round Flow
1. The bot starts the question and players use `/question` to view their private role and question.
2. Players submit answers with `/answer <number>`.
3. The round ends when everyone has answered or when `/endquestion` is used.
4. Points are awarded to the top answers.
5. The leaderboard is displayed.
6. Players may optionally accuse someone with `/accuse <player>`.
7. Use `/ready` to start the next round.

### Win Condition
- A player wins when they reach the configured points threshold.
- Use `/endgame` at any time to stop the current game.

## Score Tracking

Scores are automatically saved to `scores.json` in the format:
```json
{
  "user_id": {
    "name": "Player Name",
    "total_points": 15,
    "answers": 5
  }
}
```

## Example Gameplay

### Game Setup
```
[Admin]: /newgame 50
[Bot]: 🎮 New game registration is open! Use /register to join.

[Player1]: /register
[Bot]: ✅ Alice has joined the game!

[Player2]: /register
[Bot]: ✅ Bob has joined the game!

[Player3]: /register
[Bot]: ✅ Charlie has joined the game!
```

### Start the First Question
```
[Admin]: /ready
[Bot]: 🎮 Game started! First question incoming.

[Alice receives a private role/status update]: 🎭 Your Role: IMPOSTER!
[Bob receives a private role/status update]: 🎭 Your Role: VILLAGER!
[Charlie receives a private role/status update]: 🎭 Your Role: VILLAGER!
```

### Gameplay Round
```
[Bot]: 🎯 Question! What is 5 + 3?
       Active Players: 3

[Alice (Imposter) receives DM]: 🎭 Imposter Knowledge
                                Question: What is 5 + 3?
                                Correct Answer: 8

[Alice]: /answer 8
✅ Your answer 8 has been submitted!

[Bob]: /answer 7
✅ Your answer 7 has been submitted!

[Charlie]: /answer 9
✅ Your answer 9 has been submitted!

[Bot]: ✅ Question Ended! Correct Answer: 8
       🥇 Alice - Answer: 8 (Off by 0) - +3 pts
       🥈 Charlie - Answer: 9 (Off by 1) - +2 pts
       🥉 Bob - Answer: 7 (Off by 1) - +1 pt

       Leaderboard: Alice 3 | Charlie 2 | Bob 1
```

### Optional Accusation
```
[Bob]: /accuse Alice
[Charlie]: /accuse Alice
[Bot]: 🕵️ Accusation resolved! Alice was the imposter.
       Alice -5 pts, Bob +5 pts, Charlie +5 pts
       Leaderboard: Bob 6 | Charlie 7 | Alice 0
```

### Continue or End
```
[Admin]: /ready
[Bot]: 🎯 Next question is starting now.

[Admin]: /endgame
[Bot]: 🏁 Game ended! Final leaderboard displayed.
```

## Testing Options

### Automated Setup & Testing
Run `python setup.py` for guided setup:
- Interactive bot token configuration
- Dependency checking
- File validation
- Test suite execution

### Local Logic Testing
Run `python test_bot.py` to test core functionality without Discord:
- Question loading and validation
- Scoring algorithm
- Score persistence
- Game simulation
- Configuration checks

### Discord Testing
1. **Test Server:** Create a private Discord server for testing
2. **Bot Permissions:** Use minimal permissions initially
3. **Single Channel:** Test in one channel first
4. **Small Group:** Start with 2-3 test users

### Production Deployment
- **Backup Scores:** Keep `scores.json` safe
- **Monitor Logs:** Check console output for errors
- **User Feedback:** Test with real users gradually

**"DISCORD_BOT_TOKEN environment variable not set!"**
- Make sure you've set the environment variable before running
- Or create a `.env` file with `DISCORD_BOT_TOKEN=your_token`

**Bot doesn't respond to commands**
- Make sure slash commands are synced (should show in console on startup)
- Verify bot has permissions in the server (Send Messages, Embed Links)
- Try re-inviting bot to server with correct OAuth2 URL

**Can't find the /answer command**
- Make sure you're in the same Discord channel where the question was posted
- Type `/` to see available slash commands - `/answer` should appear
- If it doesn't appear, the bot may not have synced commands properly

**Scores not saving**
- Check that `scores.json` is in the same directory as `bot.py`
- Ensure the bot has write permissions to the directory

## Advanced Usage

### Hosting 24/7
Use a service like:
- **Heroku** (free tier limited)
- **Railway.app**
- **Replit**
- **Your own VPS**

Search "discord.py hosting" for guides.

### Customizing Scoring
Edit the `points_table` in `bot.py`:
```python
points_table = [5, 3, 1]  # 5pts for 1st, 3pts for 2nd, 1pt for 3rd
```

## License

Free to use and modify for your server!
