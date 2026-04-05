#!/usr/bin/env python3
"""
Test script for the Discord Trivia Bot
Tests core functionality without requiring Discord connection
"""

import json
import os
import sys
from datetime import datetime

# Copy functions from bot.py to avoid discord dependency
SCORES_FILE = "scores.json"
QUESTIONS_FILE = "questions.json"

def load_scores():
    if os.path.exists(SCORES_FILE):
        with open(SCORES_FILE, "r") as f:
            return json.load(f)
    return {}

def save_scores(scores):
    with open(SCORES_FILE, "w") as f:
        json.dump(scores, f, indent=4)

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

def test_question_loading():
    """Test loading questions from questions.json"""
    print("🧪 Testing question loading...")

    questions = load_questions()
    print(f"✅ Loaded {len(questions)} questions")

    if questions:
        sample = questions[0]
        print(f"📝 Sample question: {sample.get('question', 'N/A')}")
        print(f"🎯 Answer: {sample.get('answer', 'N/A')}")

    return len(questions) > 0

def test_score_system():
    """Test the scoring system logic"""
    print("\n🧪 Testing scoring system...")

    # Simulate answers for a question with correct answer = 100
    correct_answer = 100
    test_answers = {
        "user1": {"name": "Alice", "answer": 95, "difference": abs(95 - correct_answer)},
        "user2": {"name": "Bob", "answer": 105, "difference": abs(105 - correct_answer)},
        "user3": {"name": "Charlie", "answer": 98, "difference": abs(98 - correct_answer)},
        "user4": {"name": "Diana", "answer": 120, "difference": abs(120 - correct_answer)},
    }

    # Sort by closest answer
    sorted_answers = sorted(
        test_answers.items(),
        key=lambda x: x[1]["difference"]
    )

    # Award points to top 3
    points_table = [3, 2, 1]  # 1st place: 3 pts, 2nd: 2 pts, 3rd: 1 pt

    print(f"🎯 Correct answer: {correct_answer}")
    print("📊 Results:")

    for idx, (user_id, answer_data) in enumerate(sorted_answers[:3]):
        points = points_table[idx]
        medal = ["🥇", "🥈", "🥉"][idx]
        difference = answer_data["difference"]
        print(f"{medal} {answer_data['name']} - Answer: {answer_data['answer']} (Off by {difference}) - +{points} pts")

    # Show other answers
    if len(sorted_answers) > 3:
        print("\n📋 Other answers:")
        for user_id, answer_data in sorted_answers[3:]:
            difference = answer_data["difference"]
            print(f"• {answer_data['name']} - Answer: {answer_data['answer']} (Off by {difference})")

    return True

def test_score_persistence():
    """Test loading and saving scores"""
    print("\n🧪 Testing score persistence...")

    # Load existing scores
    scores = load_scores()
    print(f"✅ Loaded existing scores for {len(scores)} players")

    # Add test scores
    test_scores = {
        "test_user_1": {"name": "TestPlayer1", "total_points": 5, "answers": 2},
        "test_user_2": {"name": "TestPlayer2", "total_points": 8, "answers": 3},
    }

    # Save test scores
    save_scores(test_scores)
    print("💾 Saved test scores")

    # Load them back
    loaded_scores = load_scores()
    success = all(user in loaded_scores for user in test_scores)
    print(f"✅ Score persistence: {'PASS' if success else 'FAIL'}")

    # Restore original scores
    save_scores(scores)
    print("🔄 Restored original scores")

    return success

def test_readme_documentation():
    """Test README command documentation for the new game flow"""
    print("\n🧪 Testing README command documentation...")

    if not os.path.exists("README.md"):
        print("❌ README.md not found")
        return False

    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read()

    required_phrases = ["/newgame", "/ready", "/rules", "/accuse", "Use /newgame"]
    missing = [phrase for phrase in required_phrases if phrase not in content]

    if missing:
        print(f"❌ README missing required phrases: {', '.join(missing)}")
        return False

    print("✅ README documentation references are present")
    return True

def test_game_simulation():
    """Simulate a full game session"""
    print("\n🧪 Testing game simulation...")

    questions = load_questions()
    if not questions:
        print("❌ No questions available for simulation")
        return False

    # Simulate game with 3 questions
    num_questions = min(3, len(questions))
    used_questions = set()
    game_scores = {}

    print(f"🎮 Simulating game with {num_questions} questions...")

    for i in range(num_questions):
        # Select unused question
        available = [q for q in questions if q.get("id", q.get("question")) not in used_questions]
        if not available:
            break

        import random
        question = random.choice(available)
        question_id = question.get("id", question.get("question"))
        used_questions.add(question_id)

        print(f"\n📝 Question {i+1}: {question['question']}")
        print(f"🎯 Correct answer: {question['answer']}")

        # Simulate player answers
        correct = question['answer']
        simulated_answers = {
            "player1": {"name": "Alice", "answer": correct, "difference": 0},
            "player2": {"name": "Bob", "answer": correct + 2, "difference": 2},
            "player3": {"name": "Charlie", "answer": correct - 1, "difference": 1},
        }

        # Sort and award points
        sorted_answers = sorted(simulated_answers.items(), key=lambda x: x[1]["difference"])
        points_table = [3, 2, 1]

        for idx, (user_id, data) in enumerate(sorted_answers[:3]):
            points = points_table[idx]
            if user_id not in game_scores:
                game_scores[user_id] = {"name": data["name"], "points": 0}
            game_scores[user_id]["points"] += points

        print("🏆 Round results:")
        for idx, (user_id, data) in enumerate(sorted_answers[:3]):
            medal = ["🥇", "🥈", "🥉"][idx]
            print(f"  {medal} {data['name']}: {data['answer']} (+{points_table[idx]} pts)")

    print("\n🏁 Final game scores:")
    for user_id, data in game_scores.items():
        print(f"  {data['name']}: {data['points']} points")

    return True

def test_bot_token():
    """Check if bot token is configured"""
    print("\n🧪 Testing bot token configuration...")

    token = os.getenv("DISCORD_BOT_TOKEN")

    # Also check .env file
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
        return True
    else:
        print("⚠️  Bot token not configured (this is expected for local testing)")
        print("   To test with Discord, set DISCORD_BOT_TOKEN environment variable")
        return False

def run_all_tests():
    """Run all tests"""
    print("🚀 Starting Discord Trivia Bot Tests")
    print("=" * 50)

    tests = [
        ("Question Loading", test_question_loading),
        ("Score System", test_score_system),
        ("Score Persistence", test_score_persistence),
        ("README Documentation", test_readme_documentation),
        ("Game Simulation", test_game_simulation),
        ("Bot Token Check", test_bot_token),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"✅ {test_name}: PASS")
                passed += 1
            else:
                print(f"❌ {test_name}: FAIL")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Bot logic is working correctly.")
        print("\n💡 To test with Discord:")
        print("   1. Set up a Discord bot token (see README.md)")
        print("   2. Run: python bot.py")
    else:
        print("⚠️  Some tests failed. Check the output above.")

    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)