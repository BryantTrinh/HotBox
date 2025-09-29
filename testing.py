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
TARGET_CHANNEL_IDS = [1420560553008697474]
COMMAND_PREFIX = "!"
COOLDOWN_SECONDS = 30 * 24 * 60 * 60  # 30 days
DATA_FILE = "loot_data.json"
LOOT_EMOJIS = {
    "Tickets": "🎟️",
    "Bits": "💠",
    "Gold": "💰",
    "Excellent Dust": "✨",
    "Mint Dust": "🍃",
    "Unopened Dye": "🎨"
}
COOLDOWN_BYPASS_USERS = {296181275344109568, 1370076515429253264, 547733449818243084}

LOOT_TABLE = [
    ("Tickets", (1, 5), 5),
    ("Bits", (500, 1000), 30),
    ("Gold", (500, 1000), 15),
    ("Excellent Dust", (5, 15), 23),
    ("Mint Dust", (5, 15), 22),
    ("Unopened Dye", (1, 3), 5)
]

ALLOWED_USER_IDS = {1370076515429253264, 272880100230430720, 296181275344109568, 547733449818243084}

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
user_cooldowns = {}
user_loot_history = {}

def load_data():
    global user_cooldowns, user_loot_history
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
            user_cooldowns = {int(k): datetime.datetime.fromisoformat(v).astimezone(datetime.timezone.utc)
                              for k, v in data.get("cooldowns", {}).items()}
            user_loot_history = {int(k): [(i, v, datetime.datetime.fromisoformat(t).astimezone(datetime.timezone.utc))
                                          for i, v, t in v_list]
                                 for k, v_list in data.get("history", {}).items()}
        except Exception as e:
            print(f"[ERROR] Failed to load loot data: {e}")

def save_data():
    data = {
        "cooldowns": {str(k): v.isoformat() for k, v in user_cooldowns.items()},
        "history": {str(k): [(i, v, t.isoformat()) for i, v, t in v_list] for k, v_list in user_loot_history.items()},
    }
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

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

    # #7 logic: rare items harder to get
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
# GLOBALS
# -------------------------------
original_prizes = {}
active_views = {}

# -------------------------------
# MINI-GAME
# -------------------------------
class DoubleOrNothingView(View):
    def __init__(self, ctx, user_id, item, value, timestamp):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.user_id = user_id
        self.item = item
        self.value = value
        self.original_value = value
        self.timestamp = timestamp
        self.choice_made = False
        self.time_left = 30
        self.interaction_message = None

        if user_id not in original_prizes:
            original_prizes[user_id] = (item, value, timestamp)

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn’t your lootbox!", ephemeral=True)
            return False
        return True

    async def start_timer(self):
        while self.time_left > 0 and not self.choice_made:
            embed = discord.Embed(
                title="🎰 Double or Nothing?",
                description=(f"{self.ctx.author.mention}, you won **{self.value} {self.item}**!\n"
                             f"Pick: 🎲 (Double) | 🍀 (Safe)"),
                color=0x00FF00
            )
            embed.add_field(name="⏳ Time remaining", value=f"**{self.time_left} seconds**")
            embed.add_field(name="Prize", value=f"**{self.value} {self.item}**")
            try:
                await self.interaction_message.edit(embed=embed, view=self)
            except Exception:
                pass
            await asyncio.sleep(1)
            self.time_left -= 1

        if not self.choice_made:
            await self.on_timeout()

    async def handle_choice(self, interaction: Interaction, choice: str):
        if self.choice_made:
            return  # Prevent double handling

        result_text = ""
        color = 0xFFD700

        if choice == "double":
            if random.random() < 0.5:
                self.value *= 2
                result_text = f"🎲 You risked it all... and WON! Your prize is now **{self.value} {self.item}**!"
                color = 0x00FF00
            else:
                self.value = 0
                result_text = "💀 You risked it all... and LOST! No reward this time."
                color = 0xFF0000
        elif choice == "safe":
            result_text = f"🍀 You played it safe! You keep your prize of **{self.value} {self.item}**."

        # Save prize
        if self.user_id not in user_loot_history:
            user_loot_history[self.user_id] = []
        user_loot_history[self.user_id].append((self.item, self.value, self.timestamp))
        asyncio.create_task(asyncio.to_thread(save_data))

        # Disable buttons
        for child in self.children:
            child.disabled = True

        # Send result
        embed = discord.Embed(title="🎰 Double or Nothing Result", description=result_text, color=color)
        embed.add_field(name="Original Prize", value=f"**{self.original_value} {self.item}**", inline=False)
        try:
            await interaction.response.edit_message(embed=embed, view=self)
        except Exception:
            await self.ctx.send(embed=embed)

        self.choice_made = True
        self.stop()
        if self.user_id in active_views and active_views[self.user_id] == self:
            del active_views[self.user_id]

    async def on_timeout(self):
        if self.choice_made:
            return
        self.choice_made = True
        for child in self.children:
            child.disabled = True

        embed = discord.Embed(
            title="🎰 Double or Nothing Timed Out",
            description=f"⏳ Time’s up, {self.ctx.author.mention}!\n"
                        f"You keep your original prize of **{self.value} {self.item}**.",
            color=0xAAAAAA
        )
        embed.add_field(name="Prize", value=f"**{self.value} {self.item}**", inline=False)
        try:
            await self.interaction_message.edit(embed=embed, view=None)
        except Exception:
            await self.ctx.send(embed=embed)

        self.stop()
        if self.user_id in active_views and active_views[self.user_id] == self:
            del active_views[self.user_id]


# -------------------------------
# COMMANDS
# -------------------------------
def find_member_by_name_or_id(guild, query: str):
    query_lower = query.lower()
    if query.startswith("<@") and query.endswith(">"):
        try: return guild.get_member(int(query.strip("<@!>")))
        except: return None
    if query.isdigit(): return guild.get_member(int(query))
    for m in guild.members:
        if query_lower in m.display_name.lower() or query_lower in m.name.lower():
            return m
    return None

# -------------------------------
# Lootbox command
# -------------------------------
@bot.command(name="open")
async def open_lootbox(ctx):
    try:
        if ctx.channel.id not in TARGET_CHANNEL_IDS:
            return

        user_id = ctx.author.id

        # Prevent multiple lootboxes at once
        if user_id in active_views:
            await ctx.send(f"{ctx.author.mention}, you already have a lootbox in progress!")
            return

        # Clear any previous original prize
        if user_id in original_prizes:
            del original_prizes[user_id]

        # Nitro boost / cooldown bypass
        if not ctx.author.premium_since and user_id not in COOLDOWN_BYPASS_USERS:
            await ctx.send("You must be boosting to open a lootbox.")
            return

        # Cooldown check
        now = datetime.datetime.now(datetime.timezone.utc)
        if user_id not in COOLDOWN_BYPASS_USERS and user_id in user_cooldowns:
            last_open = user_cooldowns[user_id]
            elapsed = (now - last_open).total_seconds()
            if elapsed < COOLDOWN_SECONDS:
                await ctx.send("You are on cooldown!")
                return

        # Roll loot
        item, value = roll_loot()
        emoji = LOOT_EMOJIS.get(item, "🎁")
        user_cooldowns[user_id] = now
        original_prizes[user_id] = (item, value, now)

        # STEP 1: Praying embed
        praying_embed = discord.Embed(
            title="🌸 Praying ♡",
            description=f"{random.choice(list(LOOT_EMOJIS.values()))}   "
                        f"{random.choice(list(LOOT_EMOJIS.values()))}   "
                        f"{random.choice(list(LOOT_EMOJIS.values()))}",
            color=0xFFC5D3
        )
        message = await ctx.send(embed=praying_embed)
        await asyncio.sleep(0.6)

        # STEP 2: Spinning animation
        spin_embed = discord.Embed(title="🎰 Spinning...", description="| 🎲   💎   💰 |", color=0xFFC5D3)
        await message.edit(embed=spin_embed)

        for _ in range(3):
            reels = [random.choice(list(LOOT_EMOJIS.values())) for _ in range(3)]
            spin_embed.description = f"| {reels[0]}   {reels[1]}   {reels[2]} |"
            await message.edit(embed=spin_embed)
            await asyncio.sleep(0.25)

        # STEP 3: Attach Double or Nothing view (only edit once)
        view = DoubleOrNothingView(ctx, user_id, item, value, now)
        view.interaction_message = message
        active_views[user_id] = view

        # Send the first result embed with the view attached
        result_embed = discord.Embed(
            title="🎉 Congrats!",
            description=f"{ctx.author.mention}, you won **{value} {item}** {emoji}\nPick: 🎲 (Double) | 🍀 (Safe)",
            color=0xFFC5D3
        )

        # Start the view’s timer, which will handle all future updates
        asyncio.create_task(view.start_timer())

    except Exception:
        import traceback
        traceback.print_exc()



ALLOWED_USER_IDS = {1370076515429253264, 272880100230430720, 296181275344109568, 547733449818243084}  # replace with actual Discord user IDs

@bot.command(name="retry")
async def retry_lootbox(ctx, member: discord.Member):
    try:
        if ctx.author.id not in ALLOWED_USER_IDS:
            await ctx.send("❌ You don’t have permission to use this command.")
            return

        user_id = member.id

        if user_id not in original_prizes:
            await ctx.send(f"❌ {member.display_name} has no original prize to retry.")
            return

        # ✅ Always reference the ORIGINAL prize saved earlier
        item, value, timestamp = original_prizes[user_id]

        # Disable previous view if exists
        if user_id in active_views:
            await ctx.send(f"{ctx.author.mention}, you already have a lootbox in progress!")
            return

        game_embed = discord.Embed(
            title="🎰 Double or Nothing Retry",
            description=(f"{member.mention}, you get another chance!\n\n"
                         f"Your **original prize** was **{value} {item}**.\n"
                         "Do you want to risk it again?\n\n"
                         "Pick one: 🎲 (Double) | 🍀 (Safe)"),
            color=0x00FF00
        )
        game_embed.add_field(name="Original Prize", value=f"**{value} {item}**")

        view = DoubleOrNothingView(
            ctx,
            user_id,
            item,
            value,
            datetime.datetime.now(datetime.timezone.utc)
        )

        message = await ctx.send(embed=game_embed, view=view)
        view.interaction_message = message
        asyncio.create_task(view.start_timer())

        await ctx.send(f"✅ {member.mention} has been given another try at Double or Nothing!")

    except Exception as e:
        await ctx.send(f"❌ Error retrying lootbox: {e}")

@bot.command(name="history")
async def loot_history(ctx, *, query: str = None):
    # Figure out target
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
                title=f"{target.display_name}'s Loot History "
                      f"(Page {self.current_page + 1}/{total_pages})",
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

    # Send first page
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

    # Figure out target
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
    embed.add_field(name="!open", value="Open a lootbox! Can only be used once every 30 days.", inline=False)
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
