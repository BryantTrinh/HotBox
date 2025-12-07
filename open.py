# -------------------------------
# Worked command
# -------------------------------
@bot.command(name="worked")
async def worked_command(ctx, days: int = 30):
    ALLOWED_USERS = {1370076515429253264, 296181275344109568}
    WORK_CHANNEL_ID = 1435858707782307933
    TARGET_PHRASE = "your workers have finished their tasks"

    if ctx.author.id not in ALLOWED_USERS:
        return await ctx.send("❌ You do not have permission to use this command.")

    if days < 1 or days > 90:
        return await ctx.send("❌ Please provide a number of days between 1 and 90.")

    channel = ctx.guild.get_channel(WORK_CHANNEL_ID)
    if not channel:
        return await ctx.send("❌ Could not find the target work channel.")

    since = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    user_counts = {}
    total_scanned = 0
    total_matched = 0
    batch_index = 1
    progress_bar_length = 20
    last_message = None

    while True:
        scanned = 0
        matched = 0

        progress_embed = discord.Embed(
            title=f"🏗️ Scanning Batch #{batch_index}...",
            description=f"⏳ Scanning up to 5000 messages from the past {days} days...\nScanned: 0\nMatches: 0",
            color=discord.Color.orange(),
        )
        progress_msg = await ctx.send(embed=progress_embed)

        async def heartbeat():
            try:
                while True:
                    filled = min(progress_bar_length, (scanned % 1000) // 50)
                    bar = "#" * filled + "-" * (progress_bar_length - filled)
                    progress_embed.description = (
                        f"⏳ Scanning Batch #{batch_index}...\n"
                        f"**Progress:** [{bar}] Scanned: {total_scanned + scanned} messages\n"
                        f"**Matches:** {total_matched + matched}"
                    )
                    await progress_msg.edit(embed=progress_embed)
                    await asyncio.sleep(5)
            except asyncio.CancelledError:
                return

        heartbeat_task = asyncio.create_task(heartbeat())

        batch_limit = 5000
        messages_in_batch = 0
        oldest_in_batch = None  # <-- FIXED

        async for message in channel.history(limit=batch_limit, before=last_message, oldest_first=False):
            messages_in_batch += 1
            scanned += 1
            total_scanned += 1

            # ✅ TRACK THE OLDEST MESSAGE IN THIS BATCH
            if oldest_in_batch is None or message.created_at < oldest_in_batch.created_at:
                oldest_in_batch = message

            if message.created_at < since:
                heartbeat_task.cancel()
                break

            if message.author.bot:
                for e in message.embeds:
                    desc = strip_markdown(e.description.lower() if e.description else "")
                    if TARGET_PHRASE in desc:
                        matched += 1
                        total_matched += 1
                        original_desc = e.description or ""

                        mentions = re.findall(MENTION_REGEX, original_desc)
                        for user_id in mentions:
                            uid = int(user_id)
                            user_counts[uid] = user_counts.get(uid, 0) + 1

                        if not mentions:
                            usernames = re.findall(USERNAME_REGEX, original_desc)
                            for username in usernames:
                                member = discord.utils.find(
                                    lambda m: m.name.lower() == username.lower(), ctx.guild.members
                                )
                                if member:
                                    user_counts[member.id] = user_counts.get(member.id, 0) + 1

        heartbeat_task.cancel()

        # ✅ FIXED PAGINATION — ADVANCE TO NEXT OLDER MESSAGE
        last_message = oldest_in_batch

        batch_summary = discord.Embed(
            title=f"✅ Completed Batch #{batch_index}",
            description=f"Scanned **{scanned}** messages, found **{matched}** completions.",
            color=discord.Color.green() if matched else discord.Color.red(),
        )
        await progress_msg.edit(embed=batch_summary)

        # STOP if fewer than batch_limit messages OR reached time limit
        if messages_in_batch < batch_limit or (last_message and last_message.created_at < since):
            break

        batch_index += 1
        await ctx.send(f"📦 Continuing to Batch #{batch_index}...")
        await asyncio.sleep(1)

    if not total_matched:
        embed = discord.Embed(
            title="📭 No Work Completions Found",
            description=f"Scanned **{total_scanned}** messages in the past {days} days.\nNo matches found.",
            color=discord.Color.red(),
        )
        return await ctx.send(embed=embed)

    sorted_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)

    leaderboard_data = []
    leaderboard_preview_lines = []

    for i, (user_id, count) in enumerate(sorted_users, start=1):
        member = ctx.guild.get_member(user_id)
        username = member.display_name if member else f"<@{user_id}>"
        leaderboard_data.append((username, user_id, count))
        if i <= 10:
            leaderboard_preview_lines.append(f"**#{i}** {username} — {count} times")

    preview_text = "\n".join(leaderboard_preview_lines) or "No valid users found."

    final_embed = discord.Embed(
        title=f"🏆 Work Leaderboard (Past {days} Days)",
        description=(
            f"✅ Scan complete!\nScanned **{total_scanned}** messages.\n"
            f"Found **{total_matched}** successful completions.\n\n{preview_text}"
        ),
        color=discord.Color.green(),
    )

    view = LeaderboardView(leaderboard_data)
    await ctx.send(embed=final_embed, view=view)








    @bot.command(name="worked")
async def worked_command(ctx, days: int = 30):
    ALLOWED_USERS = {1370076515429253264, 296181275344109568}
    WORK_CHANNEL_ID = 1435858707782307933
    TARGET_PHRASE = "your workers have finished their tasks"

    if ctx.author.id not in ALLOWED_USERS:
        return await ctx.send("❌ You do not have permission to use this command.")

    if days < 1 or days > 90:
        return await ctx.send("❌ Please provide a number of days between 1 and 90.")

    channel = ctx.guild.get_channel(WORK_CHANNEL_ID)
    if not channel:
        return await ctx.send("❌ Could not find the target work channel.")

    since = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    user_counts = {}
    total_scanned = 0
    total_matched = 0
    progress_bar_length = 20

    progress_embed = discord.Embed(
        title=f"🏗️ Scanning Messages...",
        description=f"⏳ Scanning messages from the past {days} days...\nScanned: 0\nMatches: 0",
        color=discord.Color.orange(),
    )
    progress_msg = await ctx.send(embed=progress_embed)

    scanned = 0
    matched = 0

    async def heartbeat():
        try:
            while True:
                filled = min(progress_bar_length, (scanned % 1000) // 50)
                bar = "#" * filled + "-" * (progress_bar_length - filled)
                progress_embed.description = (
                    f"⏳ Scanning messages...\n"
                    f"**Progress:** [{bar}] Scanned: {total_scanned + scanned} messages\n"
                    f"**Matches:** {total_matched + matched}"
                )
                await progress_msg.edit(embed=progress_embed)
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            return

    heartbeat_task = asyncio.create_task(heartbeat())

    async for message in channel.history(limit=None, oldest_first=False):
        scanned += 1
        total_scanned += 1

        if message.created_at < since:
            heartbeat_task.cancel()
            break

        if message.author.bot:
            for e in message.embeds:
                desc = strip_markdown(e.description.lower() if e.description else "")
                if TARGET_PHRASE in desc:
                    matched += 1
                    total_matched += 1
                    original_desc = e.description or ""

                    mentions = re.findall(MENTION_REGEX, original_desc)
                    for user_id in mentions:
                        uid = int(user_id)
                        user_counts[uid] = user_counts.get(uid, 0) + 1

                    if not mentions:
                        usernames = re.findall(USERNAME_REGEX, original_desc)
                        for username in usernames:
                            member = discord.utils.find(
                                lambda m: m.name.lower() == username.lower(), ctx.guild.members
                            )
                            if member:
                                user_counts[member.id] = user_counts.get(member.id, 0) + 1

    heartbeat_task.cancel()

    if not total_matched:
        embed = discord.Embed(
            title="📭 No Work Completions Found",
            description=f"Scanned **{total_scanned}** messages in the past {days} days.\nNo matches found.",
            color=discord.Color.red(),
        )
        return await ctx.send(embed=embed)

    sorted_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)

    leaderboard_data = []
    leaderboard_preview_lines = []

    for i, (user_id, count) in enumerate(sorted_users, start=1):
        member = ctx.guild.get_member(user_id)
        username = member.display_name if member else f"<@{user_id}>"
        leaderboard_data.append((username, user_id, count))
        if i <= 10:
            leaderboard_preview_lines.append(f"**#{i}** {username} — {count} times")

    preview_text = "\n".join(leaderboard_preview_lines) or "No valid users found."

    final_embed = discord.Embed(
        title=f"🏆 Work Leaderboard (Past {days} Days)",
        description=(
            f"✅ Scan complete!\nScanned **{total_scanned}** messages.\n"
            f"Found **{total_matched}** successful completions.\n\n{preview_text}"
        ),
        color=discord.Color.green(),
    )

    view = LeaderboardView(leaderboard_data)
    await ctx.send(embed=final_embed, view=view)