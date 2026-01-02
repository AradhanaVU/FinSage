"""List available Gemini models"""
import os
from dotenv import load_dotenv

load_dotenv()

gemini_key = os.getenv("GEMINI_API_KEY")

print("Listing available Gemini models...\n")

try:
    import google.generativeai as genai
    genai.configure(api_key=gemini_key)
    
    print("Available models:")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"  - {m.name}")
    
except Exception as e:
    print(f"Error: {e}")


