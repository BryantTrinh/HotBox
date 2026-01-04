import os
from dotenv import load_dotenv

print("🔍 Loading .env file...")
load_dotenv()

print("🔍 Checking for DISCORD_TOKEN...")
token = os.getenv("DISCORD_TOKEN")

if token:
    print("✅ Token loaded successfully!")
    print(f"First 10 characters: {token[:10]}...")
else:
    print("❌ No token found. Check your .env file.")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Files in this folder: {os.listdir('.')}")
