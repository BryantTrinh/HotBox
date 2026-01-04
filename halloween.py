import discord
import json
from discord.ext import commands
from discord.ui import View, Button, button
from discord import Interaction
import random
import datetime
import os
from dotenv import load_dotenv
import asyncio

# -------------------------------
# LOAD ENVIRONMENT VARIABLES
# -------------------------------
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# -------------------------------
# CONFIG
# -------------------------------
#--- booster ch: 1420601193222111233
TARGET_CHANNEL_IDS = [1420560553008697474, 1420601193222111233]  # multiple channels
COMMAND_PREFIX = "!"
COOLDOWN_SECONDS = 30 * 24 * 60 * 60  # 30 days in seconds for !open
TRICK_COOLDOWN_SECONDS = 30 * 60      # 30 minutes in seconds for !trickortreat
DATA_FILE = "loot_data.json"
LOOT_EMOJIS = {
    "Tickets": "🎟️",
    "Bits": "💠",
    "Gold": "💰",
    "Excellent Dust": "✨",
    "Mint Dust": "🍃",
    "Unopened Dye": "🎨"
}
# User IDs who bypass cooldown
COOLDOWN_BYPASS_USERS = {296181275344109568, 1370076515429253264}

# Loot table with chances (%) and reward ranges
LOOT_TABLE = [
    ("Tickets", (1, 5), 5),
    ("Bits", (500, 1000), 30),
    ("Gold", (500, 1000), 15),
    ("Excellent Dust", (5, 15), 23),
    ("Mint Dust", (5, 15), 22),
    ("Unopened Dye", (1, 3), 5)
]

# -------------------------------
# BOT SETUP
# -------------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents, help_command=None, case_insensitive=True)

# -------------------------------
# DATA STORAGE
# -------------------------------
user_cooldowns = {}      # user_id: datetime (UTC aware) for !open
trick_cooldowns = {}     # user_id: datetime (UTC aware) for !trickortreat
user_loot_history = {}   # user_id: list of (item, value, timestamp)

def load_data():
    global user_cooldowns, user_loot_history
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                raw_data = f.read()
                data = json.loads(raw_data)
                
            user_cooldowns = {
                int(k): datetime.datetime.fromisoformat(v).astimezone(datetime.timezone.utc)
                for k, v in data.get("cooldowns", {}).items()
            }
            user_loot_history = {
                int(k): [
                    (i, v, datetime.datetime.fromisoformat(t).astimezone(datetime.timezone.utc))
                    for i, v, t in v_list
                ]
                for k, v_list in data.get("history", {}).items()
            }

        except json.JSONDecodeError as e:
            print(f"[WARNING] loot_data.json is corrupted: {e}. Attempting partial recovery...")
            try:
                recovered_data = None
                for line in raw_data.splitlines():
                    try:
                        recovered_data = json.loads(line)
                        break
                    except:
                        continue
                if recovered_data:
                    user_cooldowns = {
                        int(k): datetime.datetime.fromisoformat(v).astimezone(datetime.timezone.utc)
                        for k, v in recovered_data.get("cooldowns", {}).items()
                    }
                    user_loot_history = {
                        int(k): [
                            (i, v, datetime.datetime.fromisoformat(t).astimezone(datetime.timezone.utc))
                            for i, v, t in v_list
                        ]
                        for k, v_list in recovered_data.get("history", {}).items()
                    }
                    print("[INFO] Successfully recovered partial data.")
                else:
                    print("[ERROR] Could not recover any data. Please fix loot_data.json manually.")
            except Exception as ex:
                print(f"[ERROR] Failed to recover data: {ex}")

def save_data():
    data = {
        "cooldowns": {str(k): v.isoformat() for k, v in user_cooldowns.items()},
        "history": {
            str(k): [(i, v, t.isoformat()) for i, v, t in v_list]
            for k, v_list in user_loot_history.items()
        },
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
    for guild in bot.guilds:
        for channel_id in TARGET_CHANNEL_IDS:
            channel = guild.get_channel(channel_id)
            if channel:
                await channel.send(f"{bot.user.mention} is now online!")

# -------------------------------
# OFFLINE NOTIFICATION
# -------------------------------
async def notify_offline():
    for guild in bot.guilds:
        for channel_id in TARGET_CHANNEL_IDS:
            channel = guild.get_channel(channel_id)
            if channel:
                try:
                    await channel.send(f"{bot.user.mention} is now offline!")
                except Exception as e:
                    print(f"Failed to send offline message to {channel_id}: {e}")

# -------------------------------
# COMMANDS
# -------------------------------

@bot.command(name="open")
async def open_lootbox(ctx):
    try:
        if ctx.channel.id not in TARGET_CHANNEL_IDS:
            return

        # Check if user is a Nitro Booster
        if not ctx.author.premium_since:
            await ctx.send(f"{ctx.author.mention}, only **server boosters** can use `!open` 💖")
            return

        user_id = ctx.author.id
        now = datetime.datetime.now(datetime.timezone.utc)


        # --- Cooldown check ---
        if user_id not in COOLDOWN_BYPASS_USERS and user_id in user_cooldowns:
            last_open = user_cooldowns[user_id]
            elapsed = (now - last_open).total_seconds()
            if elapsed < COOLDOWN_SECONDS:
                next_time = last_open + datetime.timedelta(seconds=COOLDOWN_SECONDS)
                unix_time = int(next_time.timestamp())
                formatted_time = f"<t:{unix_time}:f>"

                cd_embed = discord.Embed(
                    description=f"{ctx.author.mention}, you must wait until {formatted_time} to open another lootbox!",
                    color=0xFFC0CB
                )
                cd_embed.set_image(url="https://media.giphy.com/media/PivShcAVhKARq/giphy.gif")
                await ctx.send(embed=cd_embed)
                return

        # --- Roll loot (the actual prize) ---
        item, value = roll_loot()
        emoji = LOOT_EMOJIS.get(item, "🎁")

        # Update cooldown + history
        if user_id not in COOLDOWN_BYPASS_USERS:
            user_cooldowns[user_id] = now
        if user_id not in user_loot_history:
            user_loot_history[user_id] = []
        user_loot_history[user_id].append((item, value, now))

        # Save asynchronously
        asyncio.create_task(asyncio.to_thread(save_data))

        # --- Initial embed ---
        spin_items = list(LOOT_EMOJIS.values())
        embed = discord.Embed(
            title="<a:kawaiiStarsSparkle:1420989584895905903>Praying ♡",
            description="Spinning...",
            color=0xFFC5D3,
        )
        slot_message = await ctx.send(embed=embed)

        # --- Quick animation ---
        for _ in range(3):
            reels = [random.choice(spin_items) for _ in range(3)]
            embed.description = f"<a:PinkDice:1420985419704700938> | {reels[0]}   {reels[1]}   {reels[2]}"
            await slot_message.edit(embed=embed)
            await asyncio.sleep(0.08)

        # --- Final prize (AFTER loop finishes) ---
        embed.description = f"<a:PinkDice:1420985419704700938> | {emoji}   {emoji}   {emoji}"
        await slot_message.edit(embed=embed)

        # --- Congrats embed ---
        gif_url = "https://cdn.discordapp.com/attachments/1321372597572599869/1420574912245923870/IMG_9434.gif"
        final_embed = discord.Embed(
            title="**Congrats** <:3z_vdayboxP2U:1420544327817629786>",
            description=(
                f"**You've won {value} {item} <a:pinkhearts:1420576070138073149>** \n\n"
                "-# Please open a ticket in <#1412934283613700136> to claim. \n\n"
                "-# *Open another chest in 30 days!* <a:pinkhearts:1420576070138073149>"
            ),
            color=0xFFC5D3,
        )
        final_embed.set_thumbnail(url=gif_url)

        # small pause just for effect
        await asyncio.sleep(0.3)
        await slot_message.edit(embed=final_embed)

    except Exception:
        import traceback
        traceback.print_exc()

#----------------------------------------------
# Halloween EVENT for Boosters and Non-Boosters
#----------------------------------------------
@bot.command(name="trickortreat")
async def trick_or_treat(ctx):
    try:
        if ctx.channel.id not in TARGET_CHANNEL_IDS:
            return

        user_id = ctx.author.id
        now = datetime.datetime.now(datetime.timezone.utc)

        # --- Cooldown check ---
        if user_id not in COOLDOWN_BYPASS_USERS and user_id in trick_cooldowns:
            last_open = trick_cooldowns[user_id]
            elapsed = (now - last_open).total_seconds()
            if elapsed < TRICK_COOLDOWN_SECONDS:
                next_time = last_open + datetime.timedelta(seconds=TRICK_COOLDOWN_SECONDS)
                unix_time = int(next_time.timestamp())
                formatted_time = f"<t:{unix_time}:f>"

                cd_embed = discord.Embed(
                    description=f"{ctx.author.mention}, you must wait until {formatted_time} to go trick-or-treating again!",
                    color=0xFF7518  # Pumpkin orange 🎃
                )
                cd_embed.set_image(url="https://media.giphy.com/media/T8Dfbp7amklQk/giphy.gif")
                await ctx.send(embed=cd_embed)
                return

        # --- Roll Halloween candy ---
        candy_amount = random.randint(1, 25)
        candy_name = "Halloween Candy 🍬"

        # Update cooldown + history
        if user_id not in COOLDOWN_BYPASS_USERS:
            trick_cooldowns[user_id] = now
        if user_id not in user_loot_history:
            user_loot_history[user_id] = []
        user_loot_history[user_id].append((candy_name, candy_amount, now))

        asyncio.create_task(asyncio.to_thread(save_data))

        # --- Result embed ---
        embed = discord.Embed(
            title="🎃 Trick or Treat!",
            description=f"{ctx.author.mention}, you got **{candy_amount} {candy_name}**!",
            color=0xFF7518
        )
        embed.set_thumbnail(url="https://media.giphy.com/media/WyAFMfpFSB6Bq/giphy.gif")  # Pusheen Halloween GIF
        await ctx.send(embed=embed)

    except Exception:
        import traceback
        traceback.print_exc()

@bot.command(name="candy")
async def candy_total(ctx):
    """Show total Halloween Candy collected over time."""
    user_id = ctx.author.id
    total_candy = 0

    if user_id in user_loot_history:
        total_candy = sum(value for item, value, _ in user_loot_history[user_id] if "Halloween Candy" in item)

    embed = discord.Embed(
        title="🍬 Halloween Candy Collected",
        description=f"{ctx.author.mention}, you have collected a total of **{total_candy} Halloween Candy 🍬** so far!",
        color=0xFF69B4
    )
    embed.set_thumbnail(url="https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHhuOWxrajN6dWx6djFodDg0MDN4OHJtZnp4YW1sbmdwZHpqcjUyZSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/8RppzuEQJ40BpxDL2Y/giphy.gif")
    await ctx.send(embed=embed)

@bot.command(name="history")
async def loot_history(ctx):
    user_id = ctx.author.id
    if user_id not in user_loot_history or len(user_loot_history[user_id]) == 0:
        await ctx.send(f"{ctx.author.mention}, you haven't opened any lootboxes yet!")
        return

    # Filter out Halloween Candy 🍬 from history
    filtered_history = [entry for entry in user_loot_history[user_id] if "Halloween Candy" not in entry[0]]

    if len(filtered_history) == 0:
        await ctx.send(f"{ctx.author.mention}, you haven't opened any **booster lootboxes** yet!")
        return

    history = list(reversed(filtered_history))
    items_per_page = 5
    total_pages = (len(history) + items_per_page - 1) // items_per_page
    thumbnail_url = "https://cdn.discordapp.com/attachments/1321372597572599869/1420595192150622409/IMG_9439.gif"

    class LootHistoryView(View):
        def __init__(self):
            super().__init__(timeout=120)
            self.current_page = 0

        async def update_message(self, interaction: Interaction):
            start_index = self.current_page * items_per_page
            end_index = start_index + items_per_page
            page_items = history[start_index:end_index]

            lines = [f"{ts.strftime('%Y-%m-%d %H:%M:%S')}: {value} {item}" for item, value, ts in page_items]

            embed = discord.Embed(
                title=f"<:hnote1:1420592325817663570> {ctx.author.display_name}'s Loot History (Page {self.current_page + 1}/{total_pages})",
                description="\n".join(lines),
                color=0xFFDBE5,
            )
            embed.set_thumbnail(url=thumbnail_url)

            self.previous.disabled = self.current_page == 0
            self.next.disabled = self.current_page == total_pages - 1

            await interaction.response.edit_message(embed=embed, view=self)

        @button(label="◀️", style=discord.ButtonStyle.secondary)
        async def previous(self, interaction: Interaction, button: Button):
            if self.current_page > 0:
                self.current_page -= 1
                await self.update_message(interaction)

        @button(label="▶️", style=discord.ButtonStyle.secondary)
        async def next(self, interaction: Interaction, button: Button):
            if self.current_page < total_pages - 1:
                self.current_page += 1
                await self.update_message(interaction)

    view = LootHistoryView()
    page_items = history[:items_per_page]
    lines = [f"{ts.strftime('%Y-%m-%d %H:%M:%S')}: {value} {item}" for item, value, ts in page_items]

    embed = discord.Embed(
        title=f"<:hnote1:1420592325817663570> {ctx.author.display_name}'s Loot History (Page 1/{total_pages})",
        description="\n".join(lines),
        color=0xFFDBE5,
    )
    embed.set_thumbnail(url=thumbnail_url)
    await ctx.send(embed=embed, view=view)

@bot.command(name="cooldown")
async def check_cooldown(ctx):
    user_id = ctx.author.id
    now = datetime.datetime.now(datetime.timezone.utc)

    if user_id not in user_cooldowns:
        await ctx.send(f"{ctx.author.mention}, you can open a lootbox right now!")
        return

    last_open = user_cooldowns[user_id]
    elapsed = (now - last_open).total_seconds()

    if elapsed >= COOLDOWN_SECONDS:
        await ctx.send(f"{ctx.author.mention}, you can open a lootbox right now!")
    else:
        next_time = last_open + datetime.timedelta(seconds=COOLDOWN_SECONDS)
        unix_time = int(next_time.timestamp())
        formatted_time = f"<t:{unix_time}:f>"

        embed = discord.Embed(
            title="Oops! You're Still On Cooldown! <:024_bear_clock_time:1420541982094266480>",
            color=0xFFFFFF,
        )
        embed.add_field(
            name="\u200b",
            value=f"<a:h1flower:1398829165503053957> You can open another chest again on: {formatted_time}",
            inline=False,
        )
        embed.add_field(
            name="\u200b",
            value="<a:h1flower:1398829165503053957> *Thank you for boosting us, cutie!*",
            inline=False,
        )
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/1321372597572599869/1420546860569071768/IMG_9417.jpg"
        )
        await ctx.send(embed=embed)

@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(
        title="<a:hnote3:1420614028514033685> Bot Commands",
        description="Here are all the commands you can use:",
        color=0xF1DBB6
    )
    embed.add_field(name="!open", value="Open a lootbox! Can only be used once every 30 days.", inline=False)
    embed.add_field(name="!history", value="View your lootbox history with paging buttons.", inline=False)
    embed.add_field(name="!cooldown", value="Check how long until you can open your next lootbox.", inline=False)
    embed.add_field(name="!help", value="Show this help message with all available commands.", inline=False)
    embed.add_field(name="!prize", value="This shows list of available prizes.", inline=False)
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1420560553008697474/1420613932288180265/IMG_9442.jpg")
    await ctx.send(embed=embed)

@bot.command(name="help2")
async def help_command(ctx):
    is_booster = bool(ctx.author.premium_since)

    embed = discord.Embed(
        title="💖 Bot Commands",
        description="Here’s what you can do!",
        color=0xFFC0CB
    )

    if is_booster:
        # Booster-only view
        embed.add_field(
            name="🌸 Booster-Only Commands",
            value=(
                "`!open` — Open a lootbox (Cooldown: 30 days)\n"
                "`!history` — View your loot history\n"
                "`!cooldown` — Check your remaining cooldowns\n"
                "`!prize` — Learn how to claim your rewards"
            ),
            inline=False
        )

    # Everyone commands
    embed.add_field(
        name="🍬 Everyone Commands",
        value=(
            "`!trickortreat` — Collect Halloween Candy (Cooldown: 30 minutes)\n"
            "`!candy` — See how much candy you’ve collected"
        ),
        inline=False
    )

    if not is_booster:
        embed.set_footer(text="💎 Boost the server to unlock exclusive lootbox rewards & commands!")

    await ctx.send(embed=embed)

@bot.command(name="prize")
async def prize_command(ctx):
    embed = discord.Embed(
        title="<a:BunnyBook:1420995026741104804> List of Prizes",
        description="\n",
        color=0xF1DBB6
    )
    embed.add_field(name="Tickets 🎟️", value="\u200b", inline=False)
    embed.add_field(name="Bits 💠", value="\u200b", inline=False)
    embed.add_field(name="Gold 💰", value="\u200b", inline=False)
    embed.add_field(name="Excellent Dust ✨", value="\u200b", inline=False)
    embed.add_field(name="Mint Dust 🍃", value="\u200b", inline=False)
    embed.add_field(name="Unopened Dye 🎨", value="\u200b", inline=False)
    embed.set_thumbnail(
        url="https://cdn.discordapp.com/attachments/1420560553008697474/1420993021972840468/IMG_9468.gif?ex=68d76a61&is=68d618e1&hm=4e681ce1f4fa398443d0363c8397197edaa1880c9057739893eb0025ef614b3e&"
    )
    await ctx.send(embed=embed)


# -------------------------------
# RUN BOT WITH OFFLINE NOTIFICATION
# -------------------------------
async def main():
    try:
        await bot.start(TOKEN)
    finally:
        await notify_offline()

asyncio.run(main())
