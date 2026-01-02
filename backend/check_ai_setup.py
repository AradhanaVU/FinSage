"""Simple script to check which AI provider is configured"""
import os
from dotenv import load_dotenv

load_dotenv()

print("\n" + "="*60)
print("AI PROVIDER CONFIGURATION CHECK")
print("="*60 + "\n")

gemini_key = os.getenv("GEMINI_API_KEY")
openai_key = os.getenv("OPENAI_API_KEY")

if gemini_key:
    print("[OK] GEMINI_API_KEY is set")
    print(f"  Key starts with: {gemini_key[:10]}..." if len(gemini_key) > 10 else "  Key is too short")
else:
    print("[NOT SET] GEMINI_API_KEY is not set")

print()

if openai_key:
    print("[OK] OPENAI_API_KEY is set")
    print(f"  Key starts with: {openai_key[:10]}..." if len(openai_key) > 10 else "  Key is too short")
else:
    print("[NOT SET] OPENAI_API_KEY is not set")

print("\n" + "-"*60)

if gemini_key:
    print("\n[WILL USE] GEMINI (preferred)")
elif openai_key:
    print("\n[WILL USE] OPENAI")
else:
    print("\n[WARNING] FALLBACK responses (no API keys set)")

print("\nTo set up Gemini:")
print("1. Get a free API key: https://makersuite.google.com/app/apikey")
print("2. Create/edit backend/.env file")
print("3. Add: GEMINI_API_KEY=your_key_here")
print("4. Restart the backend server")

print("\n" + "="*60 + "\n")

