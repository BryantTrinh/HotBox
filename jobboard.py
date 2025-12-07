import discord
from discord.ext import commands
import os, json, datetime, asyncio, traceback

# ----------------------------
# CONFIG
# ----------------------------

MILESTONE_EMOJIS = {
    "1️⃣": ("1200 Effort", "Please provide proof you reached 1200 effort."),
    "2️⃣": ("1500 Effort", "Please provide proof you reached 1500 effort."),
    "3️⃣": ("2000 Effort", "Please provide proof you reached 2000 effort.")
}

REWARD_OPTIONS = {
    "1200 Effort": {"tickets": 5},
    "1500 Effort": {"tickets": 7},
    "2000 Effort": {"tickets": 10},
}

CLAN_REQUEST_CHANNEL_IDS = {
    1445623958975156418,
    1285473965657030667
}

CLANREQUEST_ALLOWED_CHANNELS = {
    1285473965657030667,
    1445623958975156418,
}

ALLOWED_CLANREQUEST_ROLES = {
    1284652349687861269,
    1284677493202096248,
    1284694328257544192,
    1361842372157374546,
    1284689791216255078,
}

ALLOWED_ROLE_ID = 1284689791216255078

MILESTONE_STAFF_ROLES = {
    1284652349687861269,
    1284677493202096248,
    1284694328257544192,
    1361842372157374546,
}

MILESTONE_PING_ROLE_ID = 1445526242949332993
CLAN_HELP_PING_ROLE_ID = 1286451226937917488

active_ticket_cache = {}
MILESTONE_CLAIMS_FILE = "milestone_claim_history.json"

# ----------------------------
# FOOTERS
# ----------------------------

def add_embed_footer(embed: discord.Embed) -> discord.Embed:
    """Normal embeds keep the Luna footer."""
    footer_line = "*Luna ❀⋆ coded by <@296181275344109568>*"
    if embed.description:
        embed.description = embed.description.replace(f"\n\n{footer_line}", "")
        embed.description += f"\n\n{footer_line}"
    else:
        embed.description = footer_line
    return embed

def set_milestone_footer(embed: discord.Embed, owner_id: int, milestone: str):
    """ONLY used for reward embeds. This DOES NOT show Luna footer."""
    embed.set_footer(text=f"OwnerID: {owner_id} | Milestone: {milestone}")
    return embed

def extract_footer_meta(embed: discord.Embed):
    """Reads OwnerID + Milestone from reward embeds."""
    if not embed.footer or not embed.footer.text:
        return None, None

    text = embed.footer.text
    try:
        owner = int(text.split("OwnerID:")[1].split("|")[0].strip())
        milestone = text.split("Milestone:")[1].strip()
        return owner, milestone
    except:
        return None, None

# ----------------------------
# Load / Save Claims
# ----------------------------

def load_claim_history():
    print("[load_claim_history] Loading claim history...")
    if os.path.exists(MILESTONE_CLAIMS_FILE):
        try:
            with open(MILESTONE_CLAIMS_FILE, "r") as f:
                data = json.load(f)
                print(f"[load_claim_history] Loaded {len(data.get('claims', []))} claims.")
                return data
        except Exception as e:
            print(f"[load_claim_history] ERROR reading file: {e}")
            traceback.print_exc()
            return {"claims": []}
    print("[load_claim_history] File not found, starting fresh.")
    return {"claims": []}

def save_claim_history():
    print(f"[save_claim_history] Saving {len(claim_history.get('claims', []))} claims...")
    try:
        with open(MILESTONE_CLAIMS_FILE, "w") as f:
            json.dump(claim_history, f, indent=4)
        print("[save_claim_history] Save successful.")
    except Exception as e:
        print(f"[save_claim_history] ERROR saving file: {e}")
        traceback.print_exc()

claim_history = load_claim_history()

def log_milestone_completion(user_id: int, milestone: str, reward_type: str, reward_amount: int | None):
    print(
        f"[log_milestone_completion] Logging completion: "
        f"user_id={user_id}, milestone={milestone}, reward_type={reward_type}, reward_amount={reward_amount}"
    )
    entry = {
        "user_id": user_id,
        "milestone": milestone,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "reward": {"type": reward_type, "amount": reward_amount},
    }
    claim_history["claims"].append(entry)
    save_claim_history()

def get_confirmed_milestones_for_user(user_id: int):
    print(f"[get_confirmed_milestones_for_user] Checking confirmed milestones for user_id={user_id}")
    results = set()
    for entry in claim_history.get("claims", []):
        if entry.get("user_id") != user_id:
            continue
        milestone = entry.get("milestone")
        if milestone:
            results.add(milestone)
    print(f"[get_confirmed_milestones_for_user] User {user_id} has {len(results)} completed milestones.")
    return results

# ----------------------------
# Milestone Ticket View (Persistent)
# ----------------------------

class MilestoneTicketView(discord.ui.View):
    def __init__(self, ticket_owner_id: int | None = None, milestone: str | None = None):
        super().__init__(timeout=None)
        self.ticket_owner_id = ticket_owner_id
        self.milestone = milestone or ""
        self.chosen_reward_type = None
        self.chosen_reward_amount = None
        self.confirmed = False

    # ------------
    # Helper
    # ------------

    def restore_from_footer(self, embed: discord.Embed):
        """If bot restarted, rehydrate ticket_owner + milestone."""
        owner, milestone = extract_footer_meta(embed)
        if owner:
            self.ticket_owner_id = owner
        if milestone:
            self.milestone = milestone

    def _user_is_owner(self, user):
        return user.id == self.ticket_owner_id

    def _user_is_staff(self, member):
        return any(role.id in MILESTONE_STAFF_ROLES for role in member.roles)

    # ----------------------------
    # Reward Buttons
    # ----------------------------

    @discord.ui.button(label="💠 Bits", style=discord.ButtonStyle.primary, custom_id="milestone_bits")
    async def pick_bits(self, interaction: discord.Interaction, btn):
        embed = interaction.message.embeds[0]
        self.restore_from_footer(embed)

        if interaction.user.id != self.ticket_owner_id:
            return await interaction.response.send_message("❌ Only the ticket owner can choose.", ephemeral=True)

        self.chosen_reward_type = "bits"

        await interaction.response.defer(ephemeral=True)
        await self._update_reward_embed(interaction)

    @discord.ui.button(label="🎟️ Tickets", style=discord.ButtonStyle.success, custom_id="milestone_tickets")
    async def pick_tickets(self, interaction: discord.Interaction, btn):
        embed = interaction.message.embeds[0]
        self.restore_from_footer(embed)

        if interaction.user.id != self.ticket_owner_id:
            return await interaction.response.send_message("❌ Only the ticket owner can choose.", ephemeral=True)

        tickets = REWARD_OPTIONS.get(self.milestone, {}).get("tickets", None)
        self.chosen_reward_type = "tickets"
        self.chosen_reward_amount = tickets

        await interaction.response.defer(ephemeral=True)
        await self._update_reward_embed(interaction)

    async def _update_reward_embed(self, interaction):
        msg = interaction.message
        embed = msg.embeds[0]

        embed.description = (
            f"You are claiming milestone **{self.milestone}**.\n\n"
            f"Current chosen reward:\n"
            f"{'💠 Bits' if self.chosen_reward_type=='bits' else f'🎟️ {self.chosen_reward_amount} Tickets' if self.chosen_reward_type else 'None'}\n\n"
            "Staff will press **✔️ Confirm Milestone** after manually trading the reward."
        )

        embed.set_footer(text=f"OwnerID: {self.ticket_owner_id} | Milestone: {self.milestone}")

        await msg.edit(embed=embed, view=self)

    @discord.ui.button(label="✔️ Confirm Milestone", style=discord.ButtonStyle.secondary, custom_id="milestone_confirm")
    async def confirm_milestone(self, interaction: discord.Interaction, btn):
        embed = interaction.message.embeds[0]
        self.restore_from_footer(embed)

        if not self._user_is_staff(interaction.user):
            return await interaction.response.send_message("❌ Only staff may confirm.", ephemeral=True)

        if not self.chosen_reward_type:
            return await interaction.response.send_message("⚠️ User must choose a reward first.", ephemeral=True)

        log_milestone_completion(
            user_id=self.ticket_owner_id,
            milestone=self.milestone,
            reward_type=self.chosen_reward_type,
            reward_amount=self.chosen_reward_amount,
        )

        reward_text = "Bits" if self.chosen_reward_type == "bits" else f"{self.chosen_reward_amount} Tickets"

        await interaction.response.send_message(
            f"✅ Milestone **{self.milestone}** confirmed for <@{self.ticket_owner_id}> — Reward: **{reward_text}**.",
            ephemeral=True,
        )

        await interaction.channel.send(
            f"📘 Milestone **{self.milestone}** confirmed for <@{self.ticket_owner_id}> — Reward: **{reward_text}**."
        )


        for child in self.children:
            if child.custom_id in ("milestone_bits", "milestone_tickets", "milestone_confirm"):
                child.disabled = True

        await interaction.message.edit(view=self)

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger, custom_id="milestone_close")
    async def close_ticket(self, interaction: discord.Interaction, btn):
        embed = interaction.message.embeds[0]
        self.restore_from_footer(embed)

        if not (self._user_is_owner(interaction.user) or self._user_is_staff(interaction.user)):
            return await interaction.response.send_message("❌ You cannot close this ticket.", ephemeral=True)

        if interaction.channel:
            await interaction.response.defer(ephemeral=True)
            await interaction.channel.delete()

# ----------------------------
# Milestone Select View
# ----------------------------

class MilestoneSelectView(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=300)
        self.author = author

        completed = get_confirmed_milestones_for_user(author.id)
        options = []

        for emoji, (name, _) in MILESTONE_EMOJIS.items():
            if name not in completed:
                tickets = REWARD_OPTIONS[name]["tickets"]
                options.append(
                    discord.SelectOption(label=name, value=name, description=f"{emoji} — Bits or {tickets} Tickets")
                )

        self.milestone_select.options = options

    @discord.ui.select(
        placeholder="Select your milestone...",
        min_values=1,
        max_values=1,
        options=[],
    )
    async def milestone_select(self, interaction, select):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("❌ This menu isn't for you.", ephemeral=True)

        milestone_name = select.values[0]

        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)

        await handle_milestone_selection(interaction, self.author, milestone_name)

# ----------------------------
# Milestone Ticket Handler
# ----------------------------

async def handle_milestone_selection(interaction, member, milestone_name):
    guild = interaction.guild
    channel = interaction.channel

    allowed_role = discord.utils.get(member.roles, id=ALLOWED_ROLE_ID)
    if not allowed_role:
        return await interaction.response.send_message(
            "⛔ You must have the Jobboard/Yume role to claim milestones.",
            ephemeral=True,
        )

    completed = get_confirmed_milestones_for_user(member.id)
    if milestone_name in completed:
        return await interaction.response.send_message(
            f"✅ You already claimed **{milestone_name}**.",
            ephemeral=True,
        )

    active_ticket_cache.setdefault(member.id, []).append(milestone_name)

    category = channel.category
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        member: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        **{
            guild.get_role(rid): discord.PermissionOverwrite(view_channel=True, send_messages=True)
            for rid in MILESTONE_STAFF_ROLES
            if guild.get_role(rid)
        },
    }

    ticket_channel_name = f"ticket-{member.name.lower()}-{milestone_name.split()[0]}"
    ticket_channel = await guild.create_text_channel(
        name=ticket_channel_name,
        category=category,
        overwrites=overwrites
    )

    milestone_instructions = ""
    for _, (name, instructions) in MILESTONE_EMOJIS.items():
        if name == milestone_name:
            milestone_instructions = instructions
            break

    base_embed = discord.Embed(
        title=f"🎟️ Milestone Claim — {milestone_name}",
        description=(
            f"Hello {member.mention}!\n\n"
            f"You selected **{milestone_name}**.\n\n"
            f"**Next Steps:**\n"
            f"{milestone_instructions}\n\n"
            "📝 Please provide screenshot proof here.\n"
            "Staff will review proof and press "
            "**✔️ Confirm Milestone** after manually trading the reward."
        ),
        color=0xB6E3F5,
    )
    base_embed = add_embed_footer(base_embed)

    await ticket_channel.send(f"<@&{MILESTONE_PING_ROLE_ID}>", embed=base_embed)

    reward_info = REWARD_OPTIONS[milestone_name]
    reward_embed = discord.Embed(
        title="🎁 Claim Your Reward",
        description=(
            f"You are claiming milestone **{milestone_name}**.\n\n"
            "You may choose:\n"
            f"💠 Bits\n"
            f"or\n"
            f"🎟️ {reward_info['tickets']} Tickets\n\n"
            "> Use the buttons below to choose.\n"
            "> Staff will confirm **after** trading."
        ),
        color=0xFFD18E,
    )
    reward_embed = set_milestone_footer(reward_embed, member.id, milestone_name)

    view = MilestoneTicketView(ticket_owner_id=member.id, milestone=milestone_name)
    await ticket_channel.send(embed=reward_embed, view=view)

    await interaction.response.send_message(
        f"📩 Ticket created in {ticket_channel.mention} for **{milestone_name}**!",
        ephemeral=True,
    )

# ----------------------------
# JOBREWARD COMMAND
# ----------------------------

@commands.command(name="jobreward")
async def jobreward(ctx, *, query=None):
    if not query:
        return await ctx.send("❌ Usage: `!jobreward USER`")

    query_l = query.lower().strip()
    target = None

    if query_l.startswith("<@") and query_l.endswith(">"):
        try:
            uid = int(query_l.replace("<", "").replace(">", "").replace("@", "").replace("!", ""))
            target = ctx.guild.get_member(uid)
        except:
            pass

    if not target and query_l.isdigit():
        target = ctx.guild.get_member(int(query_l))

    if not target:
        for m in ctx.guild.members:
            if query_l in m.display_name.lower() or query_l in m.name.lower():
                target = m
                break

    if not target:
        return await ctx.send(f"❌ Could not find `{query}`")

    user_claims = [c for c in claim_history["claims"] if c.get("user_id") == target.id]
    if not user_claims:
        return await ctx.send(f"📭 No milestone claims found for {target.mention}.")

    user_claims.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    lines = []
    for c in user_claims:
        ts = c.get("timestamp")
        try:
            dt = datetime.datetime.fromisoformat(ts).astimezone(datetime.timezone.utc)
            ts_text = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            ts_text = ts or "Unknown time"

        milestone = c.get("milestone", "Unknown")
        reward = c.get("reward", {})
        reward_text = f"{reward.get('amount')} {reward.get('type')}" if reward else "No reward recorded"

        lines.append(f"**{ts_text}** — {milestone} — 🎁 {reward_text}")

    embed = discord.Embed(
        title=f"🌙 Milestone Claims for {target.display_name}",
        description="\n".join(lines),
        color=0xFFC5D3,
    )
    embed = add_embed_footer(embed)
    await ctx.send(embed=embed)

# ----------------------------
# CLAN REQUEST UI
# ----------------------------

CLAN_REQUEST_TYPES = {
    "bit_frame": "Bit Frame",
    "bit_frame_dye": "Bit Frame + Dye",
    "bit_swap": "Bit Swap",
    "rental": "Rental",
    "work_permit": "Work Permit",
}

class ClanRequestView(discord.ui.View):
    def __init__(self, bot, author, clan_channel_id):
        super().__init__(timeout=300)
        self.bot = bot
        self.author = author
        self.clan_channel_id = clan_channel_id

        self.request_select.options = [
            discord.SelectOption(label=label, value=key)
            for key, label in CLAN_REQUEST_TYPES.items()
        ]

    @discord.ui.select(
        placeholder="Select request type...",
        min_values=1,
        max_values=1,
        options=[]
    )
    async def request_select(self, interaction, select):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("❌ This menu isn't for you.", ephemeral=True)

        request_key = select.values[0]
        request_label = CLAN_REQUEST_TYPES.get(request_key, "Unknown")

        await interaction.response.send_message(
            f"{interaction.user.mention} ✏️ Please type your **jobboard contribution** number below.",
            ephemeral=False,
        )

        def check(msg):
            return msg.author.id == self.author.id and msg.channel == interaction.channel

        try:
            msg = await self.bot.wait_for("message", timeout=120, check=check)
        except asyncio.TimeoutError:
            return await interaction.followup.send("⏰ Timed out. Run command again.", ephemeral=True)

        contribution_value = msg.content.strip()
        clan_channel = interaction.guild.get_channel(self.clan_channel_id) or interaction.channel

        embed = discord.Embed(
            title="📌 Clan Request",
            color=0xF1DBB6,
        )
        embed.add_field(name="Request", value=request_label, inline=False)
        embed.add_field(name="Requested By", value=self.author.mention, inline=False)
        embed.add_field(name="Jobboard Contribution", value=contribution_value, inline=False)
        embed = add_embed_footer(embed)

        if CLAN_HELP_PING_ROLE_ID:
            await clan_channel.send(f"<@&{CLAN_HELP_PING_ROLE_ID}>", embed=embed)
        else:
            await clan_channel.send(embed=embed)

        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)

        await interaction.followup.send("✅ Your clan request has been submitted.", ephemeral=True)

# ----------------------------
# CLANREQUEST COMMAND
# ----------------------------

@commands.hybrid_command(name="clanrequest", with_app_command=True)
async def clanrequest_command(ctx):
    member = ctx.author
    channel = ctx.channel

    allowed = (
        member.guild_permissions.manage_guild
        or member.guild_permissions.manage_channels
        or any(role.id in ALLOWED_CLANREQUEST_ROLES for role in member.roles)
    )

    if not allowed:
        return await ctx.send("⛔ You do not have permission to create clan requests.")

    if channel.id not in CLANREQUEST_ALLOWED_CHANNELS:
        channels = ", ".join(f"<#{cid}>" for cid in CLANREQUEST_ALLOWED_CHANNELS)
        return await ctx.send(f"🚫 This command can only be used in:\n{channels}")

    embed = discord.Embed(
        title="📌 Clan Request Setup",
        description=(
            "Choose a request type.\n\n"
            "--- Types ---\n"
            "- Bit Frame\n"
            "- Bit Frame + Dye\n"
            "- Bit Swap\n"
            "- Rental\n"
            "- Work Permit\n\n"
            "After choosing, you'll enter your **jobboard contribution** number."
        ),
        color=0xF1DBB6,
    )
    embed = add_embed_footer(embed)

    view = ClanRequestView(ctx.bot, ctx.author, channel.id)
    await ctx.send(embed=embed, view=view)



# ----------------------------
# HYBRID COMMAND: milestone
# ----------------------------

@commands.hybrid_command(name="milestone", with_app_command=True)
async def milestone_command(ctx: commands.Context):
    """Open the milestone selection menu."""
    member = ctx.author

    allowed_role = discord.utils.get(member.roles, id=ALLOWED_ROLE_ID)
    if not allowed_role:
        return await ctx.send(
            "⛔ You must have the Jobboard/Yume role to use this command."
        )


    completed = get_confirmed_milestones_for_user(member.id)
    remaining = [
        name for _, (name, _) in MILESTONE_EMOJIS.items()
        if name not in completed
    ]

    if not remaining:
        embed = discord.Embed(
            title="Job Board Milestones Rewards",
            description="🎉 You have already **fully claimed all milestones**!",
            color=0xFFC5D3
        )
        embed = add_embed_footer(embed)
        return await ctx.send(embed=embed)


    embed = discord.Embed(
        title="Job Board Milestones Rewards",
        description=(
            "Select a milestone below to open a ticket and claim your reward!\n\n"
            "1️⃣ — 1200 Effort *(Bits or 5 Tickets)*\n"
            "2️⃣ — 1500 Effort *(Bits or 7 Tickets)*\n"
            "3️⃣ — 2000 Effort *(Bits or 10 Tickets)*\n\n"
            "> This menu **opens a ticket** in a new channel.\n"
            "> Staff will later CONFIRM and log this milestone."
        ),
        color=0xFFC5D3,
    )
    embed = add_embed_footer(embed)

    view = MilestoneSelectView(member)

    if len(view.milestone_select.options) == 0:
        return await ctx.send(
            "🎉 You have already claimed **all milestones**!",
            embed=embed
        )

    await ctx.send(embed=embed, view=view)


# ----------------------------
# MILESTONE RESET
# ----------------------------

@commands.command(name="milestonereset")
async def milestonereset(ctx, target: discord.Member = None):
    WL = {296181275344109568, 1370076515429253264}

    if ctx.author.id not in WL:
        return await ctx.send("⛔ You do not have permission to use this command.")

    if target is None:
        target = ctx.author

    global claim_history
    old_count = len(claim_history["claims"])

    new_claims = [c for c in claim_history["claims"] if c.get("user_id") != target.id]
    removed = old_count - len(new_claims)

    claim_history["claims"] = new_claims
    save_claim_history()

    if target.id in active_ticket_cache:
        active_ticket_cache.pop(target.id, None)

    await ctx.send(
        f"🧹 Cleared **{removed}** milestone logs for {target.mention}.\n"
        "They may now reclaim milestones from scratch."
    )

# ----------------------------
# EXTENSION SETUP
# ----------------------------

async def setup(bot: commands.Bot):
    print("[milestone/clanrequest] Loading extension…")
    bot.add_command(milestone_command)
    bot.add_command(clanrequest_command)
    bot.add_command(jobreward)
    bot.add_command(milestonereset)
    print("[milestone/clanrequest] Extension loaded.")
