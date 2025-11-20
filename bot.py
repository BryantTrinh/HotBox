import discord
import json
from discord.ext import commands, tasks
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
COOLDOWN_SECONDS = 14 * 24 * 60 * 60  # 14 days in seconds
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
COOLDOWN_BYPASS_USERS = {296181275344109568, 1370076515429253264, 547733449818243084}

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

bot = commands.Bot(
    command_prefix=COMMAND_PREFIX,
    intents=intents,
    help_command=None,  # disable default help so custom one works
    case_insensitive=True
)

# -------------------------------
# DATA STORAGE
# -------------------------------
user_cooldowns = {}  # user_id: datetime (UTC aware)
user_loot_history = {}  # user_id: list of (item, value, timestamp)

def load_data():
    global user_cooldowns, user_loot_history
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                raw_data = f.read()
                # Attempt to parse JSON
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
                # Try to extract first valid JSON object
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
# COMMAND HELPERS
# -------------------------------
def find_member_by_name_or_id(guild, query: str):
    query_lower = query.lower()

    # --- Check if mention ---
    if query.startswith("<@") and query.endswith(">"):
        try:
            user_id = int(query.strip("<@!>"))
            return guild.get_member(user_id)
        except ValueError:
            return None

    # --- Check if numeric ID ---
    if query.isdigit():
        return guild.get_member(int(query))

    # --- Strict partial match (case-insensitive) ---
    for member in guild.members:
        if query_lower in member.display_name.lower() or query_lower in member.name.lower():
            return member

    return None

# -------------------------------
# MINI GAME
# -------------------------------
class DoubleOrNothingView(View):
    def __init__(self, ctx, user_id, item, value, timestamp):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.user_id = user_id
        self.item = item
        self.value = value
        self.timestamp = timestamp
        self.interaction_message = None
        self.remaining = 30
        self.ended = False  # Track if result already handled

    async def start_timer(self):
        try:
            while self.remaining > 0 and not self.ended:
                await asyncio.sleep(1)
                self.remaining -= 1
                if self.interaction_message and any(not child.disabled for child in self.children):
                    embed = self.build_embed()
                    await self.interaction_message.edit(embed=embed, view=self)

            # Timer reached 0 — auto "Keep"
            if not self.ended and self.interaction_message:
                self.ended = True
                for child in self.children:
                    child.disabled = True
                await self.interaction_message.edit(view=self)

                result_text = f"{self.ctx.author.mention} safely kept **{self.value} {self.item}**."
                gif_url = "https://cdn.discordapp.com/attachments/1420560553008697474/1422085281632489514/CFB31F85-BD99-423B-9BE8-7973659FC0C7.gif"

                result_embed = discord.Embed(
                    title="Double or Nothing Result",
                    description=result_text + "\n\nCreate a ticket to claim your prize in <#1412934283613700136>",
                    color=0xFFC5D3
                )
                result_embed.set_image(url=gif_url)
                await self.interaction_message.edit(embed=result_embed, view=None)

                # Save to history
                user_loot_history.setdefault(self.user_id, []).append(
                    (self.item, self.value, self.timestamp)
                )
                save_data()

        except Exception as e:
            print(f"[Timer error] {e}")

    def build_embed(self):
        return discord.Embed(
            title="🎰 Double or Nothing?",
            description=(
                f"{self.ctx.author.mention}, you won **{self.value} {self.item}!**\n\n"
                f"Do you want to risk it?\n\n"
                f"Pick one: 🎲 (Double) | 🍀 (Keep)\n"
                f"⏳ **Time remaining:** {self.remaining} seconds\n\n"
                f"**Prize:** {self.value} {self.item}"
            ),
            color=0xFFC5D3
        )

    async def show_result_embed(self, interaction: Interaction, result_text: str, gif_url: str):
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)

        if self.value > 0:
            result_text += "\n\nCreate a ticket to claim your prize in <#1412934283613700136>"

        result_embed = discord.Embed(
            title="Double or Nothing Result",
            description=result_text,
            color=0xFFC5D3
        )
        result_embed.set_image(url=gif_url)
        await interaction.response.edit_message(embed=result_embed, view=None)

        if self.value > 0:
            user_loot_history.setdefault(self.user_id, []).append(
                (self.item, self.value, self.timestamp)
            )
            save_data()

    @button(label="🎲 Double", style=discord.ButtonStyle.success)
    async def double_button(self, interaction: Interaction, button: Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ This isn’t your lootbox!", ephemeral=True)

        if random.random() < 0.5:
            self.value *= 2
            result_text = f"🎉 {interaction.user.mention} doubled their reward! Now **{self.value} {self.item}**"
            gif_url = "https://cdn.discordapp.com/attachments/1420560553008697474/1422038487569268747/120AEC33-8409-4DDF-9EA3-D6C95DC0D030.gif"
        else:
            self.value = 0
            result_text = f"💀 {interaction.user.mention} lost it all!"
            gif_url = "https://cdn.discordapp.com/attachments/1420560553008697474/1422040286791733409/IMG_9535.gif"

        await self.show_result_embed(interaction, result_text, gif_url)

    @button(label="🍀 Keep", style=discord.ButtonStyle.secondary)
    async def safe_button(self, interaction: Interaction, button: Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ This isn’t your lootbox!", ephemeral=True)

        result_text = f"{interaction.user.mention} safely kept **{self.value} {self.item}**."
        gif_url = "https://cdn.discordapp.com/attachments/1420560553008697474/1422085281632489514/CFB31F85-BD99-423B-9BE8-7973659FC0C7.gif"
        await self.show_result_embed(interaction, result_text, gif_url)



# -------------------------------
# COMMANDS
# -------------------------------
@bot.command(name="open")
async def open_lootbox(ctx):
    try:
        if ctx.channel.id not in TARGET_CHANNEL_IDS:
            return

        user_id = ctx.author.id
        now = datetime.datetime.now(datetime.timezone.utc)

        # --- Fetch the full Member object ---
        member = ctx.guild.get_member(user_id)
        if member is None:
            member = await ctx.guild.fetch_member(user_id)

        # --- Check Nitro booster / bypass users ---
        if user_id not in COOLDOWN_BYPASS_USERS:
            # Use server boost status
            if not member.premium_since:
                await ctx.send("❌ You must be boosting the server to open a lootbox.")
                return

        # --- Check cooldown / retry ---
        if user_id in pending_retries:
            pending_retries.remove(user_id)
        elif user_id not in COOLDOWN_BYPASS_USERS and user_id in user_cooldowns:
            last_open = user_cooldowns[user_id]
            elapsed = (now - last_open).total_seconds()
            if elapsed < COOLDOWN_SECONDS:
                await ctx.send("⏳ You are on cooldown!")
                return

        # --- Roll loot ---
        item, value = roll_loot()
        user_cooldowns[user_id] = now

        # --- Step 1: Praying animation ---
        praying_embed = discord.Embed(
            title="🌸 Praying ♡",
            description=f"{random.choice(list(LOOT_EMOJIS.values()))}   "
                        f"{random.choice(list(LOOT_EMOJIS.values()))}   "
                        f"{random.choice(list(LOOT_EMOJIS.values()))}",
            color=0xFFC5D3
        )
        message = await ctx.send(embed=praying_embed)
        await asyncio.sleep(0.5)

        # --- Step 2: Spinning animation ---
        spin_embed = discord.Embed(title="🎰 Spinning...", description="| 🎲 💎 💰 |", color=0xFFC5D3)
        await message.edit(embed=spin_embed)

        final_emoji = LOOT_EMOJIS[item]

        # Spin random emojis
        for _ in range(3):
            reels = [random.choice(list(LOOT_EMOJIS.values())) for _ in range(3)]
            spin_embed.description = f"| {reels[0]}   {reels[1]}   {reels[2]} |"
            await message.edit(embed=spin_embed)
            await asyncio.sleep(0.2)

        # Show winning frame
        spin_embed.description = f"| {final_emoji}   {final_emoji}   {final_emoji} |"
        await message.edit(embed=spin_embed)
        await asyncio.sleep(0.5)

        # --- Step 3: Attach DoubleOrNothingView ---
        view = DoubleOrNothingView(ctx, user_id, item, value, now)
        don_embed = view.build_embed()
        view.interaction_message = await ctx.send(embed=don_embed, view=view)
        asyncio.create_task(view.start_timer())

    except Exception:
        import traceback
        traceback.print_exc()




@bot.command(name="history")
async def loot_history(ctx, *, query: str = None):
    if query:
        target = find_member_by_name_or_id(ctx.guild, query)
        if not target:
            await ctx.send(f"❌ Could not find a user matching '{query}'.")
            return
    else:
        target = ctx.author

    user_id = target.id
    if user_id not in user_loot_history or len(user_loot_history[user_id]) == 0:
        await ctx.send(f"{target.mention} hasn't opened any lootboxes yet!")
        return

    history = list(reversed(user_loot_history[user_id]))
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

            lines = [f"{ts.strftime('%Y-%m-%d %H:%M:%S')}: {value} {item}"
                     for item, value, ts in page_items]

            embed = discord.Embed(
                title=f"{target.display_name}'s Loot History (Page {self.current_page + 1}/{total_pages})",
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
        title=f"{target.display_name}'s Loot History (Page 1/{total_pages})",
        description="\n".join(lines),
        color=0xFFDBE5,
    )
    embed.set_thumbnail(url=thumbnail_url)
    await ctx.send(embed=embed, view=view)

@bot.command(name="cooldown")
async def check_cooldown(ctx, *, query: str = None):
    now = datetime.datetime.now(datetime.timezone.utc)

    if query:
        target = find_member_by_name_or_id(ctx.guild, query)
        if not target:
            await ctx.send(f"❌ Could not find a user matching '{query}'.")
            return
    else:
        target = ctx.author

    user_id = target.id
    if user_id not in user_cooldowns:
        await ctx.send(f"{target.mention} can open a lootbox right now!")
        return

    last_open = user_cooldowns[user_id]
    elapsed = (now - last_open).total_seconds()

    if elapsed >= COOLDOWN_SECONDS:
        await ctx.send(f"{target.mention} can open a lootbox right now!")
    else:
        next_time = last_open + datetime.timedelta(seconds=COOLDOWN_SECONDS)
        unix_time = int(next_time.timestamp())
        formatted_time = f"<t:{unix_time}:f>"

        embed = discord.Embed(
            title="Cooldown Active ⏳",
            color=0xFFFFFF,
        )
        embed.add_field(
            name="\u200b",
            value=f"{target.mention} can open another chest on: {formatted_time}",
            inline=False,
        )
        await ctx.send(embed=embed)

@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(
        title="<a:hnote3:1420614028514033685> Bot Commands",
        description="Here are all the commands you can use:",
        color=0xF1DBB6
    )
    embed.add_field(name="!open", value="Open a lootbox! Can only be used once every 14 days.", inline=False)
    embed.add_field(name="!history", value="View your lootbox history with paging buttons.", inline=False)
    embed.add_field(name="!cooldown", value="Check how long until you can open your next lootbox.", inline=False)
    embed.add_field(name="!help", value="Show this help message with all available commands.", inline=False)
    embed.add_field(name="!prize", value="This shows list of available prizes.", inline=False)
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1420560553008697474/1420613932288180265/IMG_9442.jpg")
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
        url="https://cdn.discordapp.com/attachments/1420560553008697474/1420993021972840468/IMG_9468.gif"
    )
    await ctx.send(embed=embed)


# -------------------------------
# RETRY MECHANIC
# -------------------------------

# User IDs allowed to give retries
RETRY_WHITELIST = {1370076515429253264, 296181275344109568}

# Track pending retries for users
pending_retries = set()

@bot.command(name="retry")
async def retry_command(ctx, target: discord.Member):
    """Allows whitelisted users to grant a retry to another user."""
    if ctx.author.id not in RETRY_WHITELIST:
        return await ctx.send("❌ You are not allowed to give retries.")

    # Add target to pending retries
    pending_retries.add(target.id)
    await ctx.send(f"✅ {target.mention} can now use `!open` again immediately (cooldown bypass once).")

# -------------------------------
# RUN BOT
# -------------------------------
async def main():
    try:
        await bot.start(TOKEN)
    finally:
        await notify_offline()

asyncio.run(main())
