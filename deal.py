import discord
from discord.ext import commands, tasks
from discord.ui import View, Button, button
import random
import json
import os
import asyncio
import copy
from datetime import datetime, timedelta, timezone


# ----------------------------
# Footer Helper
# ----------------------------
def add_embed_footer(embed: discord.Embed) -> discord.Embed:
    footer_line = "*⋆ ˚｡⋆୨ 𝓜𝓲𝓭𝓪𝓼 ୧⋆ ˚｡⋆ coded by <@296181275344109568>*"

    if embed.description:
        embed.description += footer_line
    else:
        embed.description = footer_line

    return embed


# -----------------------------
# Whitelists and Channels
# -----------------------------
WHITELIST = [296181275344109568, 1370076515429253264, 320351249549623297]
BOX_DROP_CHANNEL_ID = 1284631100609662989  # test channel(s)

DATA_FILE = "deal_data.json"
BOX_EMOJI = "🎁"

# -----------------------------
# Back-to-back / Skip rules
# -----------------------------
# If a non-whitelisted user wins one of these, they must SKIP the next drop
SKIP_NEXT_DROP_PRIZES = {"rewind_choice", "one_free_box", "golden_door"}

# If they win these, they are allowed to win again immediately (no restriction)
ALWAYS_OK_BACK_TO_BACK = {"bit_frame", "free_dye_job", "bit_roulette"}


# -----------------------------
# Prize Pool
# -----------------------------
DEFAULT_PRIZES = {
    "bit_frame": {
        "name": "🖼️ Bit Frame of Your Choice",
        "rarity": "Common",
        "color": 0xA8A8A8,
        "chance": 30,
        "flavor": "🖼️ *A simple but stylish cosmetic reward.*",
        "description": "_Choose any Bit Frame – claim via ticket._",
        "remaining": 10,
    },
    "free_dye_job": {
        "name": "🎨 Free Regular Dye Job",
        "rarity": "Common",
        "color": 0xA8A8A8,
        "chance": 30,
        "flavor": "🎨 *A splash of color to freshen things up.*",
        "description": "_Free Regular Dye job – claim via ticket._",
        "remaining": 7,
    },
    "bit_roulette": {
        "name": "🎲 Bit Roulette",
        "rarity": "Uncommon",
        "color": 0x44D17C,
        "chance": 20,
        "flavor": "🎲 *Luck swirls around you as the wheel spins…*",
        "description": "_Roll between 5k–10k bits on the bot._",
        "remaining": 5,
    },
    "rewind_choice": {
        "name": "🔄 Rewind My Choice",
        "rarity": "Rare",
        "color": 0x4C8DFF,
        "chance": 10,
        "flavor": "🔄 *A rare token infused with time-bending magic…*",
        "description": "_Undo your last decision during the Main Event._",
        "remaining": 3,
    },
    "one_free_box": {
        "name": "📦 One Free Mystery Box",
        "rarity": "Ultra Rare",
        "color": 0xA251FF,
        "chance": 7,
        "flavor": "📦 *A shimmering box materializes beside you… for free.*",
        "description": "_Open one free mystery box with no follow-up offers or rewinds._",
        "remaining": 2,
    },
    "golden_door": {
        "name": "✨🚪 Golden Door",
        "rarity": "Secret Rare",
        "color": 0xF7C843,
        "chance": 3,
        "flavor": "✨ *The Golden Door radiates a blinding glow…*",
        "description": "_Guaranteed prize worth at least 35 tickets._",
        "remaining": 1,
    },
}


RARITY_STARS = {
    "Common": "⭐",
    "Uncommon": "⭐⭐",
    "Rare": "⭐⭐⭐",
    "Ultra Rare": "⭐⭐⭐⭐",
    "Secret Rare": "⭐⭐⭐⭐⭐",
}

RARITY_ORDER = {
    "Common": 0,
    "Uncommon": 1,
    "Rare": 2,
    "Ultra Rare": 3,
    "Secret Rare": 4,
}


# -----------------------------
# Cog
# -----------------------------
class DealOrNoDeal(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.prizes = {}
        self.winners = []

        self.sent_today: int = 0
        self.max_boxes_today: int | None = None
        self.first_spawn_time: datetime | None = None
        self.cycle_reset_time: datetime | None = None
        self.next_spawn: datetime | None = None

        self.active_message_id = None
        self.active_lock = asyncio.Lock()

        self._load_data()
        print("[Deal] DealOrNoDeal initialized.")
        self.deal_loop.start()

    def _purge_retired_prizes(self):
        """
        Remove retired/forbidden prizes that may still exist in deal_data.json.
        Purges by key and by name match (case-insensitive).
        """
        forbidden_keys = {
            "golden_mystery_bag",
            "golden_bag",
            "mystery_bag_gold",
        }

        forbidden_name_fragments = {
            "golden mystery bag",
            "mystery bag",  # keep this if you want to nuke ANY 'mystery bag' prize
        }

        to_delete = set()

        for key, prize in list(self.prizes.items()):
            name = str(prize.get("name", "")).lower()

            if key in forbidden_keys:
                to_delete.add(key)
                continue

            if any(fragment in name for fragment in forbidden_name_fragments):
                to_delete.add(key)

        if to_delete:
            for k in to_delete:
                self.prizes.pop(k, None)
            print(f"[Deal] Purged retired prizes: {sorted(to_delete)}")
            self._save_data()

    # -------------------------
    # Data persistence
    # -------------------------
    def _load_data(self):
        """Load prize + winner data, plus cycle state, from JSON."""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)

                loaded_prizes = data.get("prizes", {})
                self.prizes = copy.deepcopy(DEFAULT_PRIZES)

                for key, val in loaded_prizes.items():
                    if key in self.prizes:
                        self.prizes[key].update(val)
                    else:
                        self.prizes[key] = val

                self.winners = data.get("winners", [])

                meta = data.get("meta", {})
                self.sent_today = meta.get("sent_today", 0) or 0
                self.max_boxes_today = meta.get("max_boxes_today")

                fst_ts = meta.get("first_spawn_time")
                crt_ts = meta.get("cycle_reset_time")

                if isinstance(fst_ts, (int, float)):
                    self.first_spawn_time = datetime.fromtimestamp(fst_ts, tz=timezone.utc)
                else:
                    self.first_spawn_time = None

                if isinstance(crt_ts, (int, float)):
                    self.cycle_reset_time = datetime.fromtimestamp(crt_ts, tz=timezone.utc)
                else:
                    self.cycle_reset_time = None

                print(
                    f"[Deal] Loaded data. sent_today={self.sent_today}, "
                    f"max_boxes_today={self.max_boxes_today}, "
                    f"first_spawn_time={self.first_spawn_time}, "
                    f"cycle_reset_time={self.cycle_reset_time}"
                )

                # Remove retired prizes that may still exist in JSON
                self._purge_retired_prizes()

            except Exception as e:
                print(f"[Deal] Error loading {DATA_FILE}: {e}")
                self.prizes = copy.deepcopy(DEFAULT_PRIZES)
                self.winners = []
                self.sent_today = 0
                self.max_boxes_today = None
                self.first_spawn_time = None
                self.cycle_reset_time = None
        else:
            self.prizes = copy.deepcopy(DEFAULT_PRIZES)
            self.winners = []
            self.sent_today = 0
            self.max_boxes_today = None
            self.first_spawn_time = None
            self.cycle_reset_time = None
            self._save_data()
            print("[Deal] No data file found, created new with defaults.")

    def _save_data(self):
        """Save prize, winners, and cycle metadata to JSON (with UNIX timestamps)."""
        meta = {
            "sent_today": self.sent_today,
            "max_boxes_today": self.max_boxes_today,
            "first_spawn_time": self.first_spawn_time.timestamp() if self.first_spawn_time else None,
            "cycle_reset_time": self.cycle_reset_time.timestamp() if self.cycle_reset_time else None,
        }

        data = {
            "prizes": self.prizes,
            "winners": self.winners,
            "meta": meta,
        }

        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"[Deal] Error saving {DATA_FILE}: {e}")

    # -------------------------
    # Helpers
    # -------------------------
    def _reset_cycle_if_needed(self):
        """
        Option A:
        - 24-hour cycle starts at FIRST SPAWN (first normal box send).
        - After 24 hours from first_spawn_time, cycle resets.
        """
        now = datetime.now(timezone.utc)

        if self.cycle_reset_time and now >= self.cycle_reset_time:
            print(
                f"[Deal] Cycle reset triggered. "
                f"Old cycle: first_spawn={self.first_spawn_time}, reset_time={self.cycle_reset_time}"
            )
            self.sent_today = 0
            self.max_boxes_today = None
            self.first_spawn_time = None
            self.cycle_reset_time = None
            self.next_spawn = now + timedelta(hours=random.randint(1, 12))
            print(f"[Deal] New cycle started. Next spawn scheduled at {self.next_spawn.isoformat()} UTC.")
            self._save_data()

    def _available_prizes(self):
        return {k: v for k, v in self.prizes.items() if v.get("remaining", 0) > 0}

    def _pick_random_prize(self):
        available = self._available_prizes()
        if not available:
            return None, None

        weighted_table = []
        for key, prize in available.items():
            chance = prize.get("chance", 0)
            if chance > 0:
                weighted_table.append((key, prize, chance))

        if not weighted_table:
            return None, None

        total = sum(x[2] for x in weighted_table)
        r = random.uniform(0, total)
        upto = 0

        for key, prize, chance in weighted_table:
            if upto + chance >= r:
                return key, prize
            upto += chance

        return weighted_table[-1][0], weighted_table[-1][1]

    def _can_user_win_now(self, user_id: int) -> bool:
        """
        Non-whitelisted rule:
        - If the user won a "big prize" last time (rewind_choice / one_free_box / golden_door),
          they MUST skip the very next drop (cannot win the next box).
        - Otherwise, they may win again immediately (including small-prize back-to-back).
        """
        if not self.winners:
            return True

        last = self.winners[-1]
        last_user_id = last["user_id"]
        last_prize_key = last["prize_key"]

        # Only applies if THEY were the last winner
        if last_user_id != user_id:
            return True

        # If their last prize forces a skip, they cannot win the very next drop
        if last_prize_key in SKIP_NEXT_DROP_PRIZES:
            return False

        # Otherwise, they can win again immediately
        return True

    # ----------------------------------------------------------
    # SEND MYSTERY BOX
    # ----------------------------------------------------------
    async def _send_box_message(self, bypass_daily_limit: bool = False):
        self._reset_cycle_if_needed()

        if not self._available_prizes():
            print("[Deal] No prizes available. Box will not spawn.")
            return

        if not bypass_daily_limit and self.max_boxes_today is not None and self.sent_today >= self.max_boxes_today:
            print(
                f"[Deal] Daily limit reached ({self.sent_today}/{self.max_boxes_today}). "
                f"No further boxes until cycle reset."
            )
            return

        channel = self.bot.get_channel(BOX_DROP_CHANNEL_ID)
        if channel is None:
            print(f"[Deal] Drop channel {BOX_DROP_CHANNEL_ID} not found.")
            return

        # ✅ CHANGED: 10 seconds -> 30 seconds
        embed = discord.Embed(
            title="🎁 A Mystery Box Appears!",
            description=(
                "A mysterious **mystery box** has appeared!\n\n"
                f"React with {BOX_EMOJI} within **30 seconds**.\n"
                "_First to react with the emoji opens the box and wins the prize inside._"
            ),
            color=0xF1DBB6,
        )
        embed = add_embed_footer(embed)

        async with self.active_lock:
            msg = await channel.send(embed=embed)
            self.active_message_id = msg.id

        try:
            await msg.add_reaction(BOX_EMOJI)
        except Exception:
            pass

        # -----------------------------
        # FIRST SPAWN -> START 24H CYCLE
        # -----------------------------
        now_utc = datetime.now(timezone.utc)
        if not bypass_daily_limit and self.first_spawn_time is None:
            self.first_spawn_time = now_utc
            self.cycle_reset_time = now_utc + timedelta(hours=24)
            if self.max_boxes_today is None:
                self.max_boxes_today = random.randint(2, 5)
            print(
                f"[Deal] First spawn of new cycle at {self.first_spawn_time.isoformat()} UTC. "
                f"Cycle reset at {self.cycle_reset_time.isoformat()} UTC. "
                f"Daily max boxes: {self.max_boxes_today}"
            )
            self._save_data()

        # ---------------------------------------------------
        # WAIT FOR REACTION
        # ---------------------------------------------------
        def check(reaction, user):
            return (
                reaction.message.id == msg.id
                and str(reaction.emoji) == BOX_EMOJI
                and not user.bot
            )

        winner = None
        loop = asyncio.get_running_loop()

        # ✅ CHANGED: 10 seconds -> 30 seconds
        end_time = loop.time() + 30

        while True:
            timeout = end_time - loop.time()
            if timeout <= 0:
                break

            try:
                reaction, user = await self.bot.wait_for(
                    "reaction_add", timeout=timeout, check=check
                )
            except asyncio.TimeoutError:
                break

            # Whitelist always allowed
            if user.id in WHITELIST:
                winner = user
                break

            # Non-whitelist check (skip-next-drop rule)
            if self._can_user_win_now(user.id):
                winner = user
                break
            else:
                try:
                    await channel.send(
                        f"{user.mention}, you must skip **one** mystery box after winning a **big prize** "
                        f"(Rewind / Free Mystery Box / Golden Door). Try the next drop after this one!"
                    )
                except Exception:
                    pass
                continue

        # ---------------------------------------------------
        # No winner (does NOT count toward daily limit)
        # ---------------------------------------------------
        if not winner:
            embed = discord.Embed(
                title="🎁 Mystery Box Vanished",
                description="No Takers? I guess I'll hold onto this a little longer...",
                color=0x808080,
            )
            embed = add_embed_footer(embed)
            try:
                await msg.edit(embed=embed)
            except Exception:
                pass

            async with self.active_lock:
                if self.active_message_id == msg.id:
                    self.active_message_id = None
            return

        # ---------------------------------------------------
        # Winner found -> count toward daily limit (if not bypass)
        # ---------------------------------------------------
        if not bypass_daily_limit:
            self.sent_today += 1

        # ---------------------------------------------------
        # Prize selection
        # ---------------------------------------------------
        prize_key, prize = self._pick_random_prize()
        if not prize:
            try:
                await msg.edit(
                    embed=discord.Embed(
                        title="🎁 Mystery Box Opened… But Empty!",
                        description=(
                            f"{winner.mention} opened the mystery box, "
                            "but there was nothing inside."
                        ),
                        color=0xFF0000,
                    )
                )
            except Exception:
                pass

            async with self.active_lock:
                if self.active_message_id == msg.id:
                    self.active_message_id = None
            self._save_data()
            return

        prize["remaining"] = max(0, prize.get("remaining", 0) - 1)
        self.prizes[prize_key] = prize

        self.winners.append(
            {
                "user_id": winner.id,
                "prize_key": prize_key,
                "prize_name": prize["name"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message_id": msg.id,
                "channel_id": msg.channel.id,
            }
        )

        self._save_data()

        prize_info = self.prizes[prize_key]
        stars = RARITY_STARS.get(prize_info["rarity"], "")

        win_embed = discord.Embed(
            title="🎉 **Mystery Box – Winner!**",
            description=(
                f"Congratulations {winner.mention}!\n\n"
                f"You opened the mystery box and found:\n"
                f"{stars} **{prize_info['name']}** ({prize_info['rarity']})\n"
                f"{prize_info['flavor']}\n"
                f"{prize_info['description']}\n\n"
                "Create a ticket to claim your prize in <#1412934283613700136>\n"
                f"Ping <@320351249549623297> inside the ticket.\n\n"
                "💬 **Too slow and missed the prize? Better luck next time!**"
            ),
            color=prize_info["color"],
        )
        win_embed = add_embed_footer(win_embed)
        try:
            await msg.edit(embed=win_embed)
        except Exception:
            await channel.send(embed=win_embed)

        async with self.active_lock:
            if self.active_message_id == msg.id:
                self.active_message_id = None

    # -------------------------
    # Background Loop — 24h Cycle from First Spawn
    # -------------------------
    @tasks.loop(seconds=15)
    async def deal_loop(self):
        await self.bot.wait_until_ready()
        now = datetime.now(timezone.utc)
        self._reset_cycle_if_needed()
        if not self._available_prizes():
            return

        if self.max_boxes_today is not None and self.sent_today >= self.max_boxes_today:
            if self.cycle_reset_time:
                self.next_spawn = self.cycle_reset_time
            return

        if self.next_spawn is None:
            self.next_spawn = now + timedelta(minutes=random.randint(1, 2))
            print(f"[Deal] Next spawn scheduled at {self.next_spawn.isoformat()} UTC (initial).")
            return

        if now >= self.next_spawn:
            try:
                await self._send_box_message()
            except Exception as e:
                print(f"[Deal] Error spawning box: {e}")

            if self.max_boxes_today is not None and self.sent_today >= self.max_boxes_today:
                if self.cycle_reset_time:
                    self.next_spawn = self.cycle_reset_time
                    print(
                        f"[Deal] Daily cap reached ({self.sent_today}/{self.max_boxes_today}). "
                        f"No more boxes until cycle reset at {self.cycle_reset_time.isoformat()} UTC."
                    )
                else:
                    self.next_spawn = None
            else:
                self.next_spawn = datetime.now(timezone.utc) + timedelta(hours=random.randint(1, 12))
                print(f"[Deal] Next spawn scheduled at {self.next_spawn.isoformat()} UTC.")

    @deal_loop.before_loop
    async def before_deal_loop(self):
        await self.bot.wait_until_ready()

    # -------------------------
    # Commands
    # -------------------------
    @commands.command(name="dealstatus")
    async def deal_status(self, ctx):
        embed = discord.Embed(
            title="🎁 **Mystery Box – Prize Pool**",
            color=0xF1DBB6,
        )

        sorted_items = sorted(
            self.prizes.items(),
            key=lambda kv: (
                RARITY_ORDER.get(kv[1].get("rarity", "Common"), 99),
                kv[1].get("name", ""),
            ),
        )

        for key, prize in sorted_items:
            stars = RARITY_STARS.get(prize["rarity"], "")

            embed.add_field(
                name=f"**{prize['name']}**",
                value=(
                    f"**Rarity:** {prize['rarity']} ({stars})\n"
                    f"**Remaining:** {prize['remaining']} prizes left\n"
                    f"{prize['flavor']}\n"
                    f"{prize['description']}"
                ),
                inline=False,
            )
        embed = add_embed_footer(embed)
        await ctx.send(embed=embed)

    @commands.command(name="dealforce")
    async def deal_force(self, ctx):
        """Instantly spawn a box, bypassing daily limits (for testing/admin)."""
        if ctx.author.id not in WHITELIST:
            return await ctx.send("❌ You are not allowed.")

        await self._send_box_message(bypass_daily_limit=True)
        self.next_spawn = datetime.now(timezone.utc) + timedelta(minutes=random.randint(1, 2))
        await ctx.send("⚡ Forced mystery box spawned. Next natural spawn scheduled in 1–2 minutes.")

    @commands.command(name="dealreset")
    async def deal_reset(self, ctx):
        """Reset prize quantities back to defaults."""
        if ctx.author.id not in WHITELIST:
            return await ctx.send("❌ You do not have permission.")

        self.prizes = copy.deepcopy(DEFAULT_PRIZES)
        self._save_data()

        embed = discord.Embed(
            title="🔄 Prize Pool Reset",
            description="All mystery box prizes restored to default amounts.",
            color=0xF1DBB6,
        )
        embed = add_embed_footer(embed)
        await ctx.send(embed=embed)

    @commands.command(name="dealhistory")
    async def deal_history(self, ctx):
        if not self.winners:
            return await ctx.send("📭 No winners recorded yet.")

        history = list(reversed(self.winners))
        items_per_page = 5
        total_pages = (len(history) + items_per_page - 1) // items_per_page

        prize_map = copy.deepcopy(DEFAULT_PRIZES)
        for key, val in self.prizes.items():
            if key in prize_map:
                prize_map[key].update(val)
            else:
                prize_map[key] = val

        class DealHistoryView(View):
            def __init__(self):
                super().__init__(timeout=120)
                self.current_page = 0

            async def update_page(self, interaction):
                start = self.current_page * items_per_page
                end = start + items_per_page
                page_items = history[start:end]

                lines = []
                page_color = 0xFFC5D3
                max_rarity_score = -1

                for entry in page_items:
                    prize = prize_map.get(entry["prize_key"], DEFAULT_PRIZES[entry["prize_key"]])
                    stars = RARITY_STARS.get(prize["rarity"], "")

                    rarity = prize.get("rarity", "Common")
                    rarity_score = RARITY_ORDER.get(rarity, -1)
                    if rarity_score > max_rarity_score:
                        max_rarity_score = rarity_score
                        page_color = prize.get("color", 0xFFC5D3)

                    user = ctx.guild.get_member(entry["user_id"])
                    mention = user.mention if user else f"<@{entry['user_id']}>"

                    timestamp = datetime.fromisoformat(entry["timestamp"]).strftime(
                        "%Y-%m-%d %H:%M"
                    )

                    lines.append(
                        f"**{mention}** — {stars} *{prize['name']}* ({prize['rarity']})\n"
                        f"🕒 {timestamp}\n"
                    )

                embed = discord.Embed(
                    title=f"🎉 Mystery Box Winners (Page {self.current_page + 1}/{total_pages})",
                    description="\n".join(lines),
                    color=page_color,
                )
                await interaction.response.edit_message(embed=embed, view=self)

            @button(label="◀️", style=discord.ButtonStyle.secondary)
            async def previous(self, interaction, btn):
                if self.current_page > 0:
                    self.current_page -= 1
                await self.update_page(interaction)

            @button(label="▶️", style=discord.ButtonStyle.secondary)
            async def next(self, interaction, btn):
                if self.current_page < total_pages - 1:
                    self.current_page += 1
                await self.update_page(interaction)

        page_items = history[:items_per_page]
        lines = []
        page_color = 0xFFC5D3
        max_rarity_score = -1

        for entry in page_items:
            prize = prize_map.get(entry["prize_key"], DEFAULT_PRIZES[entry["prize_key"]])
            stars = RARITY_STARS.get(prize["rarity"], "")

            rarity = prize.get("rarity", "Common")
            rarity_score = RARITY_ORDER.get(rarity, -1)
            if rarity_score > max_rarity_score:
                max_rarity_score = rarity_score
                page_color = prize.get("color", 0xFFC5D3)

            user = ctx.guild.get_member(entry["user_id"])
            mention = user.mention if user else f"<@{entry['user_id']}>"

            timestamp = datetime.fromisoformat(entry["timestamp"]).strftime(
                "%Y-%m-%d %H:%M"
            )

            lines.append(
                f"**{mention}** — {stars} *{prize['name']}* ({prize['rarity']})\n"
                f"🕒 {timestamp}\n"
            )

        embed = discord.Embed(
            title=f"🎉 Mystery Box Winners (Page 1/{total_pages})",
            description="\n".join(lines),
            color=page_color,
        )
        await ctx.send(embed=embed, view=DealHistoryView())

    @commands.command(name="dealhelp")
    async def deal_help(self, ctx):
        embed = discord.Embed(
            title="📘 **Mystery Box Event – Help Menu**",
            description=(
                "**Concept of the Game:**\n"
                "A random **mystery box** appears every **1–12 hours** while the "
                "daily cycle is active.\n"
                "Each 24-hour cycle (starting from the **first box spawn**) allows "
                "**2–5 claimed boxes total**.\n\n"
                f"First to react quickly with {BOX_EMOJI} opens it and claims the prize inside!\n\n"
                "__Here are all available commands for the Mystery Box mini-event:__"
            ),
            color=0x7FB3FF,
        )

        embed.add_field(
            name="🎁 **!dealstatus**",
            value="Shows all available prizes, rarities, and how many remain.",
            inline=False,
        )

        embed.add_field(
            name="📜 **!dealhistory**",
            value="Shows all previous mystery box winners with rarity stars.",
            inline=False,
        )

        embed.add_field(
            name="ℹ️ **Game Rules**",
            value=(
                f"• First to react with {BOX_EMOJI} wins the box.\n"
                "• If you win a **big prize** (Rewind / Free Mystery Box / Golden Door),\n"
                "  you must **skip the next drop**.\n"
                "• Each 24-hour cycle has a random limit of **2–5 claimed boxes**.\n"
            ),
            inline=False,
        )

        embed.set_footer(text="Use !dealhelp anytime for this menu.")

        embed.add_field(
            name="\u200b",
            value="*⋆ ˚｡⋆୨ 𝓜𝓲𝓭𝓪𝓼 ୧⋆ ˚｡⋆ coded by <@296181275344109568>*",
            inline=False,
        )

        await ctx.send(embed=embed)

    @commands.command(name="dealwipe")
    async def deal_history_reset(self, ctx):
        """Reset ONLY the winner history (Clean Slate for a new event)."""
        if ctx.author.id not in WHITELIST:
            return await ctx.send("❌ You do not have permission to reset the history.")

        self.winners = []
        self._save_data()

        embed = discord.Embed(
            title="🧹 **Mystery Box – History Reset**",
            description=(
                "All winner history has been cleared.\n"
                "The event now starts with a **clean slate**!"
            ),
            color=0xFFC5D3,
        )
        embed = add_embed_footer(embed)
        await ctx.send(embed=embed)

    @commands.command(name="dealdayreset")
    async def deal_day_reset(self, ctx):
        """
        Admin-only: manually start a new 24-hour cycle right now.
        - Resets sent_today
        - Sets first_spawn_time = now
        - Sets cycle_reset_time = now + 24h
        - Randomizes max_boxes_today (2–5)
        - Schedules next spawn 1–12 hours from now
        """
        if ctx.author.id not in WHITELIST:
            return await ctx.send("❌ You do not have permission to use this.")

        now = datetime.now(timezone.utc)

        self.sent_today = 0
        self.first_spawn_time = now
        self.cycle_reset_time = now + timedelta(hours=24)
        self.max_boxes_today = random.randint(2, 5)
        self.next_spawn = now + timedelta(hours=random.randint(1, 12))

        self._save_data()

        embed = discord.Embed(
            title="🔄 **Daily Cycle Reset Complete**",
            description=(
                f"A new 24-hour cycle has been **manually started**.\n\n"
                f"📦 **Daily Box Limit:** {self.max_boxes_today} claimed boxes\n"
                f"🕒 **Cycle Start (UTC):** {self.first_spawn_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"⏳ **Cycle Reset (UTC):** {self.cycle_reset_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"⏰ **Next Spawn:** <t:{int(self.next_spawn.timestamp())}:T>"
            ),
            color=0xFFD27F
        )
        embed = add_embed_footer(embed)
        await ctx.send(embed=embed)

        print(
            f"[Deal] Manual daily cycle reset by admin. "
            f"first_spawn={self.first_spawn_time.isoformat()} UTC, "
            f"reset_time={self.cycle_reset_time.isoformat()} UTC, "
            f"max_boxes={self.max_boxes_today}, "
            f"next_spawn={self.next_spawn.isoformat()} UTC."
        )

    @commands.command(name="dealdaystatus")
    async def deal_day_status(self, ctx):
        """Shows information about the current 24-hour cycle and next spawn."""
        now = datetime.now(timezone.utc)

        if self.first_spawn_time:
            cycle_start_utc = self.first_spawn_time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            cycle_start_utc = "Not started yet"

        if self.cycle_reset_time:
            cycle_reset_utc = self.cycle_reset_time.strftime("%Y-%m-%d %H:%M:%S")
            cycle_reset_discord = f"<t:{int(self.cycle_reset_time.timestamp())}:R>"
        else:
            cycle_reset_utc = "Not scheduled"
            cycle_reset_discord = "N/A"

        if self.next_spawn:
            next_spawn_utc = self.next_spawn.strftime("%Y-%m-%d %H:%M:%S")
            next_spawn_discord = f"<t:{int(self.next_spawn.timestamp())}:R>"
        else:
            next_spawn_utc = "Not scheduled"
            next_spawn_discord = "N/A"

        if not self._available_prizes():
            status = "🔴 **No prizes remaining**"
        elif self.max_boxes_today is not None and self.sent_today >= self.max_boxes_today:
            status = "🔴 **Daily claim limit reached**"
        elif self.first_spawn_time is None:
            status = "🟡 Waiting for the first spawn of the cycle..."
        else:
            status = "🟢 Cycle active, boxes can still spawn"

        embed = discord.Embed(
            title="📊 **Daily Mystery Box Cycle Status**",
            color=0x7FB3FF
        )

        embed.add_field(
            name="📦 Boxes Claimed This Cycle",
            value=f"**{self.sent_today} / {self.max_boxes_today or '?'}**",
            inline=False
        )

        embed.add_field(
            name="🕒 Cycle Start (UTC)",
            value=cycle_start_utc,
            inline=True
        )

        embed.add_field(
            name="⏳ Cycle Reset",
            value=f"**UTC:** {cycle_reset_utc}\n**In:** {cycle_reset_discord}",
            inline=True
        )

        embed.add_field(
            name="⏰ Next Spawn",
            value=f"**UTC:** {next_spawn_utc}\n**In:** {next_spawn_discord}",
            inline=False
        )

        embed.add_field(
            name="📍 Current Status",
            value=status,
            inline=False
        )
        embed = add_embed_footer(embed)
        await ctx.send(embed=embed)

    @commands.command(name="dealnext")
    async def deal_next(self, ctx):
        """Shows the next scheduled mystery box spawn."""
        if not self.next_spawn:
            return await ctx.send("⏳ No spawn time assigned yet (maybe at daily cap, or cycle not started).")

        ts_discord = f"<t:{int(self.next_spawn.timestamp())}:R>"
        ts_utc = self.next_spawn.strftime("%Y-%m-%d %H:%M:%S")

        embed = discord.Embed(
            title="⏰ **Next Mystery Box Spawn**",
            description=(
                f"🕒 **UTC:** {ts_utc}\n"
                f"⏳ **Time Remaining:** {ts_discord}\n\n"
                f"📦 **This Cycle's Progress:** {self.sent_today} / {self.max_boxes_today or '?'} claimed boxes"
            ),
            color=0xFFD27F,
        )
        embed = add_embed_footer(embed)
        await ctx.send(embed=embed)

    @commands.command(name="dealadmin")
    async def deal_admin(self, ctx):
        """Show all admin-only commands (whitelisted)."""
        if ctx.author.id not in WHITELIST:
            return await ctx.send("❌ You do not have permission to view admin commands.")

        whitelist_mentions = []
        for user_id in WHITELIST:
            member = ctx.guild.get_member(user_id)
            whitelist_mentions.append(member.mention if member else f"<@{user_id}>")

        whitelist_text = ", ".join(whitelist_mentions)

        embed = discord.Embed(
            title="🛠️ **Mystery Box – Admin Commands**",
            description="These commands are restricted to authorized administrators:",
            color=0xFFB347
        )

        embed.add_field(
            name="⚡ **!dealforce**",
            value="Instantly spawns a mystery box (bypasses daily spawn limits).",
            inline=False,
        )

        embed.add_field(
            name="🔄 **!dealreset**",
            value="Resets all prize quantities back to default.",
            inline=False,
        )

        embed.add_field(
            name="🧹 **!dealwipe**",
            value="Clears ALL winner history (clean slate).",
            inline=False,
        )

        embed.add_field(
            name="📅 **!dealdayreset**",
            value="Start a new 24-hour cycle right now and reschedule the next spawn.",
            inline=False,
        )

        embed.add_field(
            name="📊 **!dealdaystatus**",
            value="Shows current cycle info: claimed boxes, reset time, next spawn.",
            inline=False,
        )

        embed.add_field(
            name="⏰ **!dealnext**",
            value="Shows the next scheduled spawn time.",
            inline=False,
        )

        embed.add_field(
            name="👑 **Whitelisted Admins**",
            value=whitelist_text,
            inline=False,
        )

        embed.set_footer(text="Admin tools — use responsibly.")
        await ctx.send(embed=embed)


# -----------------------------
# Extension setup
# -----------------------------
async def setup(bot: commands.Bot):
    print("[Deal] DealOrNoDeal cog loading (Mystery Box mode, 24h cycle from first spawn)...")
    await bot.add_cog(DealOrNoDeal(bot))
