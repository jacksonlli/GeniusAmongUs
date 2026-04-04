#!/usr/bin/env python3
"""
Setup script for Discord Trivia Bot
Helps configure the bot token and validates setup
"""

import os
import sys

def check_requirements():
    """Check if required packages are installed"""
    print("🔍 Checking requirements...")

    try:
        import discord
        print("✅ discord.py installed")
    except ImportError:
        print("❌ discord.py not installed")
        print("   Run: pip install -r requirements.txt")
        return False

    try:
        import dotenv
        print("✅ python-dotenv installed")
    except ImportError:
        print("❌ python-dotenv not installed")
        print("   Run: pip install -r requirements.txt")
        return False

    return True

def setup_token():
    """Help user set up Discord bot token"""
    print("\n🤖 Discord Bot Token Setup")
    print("-" * 30)

    # Check for existing token
    token = os.getenv("DISCORD_BOT_TOKEN")

    if not token:
        # Check .env file
        env_file = ".env"
        if os.path.exists(env_file):
            try:
                with open(env_file, "r") as f:
                    for line in f:
                        if line.startswith("DISCORD_BOT_TOKEN="):
                            token = line.split("=", 1)[1].strip()
                            break
            except:
                pass

    if token and token != "your_bot_token_here":
        print("✅ Bot token appears to be configured")
        print("   Token:", "*" * (len(token)-4) + token[-4:] if len(token) > 4 else token)
        return True

    print("❌ Bot token not configured")
    print("\n📋 To set up your bot token:")
    print("1. Go to https://discord.com/developers/applications")
    print("2. Create a new application or select existing")
    print("3. Go to 'Bot' section")
    print("4. Click 'Add Bot' if needed")
    print("5. Under 'Token', click 'Copy'")
    print("\nChoose setup method:")

    while True:
        print("\n1. Set environment variable (temporary)")
        print("2. Create .env file (recommended)")
        print("3. Skip for now")

        choice = input("\nEnter choice (1-3): ").strip()

        if choice == "1":
            token = input("Paste your bot token: ").strip()
            if token:
                os.environ["DISCORD_BOT_TOKEN"] = token
                print("✅ Environment variable set (temporary)")
                return True
            else:
                print("❌ No token provided")

        elif choice == "2":
            token = input("Paste your bot token: ").strip()
            if token:
                with open(".env", "w") as f:
                    f.write(f"DISCORD_BOT_TOKEN={token}\n")
                print("✅ .env file created")
                print("   Token saved to .env file")
                return True
            else:
                print("❌ No token provided")

        elif choice == "3":
            print("⏭️  Skipping token setup")
            return False

        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")

def validate_files():
    """Check if required files exist"""
    print("\n📁 Checking files...")

    required_files = ["bot.py", "questions.json", "requirements.txt"]
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")
            return False

    # Check questions.json content
    try:
        import json
        with open("questions.json", "r") as f:
            data = json.load(f)
            if isinstance(data, dict) and "questions" in data:
                count = len(data["questions"])
            elif isinstance(data, list):
                count = len(data)
            else:
                count = 0

            if count > 0:
                print(f"✅ questions.json contains {count} questions")
            else:
                print("⚠️  questions.json exists but no questions found")
    except:
        print("❌ questions.json is not valid JSON")

    return True

def run_tests():
    """Run the test suite"""
    print("\n🧪 Running tests...")

    try:
        import subprocess
        result = subprocess.run([sys.executable, "test_bot.py"],
                              capture_output=True, text=True, cwd=os.getcwd())

        if result.returncode == 0:
            print("✅ All tests passed!")
            return True
        else:
            print("⚠️  Some tests failed:")
            print(result.stdout)
            if result.stderr:
                print("Errors:", result.stderr)
            return False
    except Exception as e:
        print(f"❌ Could not run tests: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Discord Trivia Bot Setup")
    print("=" * 40)

    steps = [
        ("Check Requirements", check_requirements),
        ("Validate Files", validate_files),
        ("Setup Bot Token", setup_token),
        ("Run Tests", run_tests),
    ]

    completed = 0
    for step_name, step_func in steps:
        try:
            if step_func():
                completed += 1
            else:
                print(f"\n⚠️  {step_name} had issues")
        except Exception as e:
            print(f"\n❌ {step_name} failed: {e}")

    print("\n" + "=" * 40)
    print(f"📊 Setup Complete: {completed}/{len(steps)} steps successful")

    if completed == len(steps):
        print("\n🎉 Setup complete! You can now run:")
        print("   python bot.py")
    else:
        print("\n⚠️  Setup incomplete. Please resolve the issues above.")

    return completed == len(steps)

if __name__ == "__main__":
    success = main()
    input("\nPress Enter to exit...")
    sys.exit(0 if success else 1)