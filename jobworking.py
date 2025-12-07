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

# Yume role required to RUN /milestone
ALLOWED_CLANREQUEST_ROLES = {
    1284652349687861269,  # Yume Kami
    1284677493202096248,  # Yume Staff
    1284694328257544192,  # Yume Host
    1361842372157374546,  # Yume Mod
    1284689791216255078,  # Yume Non-Admin Yume Role
}


ALLOWED_ROLE_ID = 1284689791216255078


MILESTONE_STAFF_ROLES = {
    1284652349687861269,  # Yume Kami
    1284677493202096248,  # Yume Staff
    1284694328257544192,  # Yume Host
    1361842372157374546,  # Yume Mod
}

MILESTONE_PING_ROLE_ID = 1445526242949332993
CLAN_HELP_PING_ROLE_ID = 1286451226937917488


active_ticket_cache = {}  # {user_id: [milestone_name, ...]}
MILESTONE_CLAIMS_FILE = "milestone_claim_history.json"

# ----------------------------
# Footer Helper
# ----------------------------

def add_embed_footer(embed: discord.Embed) -> discord.Embed:
    footer_line = "*Luna ❀⋆ coded by <@296181275344109568>*"


    if embed.description:
        embed.description = embed.description.replace(f"\n\n{footer_line}", "")


    if embed.description:
        embed.description += f"\n\n{footer_line}"
    else:
        embed.description = footer_line

    return embed

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
        "reward": {
            "type": reward_type,
            "amount": reward_amount,
        },
    }
    claim_history["claims"].append(entry)
    save_claim_history()


def get_confirmed_milestones_for_user(user_id: int):
    """
    Return a set of milestones this user has confirmed.

    We treat a milestone as confirmed if:
    - There is a 'reward' dict with type/amount, OR
    - There is an old-style 'reward_choice', OR
    - There is a boolean 'confirmed' flag set to True.
    """
    print(f"[get_confirmed_milestones_for_user] Checking confirmed milestones for user_id={user_id}")
    results = set()

    for entry in claim_history.get("claims", []):
        if entry.get("user_id") != user_id:
            continue

        milestone = entry.get("milestone")
        if not milestone:
            continue

        reward_data = entry.get("reward")
        reward_choice = entry.get("reward_choice")
        confirmed_flag = entry.get("confirmed", False)

        if reward_data or reward_choice or confirmed_flag:
            print(f"[get_confirmed_milestones_for_user] Found confirmed milestone: {milestone}")
            results.add(milestone)

    print(f"[get_confirmed_milestones_for_user] User {user_id} has {len(results)} completed milestones.")
    return results


# ----------------------------
# Milestone Ticket View
# ----------------------------

class MilestoneTicketView(discord.ui.View):
    def __init__(self, ticket_owner_id: int | None = None, milestone: str | None = None):
        super().__init__(timeout=None)
        self.timeout = None
        self.ticket_owner_id = ticket_owner_id
        self.milestone = milestone or ""
        self.chosen_reward_type: str | None = None
        self.chosen_reward_amount: int | None = None
        self.confirmed: bool = False
        print(f"[MilestoneTicketView.__init__] Created for user={ticket_owner_id}, milestone='{self.milestone}'")

    def _user_is_owner(self, user: discord.Member | discord.User) -> bool:
        return self.ticket_owner_id is not None and user.id == self.ticket_owner_id

    def _user_is_staff(self, member: discord.Member) -> bool:
        return any(role.id in MILESTONE_STAFF_ROLES for role in member.roles)

    async def _update_reward_embed(self, interaction: discord.Interaction):
        print(
            f"[MilestoneTicketView._update_reward_embed] Updating reward embed: "
            f"user={interaction.user.id}, chosen_type={self.chosen_reward_type}, "
            f"chosen_amount={self.chosen_reward_amount}"
        )
        msg = interaction.message
        embed = msg.embeds[0] if msg.embeds else discord.Embed(title="🎁 Claim Your Reward")

        reward_text = "None yet."
        if self.chosen_reward_type == "bits":
            reward_text = "💠 **Bits**"
        elif self.chosen_reward_type == "tickets":
            reward_text = f"🎟️ **{self.chosen_reward_amount} Tickets**"

        embed.title = "🎁 Claim Your Reward"
        embed.description = (
            f"You are claiming milestone **{self.milestone}**.\n\n"
            f"Current chosen reward:\n{reward_text}\n\n"
            "Staff will press **✔️ Confirm Milestone** after manually trading the reward."
        )

        await msg.edit(embed=embed, view=self)

    def _maybe_add_confirm_button(self):
        """Add Confirm Milestone button only AFTER user chooses a reward (not used in Option A)."""
        if self.chosen_reward_type is None:
            return

        if any(
            isinstance(child, discord.ui.Button) and child.label == "✔️ Confirm Milestone"
            for child in self.children
        ):
            return


    async def _restore_reward_view(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Revives the reward selection View if the ticket wasn't deleted."""
        print("[_restore_reward_view] Restoring reward UI.")

        reward_info = REWARD_OPTIONS.get(self.milestone)
        if not reward_info:
            print("[_restore_reward_view] No reward info found.")
            return await interaction.response.send_message(
                "⚠️ Could not restore reward options.",
                ephemeral=True,
            )

        reward_embed = discord.Embed(
            title="🎁 Claim Your Reward",
            description=(
                f"You are claiming milestone **{self.milestone}**.\n\n"
                f"You may choose:\n"
                f"💠 Bits\n"
                f"or\n"
                f"🎟️ {reward_info['tickets']} Tickets\n\n"
                "> Use the buttons below to choose.\n"
                "> Staff will confirm **after** trading."
            ),
            color=0xFFD18E,
        )
        reward_embed = add_embed_footer(reward_embed)

        view = MilestoneTicketView(
            ticket_owner_id=self.ticket_owner_id,
            milestone=self.milestone
        )
        await channel.send(embed=reward_embed, view=view)

        return await interaction.response.send_message(
            "♻️ Ticket UI restored!",
            ephemeral=True,
        )

    async def _send_reward_picker(self, channel, ticket_owner, milestone):
        """Used when reopening a fully deleted ticket channel."""
        reward_info = REWARD_OPTIONS.get(milestone)
        if not reward_info:
            print("[_send_reward_picker] No reward info found.")
            return

        reward_embed = discord.Embed(
            title="🎁 Claim Your Reward",
            description=(
                f"You are claiming milestone **{milestone}**.\n\n"
                f"You may choose:\n"
                f"💠 Bits\n"
                f"or\n"
                f"🎟️ {reward_info['tickets']} Tickets\n\n"
                "> Use the buttons below to choose.\n"
                "> Staff will confirm **after** trading."
            ),
            color=0xFFD18E,
        )
        reward_embed = add_embed_footer(reward_embed)

        view = MilestoneTicketView(
            ticket_owner_id=ticket_owner.id,
            milestone=milestone
        )
        await channel.send(embed=reward_embed, view=view)

    @discord.ui.button(
        label="💠 Bits",
        style=discord.ButtonStyle.primary,
        custom_id="milestone_bits"
    )
    async def pick_bits(self, interaction: discord.Interaction, btn: discord.ui.Button):
        print(f"[MilestoneTicketView.pick_bits] Clicked by user={interaction.user.id}")
        if not self._user_is_owner(interaction.user):
            print("[MilestoneTicketView.pick_bits] Rejected: not ticket owner")
            return await interaction.response.send_message(
                "❌ Only the ticket owner can choose the reward.",
                ephemeral=True,
            )

        self.chosen_reward_type = "bits"
        self.chosen_reward_amount = None
        await interaction.response.defer(ephemeral=True)
        await self._update_reward_embed(interaction)

    @discord.ui.button(
        label="🎟️ Tickets",
        style=discord.ButtonStyle.success,
        custom_id="milestone_tickets"
    )
    async def pick_tickets(self, interaction: discord.Interaction, btn: discord.ui.Button):
        print(f"[MilestoneTicketView.pick_tickets] Clicked by user={interaction.user.id}")
        if not self._user_is_owner(interaction.user):
            print("[MilestoneTicketView.pick_tickets] Rejected: not ticket owner")
            return await interaction.response.send_message(
                "❌ Only the ticket owner can choose the reward.",
                ephemeral=True,
            )

        tickets = REWARD_OPTIONS.get(self.milestone, {}).get("tickets")
        print(f"[MilestoneTicketView.pick_tickets] tickets configured={tickets}")
        if tickets is None:
            return await interaction.response.send_message(
                "⚠️ Ticket amount for this milestone is not configured.",
                ephemeral=True,
            )

        self.chosen_reward_type = "tickets"
        self.chosen_reward_amount = tickets
        await interaction.response.defer(ephemeral=True)
        await self._update_reward_embed(interaction)

    @discord.ui.button(
        label="✔️ Confirm Milestone",
        style=discord.ButtonStyle.secondary,
        custom_id="milestone_confirm"
    )
    async def confirm_milestone(self, interaction: discord.Interaction, btn: discord.ui.Button):
        print(f"[MilestoneTicketView.confirm_milestone] Clicked by user={interaction.user.id}")
        if not isinstance(interaction.user, discord.Member):
            print("[MilestoneTicketView.confirm_milestone] Rejected: interaction user not a Member")
            return await interaction.response.send_message(
                "❌ Only staff can confirm milestones.",
                ephemeral=True,
            )

        if not self._user_is_staff(interaction.user):
            print("[MilestoneTicketView.confirm_milestone] Rejected: user not staff")
            return await interaction.response.send_message(
                "❌ You do not have permission to confirm milestones.",
                ephemeral=True,
            )

        if self.confirmed:
            print("[MilestoneTicketView.confirm_milestone] Already confirmed")
            return await interaction.response.send_message(
                "✅ This milestone has already been confirmed.",
                ephemeral=True,
            )

        if self.chosen_reward_type is None:
            print("[MilestoneTicketView.confirm_milestone] No reward chosen yet")
            return await interaction.response.send_message(
                "⚠️ The user must choose **Bits** or **Tickets** first.",
                ephemeral=True,
            )

        log_milestone_completion(
            user_id=self.ticket_owner_id,
            milestone=self.milestone,
            reward_type=self.chosen_reward_type,
            reward_amount=self.chosen_reward_amount,
        )

        self.confirmed = True
        btn.disabled = True

        for child in self.children:
            if not isinstance(child, discord.ui.Button):
                continue

            if child.label in {"💠 Bits", "🎟️ Tickets", "✔️ Confirm Milestone"}:
                child.disabled = True

        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.label == "🔒 Close Ticket":
                child.disabled = False

        await interaction.response.send_message(
            f"✅ Milestone **{self.milestone}** logged for <@{self.ticket_owner_id}>.",
            ephemeral=True,
        )

        channel = interaction.channel
        if channel:
            reward_text = "Bits" if self.chosen_reward_type == "bits" else f"{self.chosen_reward_amount} Tickets"
            print(f"[MilestoneTicketView.confirm_milestone] Sending public confirmation message in channel={channel.id}")
            await channel.send(
                f"📘 Milestone **{self.milestone}** confirmed for <@{self.ticket_owner_id}> — Reward: **{reward_text}**."
            )

        try:
            await interaction.message.edit(view=self)
            print("[MilestoneTicketView.confirm_milestone] View updated (buttons disabled)")
        except Exception as e:
            print(f"[MilestoneTicketView.confirm_milestone] ERROR editing message: {e}")
            traceback.print_exc()

    @discord.ui.button(
        label="🔒 Close Ticket",
        style=discord.ButtonStyle.danger,
        custom_id="milestone_close"
    )
    async def close_ticket(self, interaction: discord.Interaction, btn: discord.ui.Button):
        print(f"[MilestoneTicketView.close_ticket] Clicked by user={interaction.user.id}")

        if not isinstance(interaction.user, discord.Member):
            print("[MilestoneTicketView.close_ticket] Rejected: user not Member")
            return await interaction.response.send_message(
                "❌ You cannot close this ticket.",
                ephemeral=True,
            )

        if not (self._user_is_owner(interaction.user) or self._user_is_staff(interaction.user)):
            print("[MilestoneTicketView.close_ticket] Rejected: not owner or staff")
            return await interaction.response.send_message(
                "❌ You do not have permission to close this ticket.",
                ephemeral=True,
            )

        milestones = active_ticket_cache.get(self.ticket_owner_id, [])
        if self.milestone in milestones:
            milestones.remove(self.milestone)
            if not milestones:
                active_ticket_cache.pop(self.ticket_owner_id, None)
            print(f"[MilestoneTicketView.close_ticket] Removed milestone '{self.milestone}' from active cache.")

        try:
            await interaction.response.defer(ephemeral=True, thinking=False)
        except:
            pass

        print(f"[MilestoneTicketView.close_ticket] Deleting channel id={interaction.channel.id}")
        await interaction.channel.delete()




# ----------------------------
# Milestone Selection UI
# ----------------------------

class MilestoneSelectView(discord.ui.View):
    def __init__(self, author: discord.Member):
        super().__init__(timeout=300)
        self.author = author

        print(f"[MilestoneSelectView.__init__] Building menu for user={author.id}")
        completed = get_confirmed_milestones_for_user(author.id)
        available_milestones = [
            (emoji, name)
            for emoji, (name, _) in MILESTONE_EMOJIS.items()
            if name not in completed
        ]
        print(f"[MilestoneSelectView.__init__] Available milestones={available_milestones}")

        options = []
        for emoji, name in available_milestones:
            tickets = REWARD_OPTIONS.get(name, {}).get("tickets", "?")
            options.append(
                discord.SelectOption(
                    label=name,
                    value=name,
                    description=f"{emoji} — choose Bits or {tickets} Tickets",
                )
            )

        self.milestone_select.options = options
        print(f"[MilestoneSelectView.__init__] Options set, count={len(options)}")

    @discord.ui.select(
        placeholder="Select your milestone...",
        min_values=1,
        max_values=1,
        options=[],
    )
    async def milestone_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        print(
            f"[MilestoneSelectView.milestone_select] Triggered by user={interaction.user.id}, "
            f"values={select.values}"
        )
        if interaction.user.id != self.author.id:
            print("[MilestoneSelectView.milestone_select] Rejected: not author")
            return await interaction.response.send_message(
                "❌ This menu isn't for you.",
                ephemeral=True,
            )

        milestone_name = select.values[0]
        print(f"[MilestoneSelectView.milestone_select] User selected milestone='{milestone_name}'")

        for child in self.children:
            child.disabled = True
        try:
            await interaction.message.edit(view=self)
            print("[MilestoneSelectView.milestone_select] View updated (dropdown disabled)")
        except Exception as e:
            print(f"[MilestoneSelectView.milestone_select] ERROR editing message: {e}")
            traceback.print_exc()

        await handle_milestone_selection(interaction, self.author, milestone_name)


# ----------------------------
# Milestone Selection Handler
# ----------------------------

async def handle_milestone_selection(
    interaction: discord.Interaction,
    member: discord.Member,
    milestone_name: str,
):
    print(
        f"[handle_milestone_selection] Start: user={member.id}, "
        f"milestone='{milestone_name}', guild={interaction.guild.id if interaction.guild else None}, "
        f"channel={interaction.channel.id if interaction.channel else None}"
    )
    try:
        guild = interaction.guild
        channel = interaction.channel

        allowed_role = discord.utils.get(member.roles, id=ALLOWED_ROLE_ID)
        print(f"[handle_milestone_selection] allowed_role={allowed_role}")
        if not allowed_role:
            print("[handle_milestone_selection] User missing required role.")
            return await interaction.response.send_message(
                "⛔ You must have the Jobboard/Yume role to claim milestones.",
                ephemeral=True,
            )

        completed = get_confirmed_milestones_for_user(member.id)
        if milestone_name in completed:
            print("[handle_milestone_selection] Milestone already claimed previously.")
            return await interaction.response.send_message(
                f"✅ You already claimed **{milestone_name}**.",
                ephemeral=True,
            )

        already = active_ticket_cache.get(member.id, [])
        print(f"[handle_milestone_selection] Currently open milestones for user={already}")
        if milestone_name in already:
            print("[handle_milestone_selection] Ticket already open for this milestone.")
            return await interaction.response.send_message(
                f"⚠️ You already have an open ticket for **{milestone_name}**!",
                ephemeral=True,
            )

        active_ticket_cache.setdefault(member.id, []).append(milestone_name)
        print(f"[handle_milestone_selection] Added to active_ticket_cache: {active_ticket_cache[member.id]}")

        category = channel.category if channel else None
        print(f"[handle_milestone_selection] Ticket category={category.id if category else None}")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=False,
                send_messages=False,
                read_message_history=False
            ),

            member: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
            ),

            **{
                guild.get_role(rid): discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    manage_messages=True,
                    attach_files=True,
                )
                for rid in MILESTONE_STAFF_ROLES
                if guild.get_role(rid) is not None
            },
        }

        ticket_channel_name = f"ticket-{member.name.lower()}-{milestone_name.split()[0]}"
        print(f"[handle_milestone_selection] Creating channel '{ticket_channel_name}'")
        ticket_channel = await guild.create_text_channel(
            name=ticket_channel_name,
            category=category,
            overwrites=overwrites,
        )
        print(f"[handle_milestone_selection] Ticket channel created: id={ticket_channel.id}")

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
        ping_str = f"<@&{MILESTONE_PING_ROLE_ID}>" if MILESTONE_PING_ROLE_ID else None
        print(f"[handle_milestone_selection] Sending intro embed to ticket channel, ping={ping_str}")
        await ticket_channel.send(content=ping_str, embed=base_embed)

        reward_info = REWARD_OPTIONS.get(milestone_name)
        if reward_info:
            print(f"[handle_milestone_selection] Sending reward selection embed: reward_info={reward_info}")
            reward_embed = discord.Embed(
                title="🎁 Claim Your Reward",
                description=(
                    f"You are claiming milestone **{milestone_name}**.\n\n"
                    f"You may choose:\n"
                    f"💠 Bits\n"
                    f"or\n"
                    f"🎟️ {reward_info['tickets']} Tickets\n\n"
                    "> Use the buttons below to choose.\n"
                    "> Staff will confirm **after** trading."
                ),
                color=0xFFD18E,
            )
            reward_embed = add_embed_footer(reward_embed)
            view = MilestoneTicketView(ticket_owner_id=member.id, milestone=milestone_name)
            await ticket_channel.send(embed=reward_embed, view=view)

        print("[handle_milestone_selection] Sending ephemeral confirmation to user.")
        await interaction.response.send_message(
            f"📩 Ticket created in {ticket_channel.mention} for **{milestone_name}**!",
            ephemeral=True,
        )

    except Exception as e:
        print(f"[handle_milestone_selection] ERROR: {e}")
        traceback.print_exc()
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ An error occurred while creating the ticket. Please contact staff.",
                    ephemeral=True,
                )
            else:
                await interaction.followup.send(
                    "❌ An error occurred while creating the ticket. Please contact staff.",
                    ephemeral=True,
                )
        except Exception as e2:
            print(f"[handle_milestone_selection] ERROR sending error message: {e2}")
            traceback.print_exc()


TEST_ALLOWED_USERS = {
    1370076515429253264,
    296181275344109568
}

# ----------------------------
# HYBRID COMMAND: milestone
# ----------------------------
@commands.hybrid_command(name="milestone", with_app_command=True)
async def milestone_command(ctx: commands.Context):
    """Open the milestone selection menu."""
    member = ctx.author
    print(
        f"[milestone_command] Invoked by user={member.id} ({member}) "
        f"in guild={ctx.guild.id if ctx.guild else None}, channel={ctx.channel.id if ctx.channel else None}"
    )

    try:

        allowed_role = discord.utils.get(member.roles, id=ALLOWED_ROLE_ID)
        print(f"[milestone_command] allowed_role={allowed_role}")
        if not allowed_role:
            print("[milestone_command] User missing required role.")
            return await ctx.send(
                "⛔ You must have the Jobboard/Yume role to use this command."
            )

        if member.id in TEST_ALLOWED_USERS:
            print("[milestone_command] TEST user path, no restrictions.")
            embed = discord.Embed(
                title="Job Board Milestones Rewards",
                description=(
                    "Select any milestone below to open a ticket!\n\n"
                    "1️⃣ — 1200 Effort *(Bits or 5 Tickets)*\n"
                    "2️⃣ — 1500 Effort *(Bits or 7 Tickets)*\n"
                    "3️⃣ — 2000 Effort *(Bits or 10 Tickets)*\n\n"
                    "> This menu **only opens a ticket**.\n"
                    "> Staff will later CONFIRM this milestone and log it in history."
                ),
                color=0x97FFA9,
            )
            view = MilestoneSelectView(member)

            if len(view.milestone_select.options) == 0:
                print("[milestone_command] No milestones left — sending simple message instead of dropdown.")
                return await ctx.send(
                    "🎉 You have already claimed **all milestones**!\n"
                    "> No available rewards remain.",
                    embed=add_embed_footer(embed)
                )

            print("[milestone_command] Sending milestone selection embed+view.")
            return await ctx.send(embed=embed, view=view)

        completed = get_confirmed_milestones_for_user(member.id)
        print(f"[milestone_command] Completed milestones for user: {completed}")

        remaining = [
            name
            for _, (name, _) in MILESTONE_EMOJIS.items()
            if name not in completed
        ]
        print(f"[milestone_command] Remaining milestones for user: {remaining}")

        if not remaining:
            print("[milestone_command] User already fully claimed all milestones.")
            return await ctx.send(
                "✅ You have already **fully claimed all milestones**!"
            )

        embed = discord.Embed(
            title="Job Board Milestones Rewards",
            description=(
                "Select a milestone below to open a ticket and claim your reward!\n\n"
                "1️⃣ — 1200 Effort *(Bits or 5 Tickets)*\n"
                "2️⃣ — 1500 Effort *(Bits or 7 Tickets)*\n"
                "3️⃣ — 2000 Effort *(Bits or 10 Tickets)*\n\n"
                "> This menu **only opens a ticket**.\n"
                "> Staff will later CONFIRM this milestone and log it in history."
            ),
            color=0xFFC5D3,
        )
        embed = add_embed_footer(embed)
        view = MilestoneSelectView(member)

        if len(view.milestone_select.options) == 0:
            print("[milestone_command] No milestones left — sending simple message instead of dropdown.")
            return await ctx.send(
                "🎉 You have already claimed **all milestones**!",
                embed=embed
            )

        print("[milestone_command] Sending milestone selection embed+view.")
        await ctx.send(embed=embed, view=view)

    except Exception as e:
        print(f"[milestone_command] ERROR: {e}")
        traceback.print_exc()
        try:
            await ctx.send("❌ An internal error occurred while running this command.")
        except Exception as e2:
            print(f"[milestone_command] ERROR sending error message: {e2}")
            traceback.print_exc()

# ----------------------------
# Claim history command
# ----------------------------

@commands.command(name="jobreward")
async def jobreward(ctx, *, query: str = None):
    if not query:
        return await ctx.send("❌ Usage: `!jobreward USER`")

    target = None
    query_l = query.lower().strip()


    if query_l.startswith("<@") and query_l.endswith(">"):
        try:
            uid = int(
                query_l.replace("<", "")
                .replace(">", "")
                .replace("@", "")
                .replace("!", "")
            )
            target = ctx.guild.get_member(uid)
        except Exception:
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

    user_claims = [
        c for c in claim_history["claims"] if c.get("user_id") == target.id
    ]

    if not user_claims:
        return await ctx.send(f"📭 No milestone claims found for {target.mention}.")

    user_claims.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    lines = []
    for c in user_claims:
        ts = c.get("timestamp")
        try:
            dt = datetime.datetime.fromisoformat(ts).astimezone(
                datetime.timezone.utc
            )
            ts_text = dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            ts_text = ts or "Unknown time"

        milestone = c.get("milestone", "Unknown")


        reward_data = c.get("reward")
        if isinstance(reward_data, dict):
            r_type = reward_data.get("type")
            r_amount = reward_data.get("amount")
            if r_type == "tickets":
                reward_text = f"{r_amount} Tickets"
            elif r_type == "bits":
                reward_text = "Bits"
            else:
                reward_text = "Unknown reward"

        elif "reward_choice" in c:
            reward_text = c["reward_choice"]
        else:
            reward_text = "No reward recorded"

        lines.append(
            f"**{ts_text}** — {milestone} — 🎁 {reward_text}"
        )

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
    def __init__(self, bot, author: discord.Member, clan_channel_id: int):
        super().__init__(timeout=300)
        self.bot = bot
        self.author = author
        self.clan_channel_id = clan_channel_id

        print(f"[ClanRequestView] View created for author={author.id} in channel={clan_channel_id}")

        self.request_select.options = [
            discord.SelectOption(label=label, value=key)
            for key, label in CLAN_REQUEST_TYPES.items()
        ]

    @discord.ui.select(
        placeholder="Select request type...",
        min_values=1,
        max_values=1,
        options=[],
    )
    async def request_select(self, interaction: discord.Interaction, select: discord.ui.Select):

        print(f"[ClanRequestView] request_select triggered by user={interaction.user.id}")

        if interaction.user.id != self.author.id:
            print(f"[ClanRequestView] Rejected: interaction user is not author")
            return await interaction.response.send_message(
                "❌ This menu isn't for you.",
                ephemeral=True,
            )

        request_key = select.values[0]
        request_label = CLAN_REQUEST_TYPES.get(request_key, "Unknown")
        print(f"[ClanRequestView] User chose request: key={request_key}, label={request_label}")

        await interaction.response.send_message(
            f"{interaction.user.mention} ✏️ Please type your **jobboard contribution** number below.",
            ephemeral=False,
        )

        print("[ClanRequestView] Waiting for user message...")

        def check(msg: discord.Message):
            valid = (
                msg.author.id == self.author.id
                and msg.channel == interaction.channel
            )

            if valid:
                print(f"[ClanRequestView] Message detected: author={msg.author.id}, content='{msg.content}'")
            else:
                print(
                    f"[ClanRequestView] Ignored message: "
                    f"author={msg.author.id}, "
                    f"channel={msg.channel.id}, "
                    f"content='{msg.content}'"
                )

            return valid

        try:
            msg = await self.bot.wait_for("message", timeout=120, check=check)
            print("[ClanRequestView] wait_for passed successfully")
        except asyncio.TimeoutError:
            print("[ClanRequestView] TIMEOUT: Did not receive user message within 120 seconds")
            return await interaction.followup.send(
                "⏰ Timed out waiting for contribution. Please run the command again.",
                ephemeral=True,
            )
        except Exception as e:
            print(f"[ClanRequestView] ERROR in wait_for: {e}")
            traceback.print_exc()
            return await interaction.followup.send(
                "❌ An internal error occurred.",
                ephemeral=True,
            )

        contribution_value = msg.content.strip()
        print(f"[ClanRequestView] Contribution received: '{contribution_value}'")

        clan_channel = interaction.guild.get_channel(self.clan_channel_id) or interaction.channel
        print(f"[ClanRequestView] Target post channel resolved as: {clan_channel.id}")

        embed = discord.Embed(
            title="📌 Clan Request",
            color=0xF1DBB6,
        )
        embed.add_field(name="Request", value=request_label, inline=False)
        embed.add_field(name="Requested By", value=self.author.mention, inline=False)
        embed.add_field(name="Jobboard Contribution", value=contribution_value, inline=False)
        embed.add_field(
            name="\u200b",
            value="*Luna ❀⋆ coded by <@296181275344109568>*",
            inline=False,
        )

        try:
            if CLAN_HELP_PING_ROLE_ID:
                print(f"[ClanRequestView] Sending embed with ping role={CLAN_HELP_PING_ROLE_ID}")
                await clan_channel.send(f"<@&{CLAN_HELP_PING_ROLE_ID}>", embed=embed)
            else:
                print("[ClanRequestView] Sending embed without ping")
                embed = add_embed_footer(embed)
                await clan_channel.send(embed=embed)

            print("[ClanRequestView] Embed successfully sent to target channel")

        except Exception as e:
            print(f"[ClanRequestView] ERROR sending embed: {e}")
            traceback.print_exc()
            return await interaction.followup.send(
                "❌ Failed to send request embed.",
                ephemeral=True,
            )

        print("[ClanRequestView] Disabling dropdown UI")
        for child in self.children:
            child.disabled = True

        try:
            await interaction.message.edit(view=self)
            print("[ClanRequestView] UI updated (dropdown disabled)")
        except Exception as e:
            print(f"[ClanRequestView] ERROR while editing menu view: {e}")
            traceback.print_exc()

        try:
            await interaction.followup.send(
                "✅ Your clan request has been submitted.",
                ephemeral=True,
            )
            print("[ClanRequestView] Success followup sent")
        except Exception as e:
            print(f"[ClanRequestView] ERROR sending followup: {e}")
            traceback.print_exc()


# ----------------------------
# HYBRID COMMAND: clanrequest
# ----------------------------

@commands.hybrid_command(name="clanrequest", with_app_command=True)
async def clanrequest_command(ctx: commands.Context):
    """
    Create a clan request entry.
    Slash: /clanrequest
    Prefix: !clanrequest
    """

    member = ctx.author
    channel = ctx.channel
    print(f"[clanrequest_command] Invoked by user={member.id} in channel={channel.id}")

    allowed = (
        member.guild_permissions.manage_guild
        or member.guild_permissions.manage_channels
        or any(role.id in ALLOWED_CLANREQUEST_ROLES for role in member.roles)
    )

    print(f"[clanrequest_command] allowed={allowed}")
    if not allowed:
        return await ctx.send(
            "⛔ You do not have permission to create clan requests."
        )

    if channel.id not in CLANREQUEST_ALLOWED_CHANNELS:
        allowed_channels_str = ", ".join(f"<#{cid}>" for cid in CLANREQUEST_ALLOWED_CHANNELS)
        return await ctx.send(
            f"🚫 This command can only be used in the following channels:\n{allowed_channels_str}"
        )

    embed = discord.Embed(
        title="📌 Clan Request Setup",
        description=(
            "Please choose a request type from the dropdown.\n\n"
            "Available types:\n"
            "- Bit Frame\n"
            "- Bit Frame + Dye\n"
            "- Bit Swap\n"
            "- Rental\n"
            "- Work Permit\n\n"
            "After choosing, you'll be asked for your **jobboard contribution** number.\n"
            "The final request will be posted in this channel."
        ),
        color=0xF1DBB6,
    )

    view = ClanRequestView(ctx.bot, ctx.author, channel.id)
    print("[clanrequest_command] Sending setup embed+view.")
    embed = add_embed_footer(embed)
    await ctx.send(embed=embed, view=view)


@commands.command(name="milestonereset")
async def milestonereset(ctx, target: discord.Member = None):
    """
    Reset all milestone claims for a specified user.
    Usage:
        !milestonereset @User
        !milestonereset 123456789012345678
        !milestonereset   (resets yourself)
    """

    WL_USER = {296181275344109568, 1370076515429253264}

    if ctx.author.id not in WL_USER:
        return await ctx.send("⛔ You do not have permission to use this command.")

    # ------------ Resolve target ------------

    if target is None:
        target = ctx.author


    if isinstance(target, str) and target.isdigit():
        member = ctx.guild.get_member(int(target))
        if member:
            target = member

    if isinstance(target, discord.User):
        guild_member = ctx.guild.get_member(target.id)
        if guild_member:
            target = guild_member

    if not isinstance(target, discord.Member):
        return await ctx.send("❌ Could not resolve target user.")

    print(f"[milestonereset] Requested by {ctx.author.id} to reset user {target.id}")

    global claim_history
    old_count = len(claim_history["claims"])
    print(f"[milestonereset] Current total claims: {old_count}")

    new_claims = [
        c for c in claim_history["claims"]
        if c.get("user_id") != target.id
    ]
    removed_count = old_count - len(new_claims)

    print(f"[milestonereset] Removing {removed_count} claims for user {target.id}")

    claim_history["claims"] = new_claims
    save_claim_history()

    if target.id in active_ticket_cache:
        print(f"[milestonereset] Clearing active tickets cache for user {target.id}")
        active_ticket_cache.pop(target.id, None)

    await ctx.send(
        f"🧹 Cleared **{removed_count}** milestone logs for {target.mention}.\n"
        "They can now claim milestones again from scratch."
    )

    print("[milestonereset] Reset complete.")


# ----------------------------
# Extension setup entrypoint
# ----------------------------

async def setup(bot: commands.Bot):
    print("[milestone/clanrequest] Setting up extension, adding commands...")
    bot.add_command(milestone_command)
    bot.add_command(clanrequest_command)
    bot.add_command(jobreward)
    bot.add_command(milestonereset)

    print("[milestone/clanrequest] Setup complete.")
