import discord
import json
from discord.ext import commands
import random
import datetime
import os
from dotenv import load_dotenv

# -------------------------------
# LOAD ENVIRONMENT VARIABLES
# -------------------------------
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# -------------------------------
# CONFIG
# -------------------------------
TARGET_CHANNEL = "boosters"
COMMAND_PREFIX = "!"
COOLDOWN_SECONDS = 30
#COOLDOWN_SECONDS = 30 * 24 * 60 * 60  # 30 days in seconds
DATA_FILE = "loot_data.json"

# Loot table with chances (%) and reward ranges
LOOT_TABLE = [
    ("Tickets", (1, 5), 15),
    ("Bits", (100, 1000), 25),
    ("Gold", (1000, 5000), 15),
    ("Good Dust", (1, 25), 10),
    ("Excellent Dust", (1, 25), 8),
    ("Poor Dust", (1, 25), 10),
    ("Mint Dust", (1, 25), 7),
]

# -------------------------------
# BOT SETUP
# -------------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

# -------------------------------
# DATA STORAGE
# -------------------------------
user_cooldowns = {}  # user_id: datetime
user_loot_history = {}  # user_id: list of (item, value, timestamp)

def load_data():
    global user_cooldowns, user_loot_history
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            user_cooldowns = {int(k): datetime.datetime.fromisoformat(v) for k, v in data.get("cooldowns", {}).items()}
            user_loot_history = {int(k): [(i, v, datetime.datetime.fromisoformat(t)) for i, v, t in v_list]
                                 for k, v_list in data.get("history", {}).items()}

def save_data():
    data = {
        "cooldowns": {str(k): v.isoformat() for k, v in user_cooldowns.items()},
        "history": {str(k): [(i, v, t.isoformat()) for i, v, t in v_list] for k, v_list in user_loot_history.items()}
    }
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Load data on startup
load_data()

# -------------------------------
# LOOT FUNCTION
# -------------------------------
def roll_loot():
    items = [item for item, _, _ in LOOT_TABLE]
    ranges = {item: rng for item, rng, _ in LOOT_TABLE}
    weights = [chance for _, _, chance in LOOT_TABLE]

    reward_item = random.choices(items, weights=weights, k=1)[0]
    low, high = ranges[reward_item]

    # Skew towards lower numbers
    exp = 3
    u = random.random() ** exp
    reward_value = low + int(u * (high - low))

    return reward_item, reward_value

# -------------------------------
# EVENTS
# -------------------------------
@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.channel.name == TARGET_CHANNEL:
        print(f"[{datetime.datetime.now()}] {message.author}: {message.content}")

    await bot.process_commands(message)

# -------------------------------
# COMMANDS
# -------------------------------
@bot.command(name="open", aliases=["Open", "OPEN"])
async def open_lootbox(ctx):
    if ctx.channel.name != TARGET_CHANNEL:
        return

    user_id = ctx.author.id
    now = datetime.datetime.now()

    # Check cooldown
    if user_id in user_cooldowns:
        last_open = user_cooldowns[user_id]
        elapsed = (now - last_open).total_seconds()
        if elapsed < COOLDOWN_SECONDS:
            next_time = last_open + datetime.timedelta(seconds=COOLDOWN_SECONDS)
            formatted_time = next_time.strftime("%A, %B %d, %Y at %I:%M:%S %p")
            await ctx.send(f"{ctx.author.mention}, you must wait until **{formatted_time}** to open another lootbox!")
            return

    # Roll loot
    item, value = roll_loot()

    # Update cooldown and history
    user_cooldowns[user_id] = now
    if user_id not in user_loot_history:
        user_loot_history[user_id] = []
    user_loot_history[user_id].append((item, value, now))

    # Persist data
    save_data()

    await ctx.send(f"🎉 {ctx.author.mention} opened a lootbox and received **{value} {item}**!")

@bot.command(name="history")
async def loot_history(ctx):
    user_id = ctx.author.id
    if user_id not in user_loot_history or len(user_loot_history[user_id]) == 0:
        await ctx.send(f"{ctx.author.mention}, you haven't opened any lootboxes yet!")
        return

    lines = []
    for item, value, ts in user_loot_history[user_id]:
        timestamp = ts.strftime("%Y-%m-%d %H:%M:%S")
        lines.append(f"{timestamp}: {value} {item}")

    history_message = "\n".join(lines)
    if len(history_message) > 1900:
        history_message = history_message[:1900] + "\n…"

    await ctx.send(f"📜 {ctx.author.mention}'s loot history:\n{history_message}")

@bot.command(name="cooldown")
async def check_cooldown(ctx):
    user_id = ctx.author.id
    now = datetime.datetime.now()
    
    if user_id not in user_cooldowns:
        await ctx.send(f"{ctx.author.mention}, you can open a lootbox right now!")
        return

    last_open = user_cooldowns[user_id]
    elapsed = (now - last_open).total_seconds()
    
    if elapsed >= COOLDOWN_SECONDS:
        await ctx.send(f"{ctx.author.mention}, you can open a lootbox right now!")
    else:
        next_time = last_open + datetime.timedelta(seconds=COOLDOWN_SECONDS)
        formatted_time = next_time.strftime("%A, %B %d, %Y at %I:%M:%S %p")

        embed = discord.Embed(
            title="Oops! You're Still On Cooldown! <:024_bear_clock_time:1420541982094266480>",
            color=0xFF69B4
        )
        embed.add_field(
            name="\u200b",
            value="<a:h1flower:1398829165503053957> You can open another chest again on:\n"
                  f"{formatted_time}",
            inline=False
        )
        embed.add_field(
            name="\u200b",
            value="<a:h1flower:1398829165503053957> Thank you for boosting us, cutie!",
            inline=False
        )
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/1321372597572599869/1420546860569071768/IMG_9417.jpg"
        )

        await ctx.send(embed=embed)


# -------------------------------
# RUN BOT
# -------------------------------
bot.run(TOKEN)