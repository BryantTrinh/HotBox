import discord
from discord.ext import commands
from discord.ui import View, Button, Select
import random
import json
import os
import asyncio
from datetime import datetime

# -----------------------------
# Config
# -----------------------------
DATA_FILE = "battle_data.json"
IMAGE_FOLDER = "HK-images"

CHARACTERS = [
    "Hello Kitty", "My Melody", "Kuromi",
    "Cinnamoroll", "Pompompurin", "Keroppi", "Pochacco"
]

CHARACTER_IMAGES = {
    "Hello Kitty": ["HK1.jpg", "HK2.jpg", "HK3.jpg", "HK4.jpg"],
    "My Melody": ["Mel1.jpg", "Mel2.jpg", "Mel3.jpg", "Mel4.jpg"],
    "Kuromi": ["Kur1.jpg", "Kur2.jpg", "Kur3.jpg", "Kur4.jpg"],
    "Cinnamoroll": ["Cin1.jpg", "Cin2.jpg", "Cin3.jpg", "Cin4.jpg"],
    "Pompompurin": ["Pom1.jpg", "Pom2.jpg", "Pom3.jpg", "Pom4.jpg"],
    "Keroppi": ["Ker1.jpg", "Ker2.jpg", "Ker3.jpg", "Ker4.jpg"],
    "Pochacco": ["Poch1.jpg", "Poch2.jpg", "Poch3.jpg", "Poch4.jpg"]
}

SKILLS = [
    "Magic Beam","Super Jump","Cute Charm","Bubble Attack","Sparkle Dash",
    "Sugar Sprinkle","Paw Swipe","Twinkle Twirl","Fluffy Shield","Rainbow Burst",
    "Glitter Shot","Purrfect Strike","Moonbeam Hug","Cherry Pop","Starry Blink",
    "Fuzzy Frenzy","Honey Drizzle","Petal Dance","Snuggle Smash","Candy Cloud",
    "Berry Blush","Sugar Puff","Glitter Charm"
]

# -----------------------------
# Date Shop & Questions Config
# -----------------------------
SHOP_ITEMS = {
    "Gift Box": {"cost": 20, "desc": "🎁 Permanently adds 1-2 to a random stat."},
    "Outfit Upgrade": {"cost": 40, "desc": "👗 Permanently adds 1-2 to a stat of your choice."},
    "Golden Date Ticket": {"cost": 60, "desc": "💎 Permanently adds 2-3 to every stat."},
}

CHARACTER_QUESTIONS = {
    "Hello Kitty": [
        ("Where should we go shopping?", [
            ("🛍️ Boutique", 3), ("🎡 Mall", 2), ("🧸 Toy Store", 1), ("🍦 Ice Cream Shop", 0)
        ]),
        ("What should we bake together?", [
            ("🍰 Cake", 3), ("🍪 Cookies", 2), ("🥧 Pie", 1), ("🍩 Donuts", 0)
        ]),
        ("Where do we relax?", [
            ("🎶 Karaoke", 3), ("📚 Library", 2), ("🌳 Park", 1), ("🏠 Home", 0)
        ]),
        ("How do you end the day?", [
            ("💐 Flowers", 3), ("🤗 Hug", 2), ("👋 Wave", 1), ("👍 High-Five", 0)
        ]),
    ],
    "Keroppi": [
        ("Where should we go?", [
            ("🏞️ Lake", 3), ("🏖️ Beach", 2), ("🌳 Forest", 1), ("🏠 Stay Home", 0)
        ]),
        ("What snack should we bring?", [
            ("🍉 Watermelon", 3), ("🍙 Rice Balls", 2), ("🥪 Sandwich", 1), ("🥤 Soda", 0)
        ]),
        ("What activity?", [
            ("🎣 Fishing", 3), ("⚽ Soccer", 2), ("🛶 Canoeing", 1), ("📱 Phone Games", 0)
        ]),
        ("How do you say goodbye?", [
            ("🤝 Handshake", 3), ("👋 Wave", 2), ("✌️ Peace Sign", 1), ("😴 Nap", 0)
        ]),
    ]
}

# -----------------------------
#Whitelists and Channels
# -----------------------------

WHITELIST = [296181275344109568, 1044136575103152189, 1370076515429253264]
ALLOWED_CHANNELS = {1422420786635079701, 1420560553008697474}

# -----------------------------
# Utility Functions
# -----------------------------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"players": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def random_stats():
    return {
        "strength": random.randint(10, 15),
        "agility": random.randint(10, 15),
        "dodge": random.randint(5, 10),
        "hp": random.randint(75, 100),
        "skill": random.choice(SKILLS)
    }

def generate_unique_id(existing_ids):
    while True:
        new_id = str(random.randint(1000, 9999))
        if new_id not in existing_ids:
            return new_id
# -----------------------------
# BattleSystem Cog
# -----------------------------
class BattleSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()
        self.active_battles = {}
        self.data_lock = asyncio.Lock()
        all_ids = set()
        for player in self.data.get("players", {}).values():
            for char in player.get("characters", []):
                if "id" not in char:
                    char["id"] = generate_unique_id(all_ids)
                if "stats" not in char:
                    char["stats"] = random_stats()
                all_ids.add(char["id"])
        save_data(self.data)

    # -----------------------------
    # Channel Restriction
    # -----------------------------
    async def cog_check(self, ctx):
        if ctx.channel.id not in ALLOWED_CHANNELS:
            await ctx.send("❌ This command can only be used in the gacha channels.")
            return False
        return True

    # -----------------------------
    # Gacha Command
    # -----------------------------
    @commands.command(name="gacha")
    async def gacha(self, ctx):
        user_id = str(ctx.author.id)

        async with self.data_lock:
            # Ensure player exists
            player = self.data["players"].setdefault(user_id, {"characters": [], "last_claim": None})

            # Pick a character base + specific image
            character_base = random.choice(CHARACTERS)
            character_image = random.choice(CHARACTER_IMAGES[character_base])

            # Generate stats
            final_stats = random_stats()

            # Ensure unique ID across all characters
            all_ids = {
                c.get("id")
                for p in self.data.get("players", {}).values()
                for c in p.get("characters", [])
                if "id" in c
            }
            new_id = generate_unique_id(all_ids)

            # Store character
            new_char = {
                "id": new_id,
                "name": character_base,
                "image": character_image,
                "stats": final_stats
            }
            player["characters"].append(new_char)
            save_data(self.data)

        # Animation embed
        embed = discord.Embed(
            title="<a:gacharoll:1422434663934197760> **Sanrio Gacha Roll**",
            description=f"{ctx.author.mention}, rolling your character...",
            color=discord.Color.from_str("#ffffff")
        )
        placeholder_char = random.choice(CHARACTERS)
        placeholder_img = os.path.join(IMAGE_FOLDER, random.choice(CHARACTER_IMAGES[placeholder_char]))
        file = discord.File(placeholder_img, filename="char.jpg")
        embed.set_image(url="attachment://char.jpg")
        msg = await ctx.send(file=file, embed=embed)

        for _ in range(3):
            anim_char = random.choice(CHARACTERS)
            anim_img = os.path.join(IMAGE_FOLDER, random.choice(CHARACTER_IMAGES[anim_char]))
            file = discord.File(anim_img, filename="char.jpg")
            embed.set_image(url="attachment://char.jpg")
            await msg.edit(embed=embed, attachments=[file])
            await asyncio.sleep(0.3)

        # Final result embed
        embed = discord.Embed(
            title="<a:gacharoll:1422434663934197760> Sanrio Gacha Result",
            description=f"{ctx.author.mention}, you got **{new_char['name']}** (#{new_char['id']})!",
            color=discord.Color.from_str("#ffffff")
        )
        for k, v in final_stats.items():
            embed.add_field(name=k.title(), value=v, inline=True)
        final_img_path = os.path.join(IMAGE_FOLDER, new_char["image"])
        file = discord.File(final_img_path, filename="char.jpg")
        embed.set_image(url="attachment://char.jpg")
        await msg.edit(embed=embed, attachments=[file])

# -----------------------------
# Give Character (Paginated Dropdown)
# -----------------------------
    @commands.command(name="give")
    async def give(self, ctx, target: discord.Member):
        giver_id = str(ctx.author.id)
        receiver_id = str(target.id)

        async with self.data_lock:
            giver = self.data["players"].get(giver_id)
            if not giver or not giver.get("characters"):
                return await ctx.send("❌ You have no characters to give.")
            receiver = self.data["players"].setdefault(receiver_id, {"characters": [], "last_claim": None})

        characters = giver["characters"]
        PAGE_SIZE = 5  # Discord select menu limit

        # -----------------------------
        # Main Give View
        # -----------------------------
        class GiveView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=120)
                self.selected_index = None
                self.page = 0
                self.embed_message = None
                self.choice = None  # "give" or "cancel"
                self.update_dropdown()

            def update_dropdown(self):
                self.clear_items()
                start = self.page * PAGE_SIZE
                end = min(start + PAGE_SIZE, len(characters))
                options = [
                    discord.SelectOption(
                        label=f"{c['name']} (#{c['id']})",
                        description=f"HP: {c['stats']['hp']} STR: {c['stats']['strength']}",
                        value=str(start + i)
                    )
                    for i, c in enumerate(characters[start:end])
                ]
                self.dropdown = CharSelect(options, self)
                self.add_item(self.dropdown)
                # Add navigation buttons if multiple pages
                if len(characters) > PAGE_SIZE:
                    self.add_item(PrevPageButton(self))
                    self.add_item(NextPageButton(self))
                # Add confirm/cancel
                self.add_item(ConfirmButton(self))
                self.add_item(CancelButton(self))

        # -----------------------------
        # Dropdown
        # -----------------------------
        class CharSelect(discord.ui.Select):
            def __init__(self, options, view_ref):
                super().__init__(placeholder="Select a character to give...", options=options, min_values=1, max_values=1)
                self.view_ref = view_ref

            async def callback(self, interaction: discord.Interaction):
                if interaction.user.id != ctx.author.id:
                    return await interaction.response.send_message("❌ This dropdown isn't for you.", ephemeral=True)

                self.view_ref.selected_index = int(self.values[0])
                char = characters[self.view_ref.selected_index]

                # Update preview
                embed = discord.Embed(
                    title=f"🎁 Giving {char['name']} (#{char['id']})",
                    description=f"Select ✅ to give this character to {target.mention}, or ❌ to cancel.",
                    color=discord.Color.blurple()
                )
                img_path = os.path.join(IMAGE_FOLDER, char.get("image", "Hello-Kitty.jpg"))
                file = discord.File(img_path, filename="char.jpg")
                embed.set_image(url="attachment://char.jpg")
                await interaction.response.edit_message(embed=embed, attachments=[file], view=self.view_ref)

        # -----------------------------
        # Pagination Buttons
        # -----------------------------
        class PrevPageButton(discord.ui.Button):
            def __init__(self, view_ref):
                super().__init__(label="◀️ Prev Page", style=discord.ButtonStyle.grey)
                self.view_ref = view_ref

            async def callback(self, interaction: discord.Interaction):
                if interaction.user.id != ctx.author.id:
                    return await interaction.response.send_message("❌ This button isn't for you.", ephemeral=True)
                self.view_ref.page = (self.view_ref.page - 1) % ((len(characters) - 1)//PAGE_SIZE + 1)
                self.view_ref.update_dropdown()
                await interaction.response.edit_message(view=self.view_ref)

        class NextPageButton(discord.ui.Button):
            def __init__(self, view_ref):
                super().__init__(label="Next Page ▶️", style=discord.ButtonStyle.grey)
                self.view_ref = view_ref

            async def callback(self, interaction: discord.Interaction):
                if interaction.user.id != ctx.author.id:
                    return await interaction.response.send_message("❌ This button isn't for you.", ephemeral=True)
                self.view_ref.page = (self.view_ref.page + 1) % ((len(characters) - 1)//PAGE_SIZE + 1)
                self.view_ref.update_dropdown()
                await interaction.response.edit_message(view=self.view_ref)

        # -----------------------------
        # Confirm / Cancel Buttons
        # -----------------------------
        class ConfirmButton(discord.ui.Button):
            def __init__(self, view_ref):
                super().__init__(label="✅ Confirm", style=discord.ButtonStyle.green)
                self.view_ref = view_ref

            async def callback(self, interaction: discord.Interaction):
                if interaction.user.id != ctx.author.id:
                    return await interaction.response.send_message("❌ This button isn't for you.", ephemeral=True)
                if self.view_ref.selected_index is None:
                    return await interaction.response.send_message("❌ Select a character first.", ephemeral=True)

                # Disable everything (including dropdown)
                for item in self.view_ref.children:
                    item.disabled = True
                await interaction.response.edit_message(view=self.view_ref)

                self.view_ref.choice = "give"
                self.view_ref.stop()

        class CancelButton(discord.ui.Button):
            def __init__(self, view_ref):
                super().__init__(label="❌ Cancel", style=discord.ButtonStyle.red)
                self.view_ref = view_ref

            async def callback(self, interaction: discord.Interaction):
                if interaction.user.id != ctx.author.id:
                    return await interaction.response.send_message("❌ This button isn't for you.", ephemeral=True)

                # Disable everything
                for item in self.view_ref.children:
                    item.disabled = True
                await interaction.response.edit_message(view=self.view_ref)

                self.view_ref.choice = "cancel"
                self.view_ref.stop()


        # -----------------------------
        # Send initial message
        # -----------------------------
        view = GiveView()
        first_char = characters[0]
        embed = discord.Embed(
            title="Select a character to give",
            description=f"Choose a character to give to {target.mention}:",
            color=discord.Color.blurple()
        )
        img_path = os.path.join(IMAGE_FOLDER, first_char.get("image", "Hello-Kitty.jpg"))
        file = discord.File(img_path, filename="char.jpg")
        embed.set_image(url="attachment://char.jpg")
        view.embed_message = await ctx.send(embed=embed, file=file, view=view)

        # -----------------------------
        # Wait for selection
        # -----------------------------
        await view.wait()
        if view.choice != "give":
            return await ctx.send("❌ Give action cancelled.")

        # -----------------------------
        # Perform transfer
        # -----------------------------
        async with self.data_lock:
            char_to_give = giver["characters"].pop(view.selected_index)
            receiver["characters"].append(char_to_give)
            save_data(self.data)

        # -----------------------------
        # Confirmation embed
        # -----------------------------
        embed = discord.Embed(
            title="✅ Character Given!",
            description=f"{ctx.author.mention} gave **{char_to_give['name']} (#{char_to_give['id']})** to {target.mention}.",
            color=discord.Color.green()
        )
        img_path = os.path.join(IMAGE_FOLDER, char_to_give.get("image", "Hello-Kitty.jpg"))
        file = discord.File(img_path, filename="char.jpg")
        embed.set_image(url="attachment://char.jpg")
        await ctx.send(embed=embed)





# -----------------------------
# Battle Command
# -----------------------------
    @commands.command(name="battle")
    async def battle(self, ctx, opponent: discord.Member):
        challenger_id = str(ctx.author.id)
        opponent_id = str(opponent.id)

        # Prevent multiple battles
        if challenger_id in self.active_battles:
            return await ctx.send("❌ You are already in a battle!")
        if opponent_id in self.active_battles:
            return await ctx.send(f"❌ {opponent.display_name} is already in a battle!")

        if challenger_id not in self.data["players"] or not self.data["players"][challenger_id]["characters"]:
            return await ctx.send("❌ You don’t have any characters to battle with!")
        if opponent_id not in self.data["players"] or not self.data["players"][opponent_id]["characters"]:
            return await ctx.send("❌ Your opponent doesn’t have any characters!")

        # Mark active
        self.active_battles[challenger_id] = True
        self.active_battles[opponent_id] = True

        try:
            # Step 1: Challenge confirmation
            confirm_embed = discord.Embed(
                title="<a:HelloKittyFight:1422422183598100611> Battle Challenge!",
                description=f"{opponent.mention}, do you accept the battle challenge from {ctx.author.mention}?\nYou have 10 seconds to respond.",
                color=discord.Color.from_str("#f98eaa")
            )

            class BattleConfirmView(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=10)
                    self.choice = None
                    self.decliner = None

                @discord.ui.button(label="✅ Accept", style=discord.ButtonStyle.green)
                async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if interaction.user.id != opponent.id:
                        return await interaction.response.send_message("❌ Only the opponent can accept.", ephemeral=True)
                    self.choice = "accept"
                    for b in self.children:
                        b.disabled = True
                    await interaction.response.edit_message(embed=confirm_embed, view=self)
                    self.stop()

                @discord.ui.button(label="❌ Decline", style=discord.ButtonStyle.red)
                async def decline_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if interaction.user.id not in [ctx.author.id, opponent.id]:
                        return await interaction.response.send_message("❌ You can't press this button.", ephemeral=True)
                    self.choice = "decline"
                    self.decliner = interaction.user
                    for b in self.children:
                        b.disabled = True
                    confirm_embed.description = f"❌ {interaction.user.mention} declined the battle."
                    await interaction.response.edit_message(embed=confirm_embed, view=self)
                    self.stop()

            view = BattleConfirmView()
            await ctx.send(embed=confirm_embed, view=view)
            await view.wait()

            if view.choice != "accept":
                # Determine who declined or if timeout
                if view.choice is None:
                    return await ctx.send(f"❌ Battle cancelled. {opponent.mention} did not respond in time.")
                else:
                    return await ctx.send(f"❌ Battle cancelled. {view.decliner.mention} declined.")

            # -----------------------------
            # Step 2: Character selection
            # -----------------------------
            async def select_character(user_id, user_obj):
                characters = self.data["players"][user_id]["characters"]

                class CharSelect(discord.ui.Select):
                    def __init__(self, view):
                        options = [
                            discord.SelectOption(
                                label=f"{c['name']} (#{c['id']})",
                                description=f"HP: {c['stats']['hp']} STR: {c['stats']['strength']}",
                                value=str(i)
                            ) for i, c in enumerate(characters)
                        ]
                        super().__init__(placeholder=f"Select your character, {user_obj.display_name}", options=options, min_values=1, max_values=1)
                        self.view_ref = view  # Reference the view

                    async def callback(self, interaction: discord.Interaction):
                        if interaction.user.id != user_obj.id:
                            return await interaction.response.send_message("❌ This select menu isn't for you.", ephemeral=True)
                        self.view_ref.selected_index = int(self.values[0])  # Save selection to the view
                        for item in self.view_ref.children:
                            item.disabled = True
                        await interaction.response.edit_message(view=self.view_ref)
                        self.view_ref.stop()

                class CharSelectView(discord.ui.View):
                    def __init__(self):
                        super().__init__(timeout=30)
                        self.selected_index = None
                        self.add_item(CharSelect(self))

                view = CharSelectView()
                embed = discord.Embed(
                    title=f"{user_obj.display_name}, choose your character!",
                    color=discord.Color.blurple()
                )
                msg = await ctx.send(embed=embed, view=view)
                await view.wait()
                if view.selected_index is None:
                    raise asyncio.TimeoutError(f"{user_obj.display_name} did not select a character in time.")
                return characters[view.selected_index]


            challenger_char = await select_character(challenger_id, ctx.author)
            opponent_char = await select_character(opponent_id, opponent)

            # -----------------------------
            # Step 3: Battle logic
            # -----------------------------
            c_img_path = os.path.join(IMAGE_FOLDER, challenger_char.get("image", "Hk1.jpg"))
            o_img_path = os.path.join(IMAGE_FOLDER, opponent_char.get("image", "Hk2.jpg"))
            files = [
                discord.File(c_img_path, filename="challenger.jpg"),
                discord.File(o_img_path, filename="opponent.jpg")
            ]

            def hp_bar(current, maximum, length=10):
                filled = max(int(current / maximum * length), 0)
                empty = length - filled
                return f"{'█'*filled}{'░'*empty} ({max(current,0)}/{maximum})"

            battle_embed = discord.Embed(
                title="<a:HelloKittyFight:1422422183598100611> Battle Start!",
                description="Battle begins...",
                color=discord.Color.from_str("#f98eaa")
            )
            c_max_hp = challenger_char["stats"]["hp"]
            o_max_hp = opponent_char["stats"]["hp"]
            c_hp = c_max_hp
            o_hp = o_max_hp

            battle_embed.add_field(
                name=f"{ctx.author.display_name}'s {challenger_char['name']} (#{challenger_char['id']})",
                value=hp_bar(c_hp, c_max_hp),
                inline=True
            )
            battle_embed.add_field(
                name=f"{opponent.display_name}'s {opponent_char['name']} (#{opponent_char['id']})",
                value=hp_bar(o_hp, o_max_hp),
                inline=True
            )
            battle_embed.set_thumbnail(url="attachment://challenger.jpg")
            battle_embed.set_image(url="attachment://opponent.jpg")
            battle_message = await ctx.send(files=files, embed=battle_embed)

            # Battle loop
            turn = 0
            log = []

            while c_hp > 0 and o_hp > 0:
                attacker, defender = (challenger_char, opponent_char) if turn % 2 == 0 else (opponent_char, challenger_char)
                attacker_user = ctx.author if turn % 2 == 0 else opponent
                defender_user = opponent if turn % 2 == 0 else ctx.author

                dmg = attacker["stats"]["strength"] + random.randint(0,5)
                dodge_chance = defender["stats"]["dodge"]

                if random.randint(1,100) <= dodge_chance*2:
                    attack_text = f"💨 {defender_user.display_name}'s {defender['name']} (#{defender['id']}) dodged {attacker_user.display_name}'s {attacker['name']} (#{attacker['id']})!"
                else:
                    if turn % 2 == 0:
                        o_hp -= dmg
                    else:
                        c_hp -= dmg
                    attack_text = f"💥 {attacker_user.display_name}'s {attacker['name']} (#{attacker['id']}) hits {defender_user.display_name}'s {defender['name']} (#{defender['id']}) for {dmg} damage!"

                log.append(attack_text)

                battle_embed.set_field_at(
                    0, name=f"{ctx.author.display_name}'s {challenger_char['name']} (#{challenger_char['id']})", value=hp_bar(c_hp, c_max_hp), inline=True
                )
                battle_embed.set_field_at(
                    1, name=f"{opponent.display_name}'s {opponent_char['name']} (#{opponent_char['id']})", value=hp_bar(o_hp, o_max_hp), inline=True
                )
                battle_embed.description = "\n".join(log[-3:])  # cap last 5 lines
                await battle_message.edit(embed=battle_embed)
                turn += 1
                await asyncio.sleep(1)

            # Winner logic
            winner_id, loser_id = (challenger_id, opponent_id) if c_hp > 0 else (opponent_id, challenger_id)
            winner_char, loser_char = (challenger_char, opponent_char) if c_hp > 0 else (opponent_char, challenger_char)

            async with self.data_lock:
                self.data["players"][loser_id]["characters"].remove(loser_char)
                self.data["players"][winner_id]["characters"].append(loser_char)
                save_data(self.data)

            log.append(f"🏆 {ctx.guild.get_member(int(winner_id)).display_name}'s {winner_char['name']} (#{winner_char['id']}) wins the battle!")
            log.append(f"🎁 {ctx.guild.get_member(int(winner_id)).display_name} takes {loser_char['name']} (#{loser_char['id']}) from {ctx.guild.get_member(int(loser_id)).display_name}!")

            battle_embed.description = "\n".join(log[-3:])
            await battle_message.edit(embed=battle_embed)

            winner_user = ctx.guild.get_member(int(winner_id))
            loser_user = ctx.guild.get_member(int(loser_id))
            congrats_embed = discord.Embed(
                description=f"<a:gacharoll:1422434663934197760> **Congrats** {winner_user.mention}, you won **{loser_user.display_name}'s {loser_char['name']} (#{loser_char['id']})**!\nIt will now show in your `!mychars`",
                color=discord.Color.from_str("#f0c3e2")
            )
            congrats_embed.set_thumbnail(
                url="https://cdn.discordapp.com/attachments/1321372597572599869/1422639529197568020/IMG_9630.gif"
            )
            await ctx.send(embed=congrats_embed)

        finally:
            self.active_battles.pop(challenger_id, None)
            self.active_battles.pop(opponent_id, None)



    # -----------------------------
    # My Characters
    # -----------------------------
    @commands.command(name="mychars")
    async def mychars(self, ctx, target: str = None):
        # -----------------------------
        # Resolve target user and ID
        # -----------------------------
        user_id = str(ctx.author.id)
        user_obj = ctx.author

        if target:
            if ctx.message.mentions:
                user_obj = ctx.message.mentions[0]
                user_id = str(user_obj.id)
            elif target.isdigit():
                user_obj = ctx.guild.get_member(int(target))
                if not user_obj:
                    # User not in guild, use placeholder object
                    user_obj = discord.Object(id=int(target))
                user_id = str(target)
            else:
                return await ctx.send("❌ Invalid user. Use @mention or user ID.")

        # -----------------------------
        # Load player data safely
        # -----------------------------
        async with self.data_lock:
            player = self.data.get("players", {}).get(user_id)

        if not player or not player.get("characters"):
            return await ctx.send(f"❌ {getattr(user_obj,'display_name',user_id)} has no characters yet.")

        characters = player["characters"]

        # -----------------------------
        # Preload file paths with fallback
        # -----------------------------
        preloaded_files = []
        fallback_img = os.path.join(IMAGE_FOLDER, "Hello-Kitty.jpg")
        for char in characters:
            img_file = char.get("image")  # Use stored image
            img_path = os.path.join(IMAGE_FOLDER, img_file) if img_file else fallback_img
            if not os.path.exists(img_path):
                img_path = fallback_img
            preloaded_files.append(img_path)

        # -----------------------------
        # Embed creator
        # -----------------------------
        def create_embed(page_index):
            char = characters[page_index]
            embed = discord.Embed(
                title=f"🎀 {getattr(user_obj,'display_name',user_id)}'s Characters (Page {page_index+1}/{len(characters)})",
                color=discord.Color.blurple()
            )
            stats_text = "\n".join(f"**{k.title()}**: {v}" for k, v in char["stats"].items())
            embed.add_field(name=f"{char['name']} (#{char['id']})", value=stats_text, inline=False)
            embed.set_image(url="attachment://char.jpg")
            return embed

        # -----------------------------
        # Pagination view and the rest below that
        # -----------------------------
        class Pagination(View):
            def __init__(self):
                super().__init__(timeout=120)
                self.page = 0
                self.message = None

            async def send_initial(self):
                embed = create_embed(0)
                file_path = preloaded_files[0]
                file = discord.File(file_path, filename="char.jpg")
                self.message = await ctx.send(embed=embed, file=file, view=self)

            async def update(self):
                embed = create_embed(self.page)
                file_path = preloaded_files[self.page]
                file = discord.File(file_path, filename="char.jpg")
                await self.message.edit(embed=embed, attachments=[file])

            @discord.ui.button(label="Previous", style=discord.ButtonStyle.grey)
            async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != ctx.author.id:
                    return await interaction.response.send_message("❌ This is not yours to press!.", ephemeral=True)
                self.page = (self.page - 1) % len(characters)
                await self.update()
                await interaction.response.defer()

            @discord.ui.button(label="Next", style=discord.ButtonStyle.grey)
            async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != ctx.author.id:
                    return await interaction.response.send_message("❌ This is not yours to press!.", ephemeral=True)
                self.page = (self.page + 1) % len(characters)
                await self.update()
                await interaction.response.defer()

        # -----------------------------
        # Send initial message with view
        # -----------------------------
        view = Pagination()
        await view.send_initial()



    # -----------------------------
    # Leaderboard
    # -----------------------------
    @commands.command(name="leaderboard")
    async def leaderboard(self, ctx):
        async with self.data_lock:
            leaderboard = [(uid, len(pdata["characters"])) for uid, pdata in self.data["players"].items()]
        leaderboard.sort(key=lambda x: x[1], reverse=True)

        embed = discord.Embed(
            title="<:bs_hellokittysmile:1422432030188371998> **Character Leaderboard**",
            color=discord.Color.from_str("#f7a6b3")
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1321372597572599869/1422432724462862366/IMG_9554.gif?ex=68dca735&is=68db55b5&hm=63d3f19289b5eac5fbe9d097189241d77b53e005ae473e3d5b9436cb61c11e39&")

        for i, (uid, count) in enumerate(leaderboard[:10], start=1):
            member = ctx.guild.get_member(int(uid))
            name = member.display_name if member else f"User {uid}"
            embed.add_field(name=f"{i}. {name}", value=f"{count} characters", inline=False)

        await ctx.send(embed=embed)

    # -----------------------------
    # Event/Help
    # -----------------------------
    @commands.command(name="event")
    async def event(self, ctx):
        embed = discord.Embed(
            title="<:NG_3hello:1422427973247832146>  ***Sanrio Battle Fields***",
            description="*Welcome to Sanrio Battle Fields!*",
            color=discord.Color.from_str("#f1c6d2 ")
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1420560553008697474/1422430311454736434/IMG_9552.gif?ex=68dca4f5&is=68db5375&hm=1dde734d2fe4ad0d80bc170b53bc588fe7a06abfe437c207984865301fa55520&")
        embed.add_field(
            name="<a:SanrioComputer:1422418455885250570> **Game Objective:**",
            value="Drop characters, battle them with friends, and collect as many as you can. "
                  "When you win a battle, you take your opponent's character. "
                  "The ultimate winner is the user with the most characters!",
            inline=False
        )
        embed.add_field(name="**!gacha**", value="<a:4k_HK:1422427249872867488> Roll a random Sanrio character", inline=False)
        embed.add_field(name="**!battle @user**", value="<a:HelloKittyFight:1422422183598100611> Challenge another user to a battle. They must confirm the battle before it begins.", inline=False)
        embed.add_field(name="**!mychars**", value="<:hnote1:1420592325817663570> View your characters", inline=False)
        embed.add_field(name="**!leaderboard**", value="<:hellokittylove:1284655017873379434> View the top users by character count.", inline=False)
        embed.add_field(name="**!event**", value="<a:SanrioTextBubble:1422418161839378453> Shows this command list and game description.", inline=False)
        await ctx.send(embed=embed)

    # -----------------------------
    # Clear Command (Whitelist only)
    # -----------------------------
    @commands.command(name="clear")
    async def clear(self, ctx, target: str):
        if ctx.author.id not in WHITELIST:
            return await ctx.send("❌ You are not allowed to use this command.")

        user = None
        if ctx.message.mentions:
            user = ctx.message.mentions[0]
            user_id = str(user.id)
        elif target.isdigit():
            user_id = str(target)
            user = ctx.guild.get_member(int(user_id))
        else:
            return await ctx.send("❌ Invalid user. Use @mention or user ID.")

        async with self.data_lock:
            player = self.data.get("players", {}).get(user_id)
            if not player or not player["characters"]:
                return await ctx.send(f"❌ {user.display_name if user else 'User'} has no characters to clear.")

            player["characters"].clear()
            save_data(self.data)

        await ctx.send(f"✅ Cleared all characters for {user.display_name if user else 'User'}!")
    
    # -----------------------------
    # Clear All Users' Characters (Whitelist only)
    # -----------------------------
    @commands.command(name="clearall")
    async def clearall(self, ctx):
        if ctx.author.id not in WHITELIST:
            return await ctx.send("❌ You are not allowed to use this command.")

        async with self.data_lock:
            for player in self.data.get("players", {}).values():
                player["characters"].clear()
            save_data(self.data)

        await ctx.send("✅ Cleared **all characters** for every user in the database!")


    # -----------------------------
    # Redo Gacha (Whitelist only)
    # -----------------------------
    @commands.command(name="redo")
    async def redo(self, ctx, target: str):
        if ctx.author.id not in WHITELIST:
            return await ctx.send("❌ You are not allowed to use this command.")

        user = None
        if ctx.message.mentions:
            user = ctx.message.mentions[0]
            user_id = str(user.id)
        elif target.isdigit():
            user_id = str(target)
            user = ctx.guild.get_member(int(user_id))
        else:
            return await ctx.send("❌ Invalid user. Use @mention or user ID.")

        async with self.data_lock:
            player = self.data["players"].setdefault(user_id, {"characters": [], "last_claim": None})
            player["last_claim"] = None
            save_data(self.data)

        await ctx.send(f"✅ {user.display_name if user else 'User'} can now use `!gacha` again!")

    # -----------------------------
    # DATE COMMAND
    # -----------------------------

    @commands.command(name="date")
    async def date(self, ctx):
        user_id = str(ctx.author.id)
        async with self.data_lock:
            player = self.data["players"].get(user_id)
            if not player or not player.get("characters"):
                return await ctx.send("❌ You don’t have any characters to date.")
            player.setdefault("date_points", 0)

        # -----------------------------
        # Character select dropdown
        # -----------------------------
        class CharSelect(discord.ui.Select):
            def __init__(self, characters):
                options = [
                    discord.SelectOption(label=f"{c['name']} (#{c['id']})", value=str(i))
                    for i, c in enumerate(characters)
                ]
                super().__init__(placeholder="Pick a character to date...", options=options)
                self.characters = characters
                self.selected_index = None

            async def callback(self, interaction: discord.Interaction):
                if interaction.user.id != ctx.author.id:
                    return await interaction.response.send_message("❌ Not your menu.", ephemeral=True)
                
                await interaction.response.defer()  # <--- Fix first-click failure
                self.selected_index = int(self.values[0])
                self.view.stop()

        class CharSelectView(discord.ui.View):
            def __init__(self, characters):
                super().__init__(timeout=30)
                self.select = CharSelect(characters)
                self.add_item(self.select)

        view = CharSelectView(player["characters"])
        msg = await ctx.send("💕 Pick a character to go on a date with!", view=view)
        await view.wait()

        if view.select.selected_index is None:
            return await ctx.send("❌ You didn’t select a character.")

        char = player["characters"][view.select.selected_index]
        total_score = 0

        # -----------------------------
        # Questions
        # -----------------------------
        questions = CHARACTER_QUESTIONS.get(char["name"], [
            ("Where should we go today?", [
                ("🎢 Amusement Park", 3),
                ("🍽 Restaurant", 2),
                ("🌳 Picnic", 1),
                ("🏠 Stay Home", 0)
            ]),
            ("What should we eat?", [
                ("🍎 Fruit", 3),
                ("🍕 Pizza", 2),
                ("🍞 Bread", 1),
                ("🥗 Salad", 0)
            ]),
            ("What should we do after dinner?", [
                ("🎤 Karaoke", 3),
                ("🎬 Movie", 2),
                ("🎮 Play Games", 1),
                ("📖 Read", 0)
            ]),
            ("How do you say goodbye?", [
                ("💐 Flowers", 3),
                ("🤝 Handshake", 2),
                ("👋 Wave", 1),
                ("👍 Fist Bump", 0)
            ]),
        ])

        # -----------------------------
        # Question loop with progress & hearts (fixed)
        # -----------------------------
        class QuestionSelect(discord.ui.Select):
            def __init__(self, answers):
                options = [discord.SelectOption(label=a[0], value=str(idx)) for idx, a in enumerate(answers)]
                super().__init__(placeholder="Choose an answer...", options=options, min_values=1, max_values=1)
                self.answers = answers
                self.selected_index = None

            async def callback(self, interaction: discord.Interaction):
                if interaction.user.id != ctx.author.id:
                    return await interaction.response.send_message("❌ Not your menu.", ephemeral=True)
                
                await interaction.response.defer()  # avoids first-click fail
                idx = int(self.values[0])
                self.selected_index = idx
                self.view.score_ref[0] += self.answers[idx][1]
                self.view.stop()

        class QuestionView(discord.ui.View):
            def __init__(self, select_item, score_ref):
                super().__init__(timeout=30)
                self.add_item(select_item)
                self.score_ref = score_ref

        score_ref = [total_score]

        for i, (q_text, answers) in enumerate(questions, start=1):
            q_select = QuestionSelect(answers)
            q_view = QuestionView(q_select, score_ref)

            # Initial message content with progress and hearts
            hearts = "💖" * (score_ref[0] // 3)
            await msg.edit(content=f"❓ Q{i}/{len(questions)}: {q_text}\n💖 Score: {hearts}", view=q_view)
            
            await q_view.wait()

            # Update hearts after each selection
            hearts = "💖" * (score_ref[0] // 3)
            await msg.edit(content=f"❓ Q{i}/{len(questions)}: {q_text}\n💖 Score: {hearts}")

        total_score = score_ref[0]


        # -----------------------------
        # Save points
        # -----------------------------
        async with self.data_lock:
            player["date_points"] += total_score
            save_data(self.data)
            new_total = player["date_points"]

        if total_score >= 10:
            result = f"💖 {char['name']} had an amazing time with you! Will I see you again?"
        elif total_score >= 6:
            result = f"😊 {char['name']} enjoyed the date!"
        else:
            result = f"😅 {char['name']} felt the date was a little awkward... Maybe we should take some time apart..."

        embed = discord.Embed(
            title=f"💕 Date with {char['name']}",
            description=f"{result}\n\n✨ You earned **{total_score} Date Points**!\n💎 Total: **{new_total}** Date Points.",
            color=discord.Color.pink()
        )
        await msg.edit(content=None, embed=embed, view=None)





# -----------------------------
# Cog setup
# -----------------------------

async def setup(bot):
    print("[Sanrio] BattleSystem cog loading...")
    await bot.add_cog(BattleSystem(bot))
