# eidolon_discord_bridge.py

import discord
import asyncio
import os
from eidolon.core.ai_handler import ask_server

TOKEN = os.getenv("DISCORD_BOT_TOKEN")  # store your token securely in environment
TRIGGER = "!eidolon"

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"✅ Eidolon Discord Bridge online as {client.user}")

@client.event
async def on_message(message):
    print(f"📥 Received message: {message.content} from {message.author}")

    if message.author.bot:
        return

    if message.content.startswith(TRIGGER):
        print("⚡ Trigger detected, processing prompt...")

        prompt = message.content[len(TRIGGER):].strip()
        await message.channel.send("⏳ Thinking...")

        try:
            # Create a messages list with the user's prompt
            messages = [{"role": "user", "content": prompt}]
            print(f"🧠 Sending to ask_server: {prompt}")

            response = ask_server(messages)

            print(f"✅ Received response: {response}")

            if len(response) > 1900:
                response = response[:1900] + "..."

            await message.channel.send(response)

        except Exception as e:
            error_msg = f"⚠️ Error: {e}"
            await message.channel.send(error_msg)
            print(error_msg)

if __name__ == "__main__":
    if not TOKEN:
        TOKEN = input("Enter your Discord Bot Token: ")
    client.run(TOKEN)
