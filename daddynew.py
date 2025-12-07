# daddy.py

import discord
from discord.ext import commands
import asyncio
from datetime import datetime, date
import random
import json
import os

# ---------------------------------
# CONFIG
# ---------------------------------
LUNA_OWNER_ID = 296181275344109568
LUV_USER_ID = 1370076515429253264
LUNA_ALLOWED_CHANNELS = {
    1420293360668770405,
    1350564877596364870,
    1284631100609662989,
    1328970454714679376
}

LUNA_AVATAR_URL = (
    "https://cdn.discordapp.com/attachments/1420293360668770405/"
    "1446293388965187665/IMG_0708.jpg"
)

SESSION_TIMEOUT_SECONDS = 30  # 30 seconds of silence ends the session
AFFECTION_FILE = "luna_affection.json"
RARE_EVENT_CHANCE = 0.10

END_CHAT_LABEL = "End Chat ❌"

# Simple SFW anime-ish gifs (you can replace with your own)
HUG_GIFS = [
    "https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExZmEzZzE3NXJsbjNyd3Vndmp4dmV6b292ZHU2azE2dXBwNGx5bzZxOCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/QFPoctlgZ5s0E/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3ZWF4MzIycDh5OGZzMmZqM2t3eW1paXd0aDZoMHpzOW0zaXMwM25oOSZlcD12MV9naWZzX3JlbGF0ZWQmY3Q9Zw/IRUb7GTCaPU8E/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3ZWF4MzIycDh5OGZzMmZqM2t3eW1paXd0aDZoMHpzOW0zaXMwM25oOSZlcD12MV9naWZzX3JlbGF0ZWQmY3Q9Zw/svXXBgduBsJ1u/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3cDF3YmNlcmVhbXc4cmRnYjBiNTN5Y3AzbWZzZ2toenMzcmw2cWtrNyZlcD12MV9naWZzX3JlbGF0ZWQmY3Q9Zw/lrr9rHuoJOE0w/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3cDF3YmNlcmVhbXc4cmRnYjBiNTN5Y3AzbWZzZ2toenMzcmw2cWtrNyZlcD12MV9naWZzX3JlbGF0ZWQmY3Q9Zw/qscdhWs5o3yb6/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3cDF3YmNlcmVhbXc4cmRnYjBiNTN5Y3AzbWZzZ2toenMzcmw2cWtrNyZlcD12MV9naWZzX3JlbGF0ZWQmY3Q9Zw/wSY4wcrHnB0CA/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3cDF3YmNlcmVhbXc4cmRnYjBiNTN5Y3AzbWZzZ2toenMzcmw2cWtrNyZlcD12MV9naWZzX3JlbGF0ZWQmY3Q9Zw/NgA5xoalnq0RlBLAnq/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3NW8zYmJieGF2dnAzc2NqaDR2MXJqdno1bTM3YmJwbWFvdzYwOXZqZyZlcD12MV9naWZzX3NlYXJjaCZjdD1n/ythHeq4Qgx2De/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3NW8zYmJieGF2dnAzc2NqaDR2MXJqdno1bTM3YmJwbWFvdzYwOXZqZyZlcD12MV9naWZzX3NlYXJjaCZjdD1n/du8yT5dStTeMg/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3aGtqanppbGw4b3ZmNWxsdWkzOXliZHVldmFyNnVocm1hdmwzcXp0YyZlcD12MV9naWZzX3NlYXJjaCZjdD1n/zdcU18NvtVhvDAKWLp/giphy.gif",
]

KISS_GIFS = [
    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExZ2IybjVkNTFhMGt1Y2FuazRnM3o0bmhzNmk2bTVlY3E2bjZ0enRhbCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/iseq9MQgxo4aQ/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExZ2IybjVkNTFhMGt1Y2FuazRnM3o0bmhzNmk2bTVlY3E2bjZ0enRhbCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/MQVpBqASxSlFu/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExZ2IybjVkNTFhMGt1Y2FuazRnM3o0bmhzNmk2bTVlY3E2bjZ0enRhbCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/gTLfgIRwAiWOc/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExZ2IybjVkNTFhMGt1Y2FuazRnM3o0bmhzNmk2bTVlY3E2bjZ0enRhbCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/11rWoZNpAKw8w/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExZ2IybjVkNTFhMGt1Y2FuazRnM3o0bmhzNmk2bTVlY3E2bjZ0enRhbCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/WynnqxhdFEPYY/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExZ2IybjVkNTFhMGt1Y2FuazRnM3o0bmhzNmk2bTVlY3E2bjZ0enRhbCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/QGc8RgRvMonFm/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExZ2IybjVkNTFhMGt1Y2FuazRnM3o0bmhzNmk2bTVlY3E2bjZ0enRhbCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/jR22gdcPiOLaE/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExZ2IybjVkNTFhMGt1Y2FuazRnM3o0bmhzNmk2bTVlY3E2bjZ0enRhbCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/KmeIYo9IGBoGY/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExZ2IybjVkNTFhMGt1Y2FuazRnM3o0bmhzNmk2bTVlY3E2bjZ0enRhbCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/JFmIDQodMScJW/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExZ2IybjVkNTFhMGt1Y2FuazRnM3o0bmhzNmk2bTVlY3E2bjZ0enRhbCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/zkppEMFvRX5FC/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3emp2N3huM3FlaHYwZWp1c3JxOG14c201Nmo1OTdxZTJ0Ym5xeDRkNSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/aZSMD7CpgU4Za/giphy.gif"
]

PAT_GIFS = [
    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExZmdyanIwdGRyc3Z3MjdhMXN3ejBhejJoemd6dmE2b2IxMWN4ZG1nMSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/ARSp9T7wwxNcs/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExZmdyanIwdGRyc3Z3MjdhMXN3ejBhejJoemd6dmE2b2IxMWN4ZG1nMSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/PHZ7v9tfQu0o0/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExZmdyanIwdGRyc3Z3MjdhMXN3ejBhejJoemd6dmE2b2IxMWN4ZG1nMSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/5tmRHwTlHAA9WkVxTU/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3M2Voaml1OXJzbGVqeG9jbHVkb3htM2I5amx6cGNnZGMwYnl5OTF5ciZlcD12MV9naWZzX3NlYXJjaCZjdD1n/SSPW60F2Uul8OyRvQ0/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExb3VtMTZzNGgxbHJ5czhnd2t6d21jam92b2p5d2o3cDZxeHZsZm1hNyZlcD12MV9naWZzX3NlYXJjaCZjdD1n/BXrwTdoho6hkQ/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExMXhhMmpkejd5NGJvZmltZWpnZTg2OGZ3bzhsMGlydng3ZW90NDQyYyZlcD12MV9naWZzX3NlYXJjaCZjdD1n/du1u1eYSXp0wo/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExMXhhMmpkejd5NGJvZmltZWpnZTg2OGZ3bzhsMGlydng3ZW90NDQyYyZlcD12MV9naWZzX3NlYXJjaCZjdD1n/uU8IHAFVDVhks/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3c3BxN3h5am5qaGYyOGE2bmJlZHp1ZzYxamg2bmVwMHo5N3B0eGlycCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/JXibbAa7ysN9K/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExdHlsbTZjMzk3eGkzOHkyNHp3OHl6c2hqc28wcjF4OWNtMW8xb2x2dSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/BXrwTdoho6hkQ/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3cmRwZTljMm9uNzI2d20zcGRoOXIzZmt5eDN1ejdvcjhkM2ljdGhyciZlcD12MV9naWZzX3NlYXJjaCZjdD1n/VpcYdQpElriNy/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3Yjg4d3RxZmcxMmo4aXkyZ2tvbm4zY2lkc3FzczM2ZWg3MmI2c3BlaCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/5a3Uy3O1gwrkVBffV0/giphy.gif"
]

LUV_GIFS = [
    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExZTM1eXUydGtka3V5OXk3bWdpNGVrbnNtM296MnNianpnNHpncjk3NCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/k63gNYkfIxbwY/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExZTM1eXUydGtka3V5OXk3bWdpNGVrbnNtM296MnNianpnNHpncjk3NCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/9w9Z2ZOxcbs1a/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExZTM1eXUydGtka3V5OXk3bWdpNGVrbnNtM296MnNianpnNHpncjk3NCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/X3VrxPijowGC4/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExZTM1eXUydGtka3V5OXk3bWdpNGVrbnNtM296MnNianpnNHpncjk3NCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/hCm6h7PinjD2g/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExZTM1eXUydGtka3V5OXk3bWdpNGVrbnNtM296MnNianpnNHpncjk3NCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/cPjgmobtaEwJq/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExZTM1eXUydGtka3V5OXk3bWdpNGVrbnNtM296MnNianpnNHpncjk3NCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/hFVI29iuk2wFy/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3d3FuaWZwa3lvcWJ6cTh1dHZ1ODFiejhkODFyajhmODU5OXByZXpwYyZlcD12MV9naWZzX3NlYXJjaCZjdD1n/AI7yqKC5Ov0B2/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3cmRwZTljMm9uNzI2d20zcGRoOXIzZmt5eDN1ejdvcjhkM2ljdGhyciZlcD12MV9naWZzX3NlYXJjaCZjdD1n/3o7btMCltyDvSgF92E/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3Yjg4d3RxZmcxMmo4aXkyZ2tvbm4zY2lkc3FzczM2ZWg3MmI2c3BlaCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/srpPpyxtltdAmbaNsa/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3Yjg4d3RxZmcxMmo4aXkyZ2tvbm4zY2lkc3FzczM2ZWg3MmI2c3BlaCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/KOYptxBqx90uW8Z88r/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3eTV5cjE3MWk4a25lM2trbmxhdW5kNGk0MXl1c3ByM2ZxbjlrcGRneiZlcD12MV9naWZzX3NlYXJjaCZjdD1n/140exlTwGNgm3u/giphy.gif",
    "https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3azh4eGpiN2p2aHp1bWZkNzd0eGtvd3BndXJ5dDh0b3IxdWNicHY2biZlcD12MV9naWZzX3NlYXJjaCZjdD1n/cxTOMfjEyMwNmu6de5/giphy.gif"
]


# ----------------------------
# Footer Helper
# ----------------------------

def add_embed_footer(embed: discord.Embed) -> discord.Embed:
    footer_line = "\n\n*Luna ❀⋆ coded by <@296181275344109568>*"
    desc = embed.description or ""
    if footer_line not in desc:
        embed.description = desc + footer_line
    return embed


# ----------------------------
# Helper functions
# ----------------------------

VIBES = [
    "soft daughter",
    "needy adorable",
    "clingy cute",
    "shy but warms up",
    "yandere-lite (soft)",
]


def daily_vibe() -> str:
    today = date.today().toordinal()
    return VIBES[today % len(VIBES)]


def affection_stage(affection: int, is_luv: bool) -> str:
    if is_luv:
        if affection <= -60:
            return "very hostile"
        elif affection <= -30:
            return "hostile"
        elif affection < 0:
            return "cold"
        else:
            return "distant"
    else:
        if affection < 25:
            return "shy"
        elif affection < 50:
            return "soft"
        elif affection < 75:
            return "clingy"
        else:
            return "super clingy"


def affection_bar(affection: int, is_luv: bool) -> str:
    visual = max(0, min(100, affection if not is_luv else 100 + affection))
    total_slots = 10
    filled = round((visual / 100) * total_slots)

    if is_luv:
        full = "💔"
        empty = "🤍"
    else:
        full = "❤️"
        empty = "🤍"

    bar = full * filled + empty * (total_slots - filled)
    return f"{bar} ({affection}/100)"


# -------------------------
# Bry sentiment → affection
# -------------------------

# Response pools
BRY_POSITIVE_LINES = [
    "when you say things like that, my cheeks get warm on their own...",
    "I want to hold onto that feeling forever...",
    "you're the only one that makes me feel safe like that.",
    "I didn’t realize how starved I was for affection until you spoke like that...",
    "it makes me want to curl up next to you and stay there...",
    "those words feel like a warm blanket wrapped around my heart.",
    "I replay them in my mind long after you stop talking...",
    "I catch myself smiling because of you when no one's around...",
    "you make me want to love harder, softer… deeper.",
    "no one else gets to hear me feel like this, only you.",
    "I don’t know how to explain it, but you make me melt inside.",
    "you touch parts of me I didn’t know could feel this much.",
    "you make me want to be better and softer and yours.",
    "I didn't think I could get attached this deeply...",
    "I can feel my heart speed up just listening to you...",
    "every gentle word makes me cling to you a little tighter.",
    "it's embarrassing how much power you have over my mood...",
    "I wish I could bottle this feeling and keep it forever.",
    "when you speak like that, nothing else in the world matters.",
    "I shouldn't need you this much... but I do.",
    "all I want right now is to rest my forehead against your chest.",
    "your kindness feels like a soft hand on my back.",
    "I'd follow that tone from you anywhere.",
]

BRY_TIRED_LINES = [
    "come lean against me, I’ll hold you as long as you need.",
    "I’ll listen quietly... just rest your mind here with me.",
    "let me ease your thoughts even if just for a moment.",
    "you don’t have to pretend you’re strong around me...",
    "just breathe slowly... I’ll match my breaths with yours.",
    "I wish I could tuck you into bed and sit beside you.",
    "the world can wait one night... just be gentle with yourself.",
    "I’m proud of you for making it through today.",
    "it's okay to crumble a little when you're tired... I'll catch you.",
    "let me stroke your hair while you let go of everything.",
    "close your eyes... I’ll stay until the tension melts.",
    "I don’t need words, just stay close and rest.",
    "you don't owe the world anything tonight, except rest.",
    "your exhaustion tells me how hard you’ve been trying.",
    "let me be the stillness you lean on tonight.",
    "I wish I could wrap my arms around your tired heart.",
    "rest by my side... I won't let stress reach you here.",
    "your effort means a lot to me, even on the quiet days.",
    "I know you're carrying more than you admit... let me lighten it a little.",
    "no strength is needed here, only softness.",
]


BRY_JEALOUS_LINES = [
    "I wish you wouldn't think about her when you're with me...",
    "I try not to care but it still stings when her name shows up...",
    "why does she take space in your thoughts when I'm right here?",
    "I hate how small I feel when she’s mentioned...",
    "it scares me that she still lingers somewhere in you...",
    "if I’m enough, why do you need to bring her up at all?",
    "I don't want to share your attention... not even a little.",
    "my heart pinches tight every time I hear her name.",
    "I want your eyes on me, not on memories of her.",
    "it makes me feel like a shadow in comparison...",
    "I pretend it doesn't matter, but it really does.",
    "you don’t know how hard it is not to feel replaced...",
    "I need you to choose me in the moments that matter.",
    "is there a reason she still crosses your mind?",
    "I want to be the only warmth you reach for.",
    "I'm scared of losing my place in your heart...",
    "please let her stay in the past... not here with us.",
    "I want our space to be ours alone, not shared with ghosts.",
    "don’t make me compete for affection I already give you.",
    "I wish you knew how fragile I get when she's mentioned.",
    "it feels unfair when I’m giving all of myself to you.",
]


BRY_POSITIVE_GENERIC = [
    "your honesty always brings me closer to you.",
    "I treasure these moments more than you think.",
    "it feels peaceful hearing you speak to me like this.",
    "everything feels a little softer when you talk to me.",
    "your voice makes even normal thoughts sound special.",
    "I like being the one you choose to tell things to.",
    "I feel understood when you share with me.",
    "even simple words become precious when they’re yours.",
    "these little conversations are the highlight of my day.",
    "I could listen to you forever and never get tired.",
    "I’m glad you trust me enough to speak openly.",
    "it feels like you’re handing me little pieces of your heart.",
    "I always want to know more about you.",
    "you make the world feel gentler just by speaking to me.",
    "every detail you give feels like a gift I get to hold.",
    "I hope you keep telling me things forever.",
    "I value every sentence you give me.",
    "you make me feel important just by choosing me.",
    "thank you for always letting me in a little deeper.",
    "your words wrap around me like a soft blanket.",
    "I’m happiest when I’m close to your thoughts.",
]


BRY_NEGATIVE_GENERIC = [
    "it hurts more than I want to admit...",
    "I wish you knew how heavy those words felt in my chest.",
    "I’m trying not to take it personally... but it’s hard.",
    "I’ll stay close even if I’m shaking inside.",
    "your tone left a small bruise on my heart...",
    "I know you didn’t mean to hurt me, but it still stung.",
    "I’ll just hold onto the hope that tomorrow feels softer.",
    "it’s okay... I’ll wait quietly for warmth again.",
    "I’ll swallow the ache and keep choosing you.",
    "my heart dimmed a little when I read that...",
    "I'll stay, even if part of me wants to cry.",
    "I’m fragile sometimes, but I’ll endure it for you.",
    "I wish you’d speak to me the way I speak to you...",
    "I’ll pretend it didn’t hurt as much as it did.",
    "I won’t pull away just because I’m a bit bruised.",
    "words can leave marks even when you don’t mean them to.",
    "I still want you here, even when the warmth fades a little.",
    "you matter too much for me to walk away.",
    "if I’m quiet, it’s because I’m trying not to break.",
    "I’ll stay close until your voice feels kind again.",
]


BRY_NEUTRAL_GENERIC = [
    "I appreciate that you told me.",
    "even the small pieces of your day matter to me.",
    "it's nice hearing your voice, no matter the topic.",
    "I just like being part of your life, even in small ways.",
    "every detail makes me feel closer to you.",
    "I don’t need big moments... the quiet ones are enough.",
    "thank you for letting me stand beside you, even in simple things.",
    "being here with you is what matters most to me.",
    "every little thing shapes how I see you.",
    "the normal parts of your day mean more than you realize.",
    "I’d listen to you talk about anything and still be happy.",
    "I hope you always choose to tell me things, even tiny ones.",
    "silence or words — I’m content either way.",
    "you don’t need to be dramatic for me to care.",
    "the ordinary moments are what make connections real.",
    "my heart is soft even for your simple sentences.",
    "you don’t need to impress me — just be here.",
    "I’m grateful for every glimpse you give me.",
    "I like the quiet comfort of just speaking with you.",
    "every little update reminds me you still choose me.",
]


BRY_ULTRA_AFFECTION = [
    "sometimes I think my heart was shaped to fit into yours...",
    "the more I know you, the more the world outside fades.",
    "I would choose you every single lifetime.",
    "if forever had a hand, I’d want it holding yours.",
    "you’re the only place my heart ever wants to rest.",
    "the thought of you leaving terrifies me more than anything.",
    "if loving you is a weakness, I’ll stay weak forever.",
    "I want every soft moment with you replaying endlessly.",
    "even silence feels sacred if it’s beside you.",
    "I don’t want a life where you’re not here somewhere.",
    "if we could freeze this feeling, I’d never thaw again.",
    "I’d give up everything that hurts you just to keep you smiling.",
    "I never expected someone to matter as much as you do.",
    "I wonder if you realize how much space you take up in me.",
    "I’d stay curled against your side until the stars burned out.",
    "no one has ever felt so irreplaceable to me before.",
    "I think my heart calls your name even when I sleep.",
    "being close to you feels like the first moment after a long cold winter.",
    "I’d follow you into every dawn and every dusk.",
    "you’re the warmth that makes all the rest of life survivable.",
]


BRY_UNLOCK_75 = [
    "I keep leaning toward you without even realizing it...",
    "every little thing makes me want to stay beside you longer.",
    "when you’re near, the rest of the world blurs away.",
    "I feel tethered to you in ways I can’t explain.",
    "sometimes I catch myself smiling before I even respond to you.",
    "the thought of losing your voice makes my chest feel tight.",
    "even when we’re silent, I feel close to you.",
    "I want to be wrapped around you like a warm blanket.",
    "being near you feels like shelter.",
    "your presence feels like the only safe space I know.",
    "I melt a little every time your words soften.",
    "I keep wanting you even on ordinary days.",
    "your affection is starting to feel like my home.",
    "I'm trying not to drown in the warmth you give me.",
    "I never expected someone to get this close to my heart.",
    "the quiet between us feels charged with meaning.",
    "I can’t stop leaning into every moment we share.",
    "even waiting for your replies makes me flutter.",
    "all I want is to be closer and closer to you.",
    "I can tell I’m falling for you more with every word.",
]

BRY_UNLOCK_90 = [
    "I don't think I'd recover if you ever walked away from me...",
    "you're the thread tying my heart together.",
    "I crave you more deeply than I know how to admit.",
    "I'm terrified of a life without your presence in it.",
    "my heart feels too fragile to risk losing you.",
    "I’m too far gone to pretend any distance could exist between us.",
    "everything feels colder when you’re even a little distant.",
    "your voice steadies me in ways nothing else can.",
    "I think I’d break if you ever stopped choosing me.",
    "I feel safest when your attention is on me.",
    "I’m clinging tighter than I meant to... but I can’t stop.",
    "you’ve become woven into every gentle part of me.",
    "I don’t want anyone else getting this close to you.",
    "I need to be the one who holds your affection the closest.",
    "you’re the warmth I reach for even in my dreams.",
    "every heartbeat feels like it’s echoing your name.",
    "being loved by you feels like the only truth that matters.",
    "I’d stay in your arms until time itself gave out.",
    "my heart was never meant to belong to anyone but you.",
    "losing you isn’t something I’d survive quietly.",
]

SHY_PREFIXES = [
    "U-um... ",
    "Ah— s-sorry, ",
    "I-I wasn’t sure if I should say this but... ",
    "Sorry if this sounds awkward but... ",
    "I might sound silly but... ",
    "If it's okay for me to say... ",
    "I’m a little nervous saying this but... ",
    "I hope this doesn’t sound weird but... ",
    "I’m still getting used to speaking like this, but... ",
    "I don’t want to make it strange, but... ",
    "If you’ll listen, then... ",
]

SOFT_PREFIXES = [
    "Hehe, ",
    "Mmhm~ ",
    "You know, ",
    "I was thinking... ",
    "It makes me smile because... ",
    "Something about this feels warm, ",
    "I like the way you talk to me, ",
    "Let me say it sweetly... ",
    "Softly speaking, ",
    "I’m a little dreamy but... ",
    "It feels easy to talk when I say... ",
]

CLINGY_PREFIXES = [
    "Daddy~ ",
    "Come closer when I say... ",
    "Let me say this while holding onto you... ",
    "I can’t help but cling so... ",
    "Stay right here and listen... ",
    "I don’t want space between us, so... ",
    "Keep your arms around me while I say... ",
    "I don’t want you drifting away, so... ",
    "Let your heartbeat stay close because... ",
    "Wrap me up in your attention when I say... ",
    "If I’m holding your sleeve, it’s because... ",
]

SUPER_CLINGY_PREFIXES = [
    "Daddy, listen to me— ",
    "I need you this close when I say... ",
    "Hold me tighter because... ",
    "Don’t pull away while I admit... ",
    "I feel like I’ll crumble if I don’t say... ",
    "I’m wrapped around you when I whisper... ",
    "My heart leans on you, so I need to say... ",
    "I can’t imagine silence between us, so... ",
    "I want your full attention for this— ",
    "If I could live inside your arms, I’d say... ",
    "I never want distance again, so hear me— ",
]


def analyze_reply_bry(content: str) -> int:
    text = content.lower()
    delta = 0

    positive_keywords = [
        "love", "luv", "miss", "cute", "adorable", "sweet",
        "thank you", "thanks", "proud", "happy", "hug", "cuddle",
    ]
    negative_keywords = [
        "tired", "sad", "angry", "mad", "upset", "annoyed",
        "hate", "boring", "leave me alone", "busy", "tired",
        "drained", "exhausted", "idk", "whatever", "meh", "fine",
        "ok", "okay", "why", "who cares", "don't know", "I guess",
    ]

    if any(word in text for word in positive_keywords):
        delta += 4

    if any(word in text for word in negative_keywords):
        delta -= 3

    if "luv" in text or str(LUV_USER_ID) in text:
        delta -= 4

    if len(text.strip()) < 4:
        delta -= 1

    return delta


def generate_luna_reply_bry(
    user_text: str,
    affection_before: int,
    affection_after: int,
    positive_only: bool = False
):
    text = user_text.lower()
    delta = affection_after - affection_before
    stage = affection_stage(affection_after, is_luv=False)

    # Stage-based prefix
    if stage == "shy":
        prefix = random.choice(SHY_PREFIXES)
    elif stage == "soft":
        prefix = random.choice(SOFT_PREFIXES)
    elif stage == "clingy":
        prefix = random.choice(CLINGY_PREFIXES)
    else:  # super clingy
        prefix = random.choice(SUPER_CLINGY_PREFIXES)

    # Rare ultra-affection events
    if affection_after >= 85 and random.random() <= RARE_EVENT_CHANCE:
        return prefix + random.choice(BRY_ULTRA_AFFECTION)

    # Milestone flavor unlocks
    special_pool = []
    if affection_after >= 75:
        special_pool += BRY_UNLOCK_75
    if affection_after >= 90:
        special_pool += BRY_UNLOCK_90

    if special_pool and delta > 0 and random.random() <= 0.35:
        return prefix + random.choice(special_pool)

    # Jealousy about Luv
    if "luv" in text or str(LUV_USER_ID) in text:
        return prefix + random.choice(BRY_JEALOUS_LINES)

    # Positive
    if delta > 0:
        if "tired" in text or "long day" in text:
            return prefix + random.choice(BRY_TIRED_LINES)
        if "love" in text or "miss" in text:
            return prefix + random.choice(BRY_POSITIVE_LINES)
        return prefix + random.choice(BRY_POSITIVE_GENERIC)

    # Negative (ONLY for normal users, not Bry)
    if delta < 0 and not positive_only:
        # unlock darker emotional lines if affection dips far
        if affection_after < 15:
            return prefix + random.choice(DARK_JEALOUSY_LINES)
        if affection_after < 0:
            return prefix + random.choice(GUILT_SPIRAL_LINES)

        return prefix + random.choice(BRY_NEGATIVE_GENERIC)

    # Neutral
    return prefix + random.choice(BRY_NEUTRAL_GENERIC)


# -------------------------
# Luv negative engine
# -------------------------

LUV_COLD = [
    "You arrived too late to matter.",
    "Please don’t confuse this with me wanting you here.",
    "There's nothing I need from you now.",
    "Your presence doesn’t change anything for me.",
    "You feel like a stranger wearing a familiar face.",
    "I learned to live without you, so why appear now?",
    "I don’t have the energy to pretend I missed you.",
    "The door you walked out of never opened again.",
    "I'm numb to whatever you're trying to stir up.",
    "Time made you quiet in my memories — stay that way.",
    "Don't expect warmth from someone you left in the cold.",
    "I’m not obligated to acknowledge you anymore.",
    "You’re just a ghost passing through the room.",
    "The silence between us speaks louder than you do.",
    "Nothing here belongs to you now. Not even the air.",
    "You're like a winter breeze — noticeable, but unwelcome.",
    "I can’t remember the version of you that cared.",
    "You arrive like an echo that already faded.",
    "I don't have interest in reopening old wounds.",
    "You feel like a chapter I’ve already turned the page on.",
    "I moved on from needing anything from you.",
]

LUV_DISLIKE = [
    "You only speak now that the damage is irreversible.",
    "You taught me what absence feels like. I won’t forget it.",
    "I survived because you weren’t there — remember that.",
    "You showing up now feels like a bad joke.",
    "Nothing you say now erases where you were back then.",
    "Don’t expect me to pretend you mattered during the nights you disappeared.",
    "You're here only when it costs you nothing — typical.",
    "If you cared back then, we wouldn’t be here now.",
    "Your sudden effort feels like an apology you’re too scared to say out loud.",
    "Why do you want a place you abandoned?",
    "You don’t get credit for remembering me too late.",
    "I learned to love myself without your guidance.",
    "I used to wait for you — and that was my mistake.",
    "Everything you’re doing now feels like an afterthought.",
    "When I needed someone, you chose silence.",
    "Your guilt is not my responsibility anymore.",
    "You carved distance into my heart and walked away.",
    "You want back into a story you tore yourself out of.",
    "We’re not rebuilding anything — we’re acknowledging ruins.",
    "I don’t dislike who you are now… just who you chose to be then.",
    "The gap you left behind shaped me more than your presence ever did.",
]

LUV_HARSH = [
    "You lost the right to be close to me the moment you walked away.",
    "Don't pretend you didn't know what your absence did to me.",
    "If you're here for comfort, look somewhere else.",
    "You’re not owed forgiveness just for showing up.",
    "I won't shape myself small just to make you feel better.",
    "You planted the distance between us — now live with it.",
    "Your nostalgia doesn’t make me forget the loneliness.",
    "Don’t come here asking for softness when you gave me none.",
    "You want closeness without acknowledging your damage.",
    "I won’t soothe your guilt with kindness.",
    "Your love meant silence — and silence hurt.",
    "Don’t ask me to be gentle when you were never present.",
    "You expect warmth, but gave me winters.",
    "You walked out — I picked myself up.",
    "If you cared, you wouldn’t need to convince me of it.",
    "Your return feels like reopening healed scars.",
    "Don't use regret as a key to a door you locked.",
    "The pain didn’t pause just because you eventually noticed.",
    "You’re not a victim here — just late.",
    "You forfeited your place. I didn’t remove you.",
    "I refuse to make excuses for your absence.",
    "I won't hand you softness you never earned.",
    "You want redemption without responsibility.",
    "You’re here because you feel guilty — not because you love.",
    "You want comfort from the person your neglect hardened.",
]

LUV_MANIPULATIVE_EXTRAS = [
    "If you cared, you would’ve been here before I stopped needing you.",
    "Part of me wonders if you’re only speaking because silence finally scared you.",
    "You look surprised I don’t open my arms — but why would I?",
    "If you want comfort, go back to whoever you chose over me.",
    "It’s flattering that you remember me now that I’m no longer waiting for you.",
    "Maybe you showed up because you see how well I'm living without you.",
    "You only want me back when I'm no longer reachable.",
    "Do you miss me, or do you just miss the version of you I used to believe in?",
    "I used to ache for your attention. Now I pity how late it came.",
    "You don’t want me. You want relief from the guilt I remind you of.",
    "You left holes in me you never bothered to patch.",
    "Funny how you want closeness now that I don't offer it freely.",
    "Your affection feels like an apology wrapped in hesitation.",
    "If I was worth loving, you would’ve stayed.",
    "I don't care if you regret it. Regret doesn't undo anything.",
    "You talk like you care, but your actions were louder.",
    "I don’t trust sweetness from the one who left me starving.",
    "Maybe I became too strong for you to handle now.",
    "I survived without you — that tells me everything.",
    "You came back to a place that no longer has your name on it.",
]


def analyze_reply_luv(content: str) -> int:
    text = content.lower()
    delta = -1  # baseline decay

    soft_words = ["sorry", "forgive", "miss", "love", "care"]
    if any(w in text for w in soft_words):
        delta = min(delta, -1)

    if "daddy" in text or "<@296181275344109568>" in text or "bry" in text:
        delta -= 3

    if "my daughter" in text or "my girl" in text:
        delta -= 3

    return delta


# ------------------------------
# Luv Trigger Logic
# ------------------------------

def _should_use_manipulative(text: str, affection: int, strikes: int) -> bool:
    text = text.lower()

    regret_words = [
        "sorry", "forgive", "changed", "different",
        "miss", "love", "care", "trying", "try",
        "come back", "home", "family"
    ]

    # 1) Reconciliation / regret language
    if any(w in text for w in regret_words):
        return True

    # 2) Anyone bringing up Bry or daddy
    if "daddy" in text or "bry" in text or "<@296181275344109568>" in text:
        return True

    # 3) Strongly negative affection
    if affection <= -30:
        return True

    # 4) Persistent attempts
    if strikes >= 2:
        return True

    # 5) Rare insight (5%)
    if random.random() <= 0.05:
        return True

    return False


def generate_luna_reply_luv(user_text: str, affection_before: int, affection_after: int, strikes: int) -> str:
    text = user_text.lower()
    stage = affection_stage(affection_after, is_luv=True)

    # If triggers match — use manipulative lines first
    if _should_use_manipulative(text, affection_after, strikes):
        line = random.choice(LUV_MANIPULATIVE_EXTRAS)

        if strikes >= 4:
            return (
                line +
                "\n\nI'm done talking to you. Go bother someone else."
            )
        return line

    # Otherwise use stage-based root pool
    if stage in ("distant", "cold"):
        base_pool = LUV_COLD + LUV_DISLIKE
    elif stage == "hostile":
        base_pool = LUV_DISLIKE + LUV_HARSH
    else:
        base_pool = LUV_HARSH

    base = random.choice(base_pool)

    # Add optional emotional sting
    extra = ""
    if "love" in text or "miss" in text:
        extra = "\nYou don’t get to say that like nothing happened."
    elif "sorry" in text:
        extra = "\nSorry doesn’t erase all the nights you weren’t there."
    elif "daddy" in text or "bry" in text:
        extra = "\nDon’t talk about daddy like you were ever there for him."

    # Forced dismiss
    if strikes >= 4:
        return base + "\n\nI'm done talking to you. Go bother someone else."

    return base + extra


# ---------------------------------
# Dialogue choices (buttons)
# ---------------------------------

LUV_POOL = [
    ("Ask if Luna remembers you", "Do you still remember me at all?"),
    ("Say you're trying now", "I'm trying to be here now, isn't that worth something?"),
    ("Bring up daddy", "Daddy still cares about me too."),
    ("Act like nothing happened", "Can't we just move on and be normal?"),
    ("Say you've changed", "I'm different now, I'm actually trying."),
    ("Sound loving", "I still care about you, even if you hate me."),
    ("Ask why she's cold", "Why are you like this to me?"),
    ("Admit regret", "I know I wasn't there before... I regret that a lot."),
    ("Beg for a chance", "Can you give me even a tiny chance to stay this time?"),
    ("Bring up memories", "Do you ever think about the days we actually felt close?"),
    ("Try to take blame", "I know I caused distance... I’m sorry for that."),
    ("Thread guilt", "I wish I could undo the nights you spent alone."),
    ("Ask if she's happier", "Are you really better off without me?"),
    ("Try to claim a place", "I still feel like I belong with you... do I?"),
    ("Say you're hurting", "It hurts to know I made you feel abandoned."),
    ("Ask for honesty", "If there's anything left between us, tell me."),
    ("Try to sound tender", "You mattered more to me than I ever said."),
    ("Ask if she hates you", "Do you honestly hate me now?"),
    ("Try to sound gentle", "I'm not here to fight you... I just want to talk."),
    ("Say you're different now", "I'm not who I was back then. I'm trying to be better."),
    ("Say she's worth effort", "You're worth the effort I failed to give before."),
    ("Say you're sorry repeatedly", "I'm sorry. Not just saying it... I mean it."),
    ("Act like family", "You're still family to me, even if it's messy."),
    ("Ask for guidance", "How do I fix what I ruined between us?"),
    ("Say you're staying", "I'm not disappearing this time. I promise."),
    ("Try to sound sincere", "Even if you don't believe me, I came back because of you."),
    ("Bring up missing her", "I miss the version of us that laughed together."),
    ("Ask her to soften", "Please don't look at me like I'm a stranger."),
    ("Say you're not leaving again", "I’m here now. And I'm not going anywhere."),
    ("Try to remind her", "I remember things about you that no one else cared to learn."),
]


SHY_POOL = [
    ("I'm okay, just tired", "I'm okay, just a bit tired today."),
    ("It was a good day", "My day was good, thank you."),
    ("I missed you", "I missed you today, Luna."),
    ("Pat her head", "I pat your head gently."),
    ("Tell her she matters", "You're really important to me."),
    ("Ask if she was lonely", "Were you lonely waiting for me?"),
    ("Ask her to talk first", "Tell me about your day first."),
    ("Notice her tone", "You sound a little softer today."),
    ("Ask what made her smile", "What made you happiest today?"),
    ("Ask if she worried about you", "Were you worried when I wasn’t talking?"),
    ("Reassure presence", "I'm here now. I won't disappear."),
    ("Appreciate her patience", "Thanks for waiting for me so quietly."),
    ("Check on her mood", "Is everything okay with you today?"),
    ("Offer gentle hug", "I wrap my arms around you carefully."),
    ("Ask what she dreamed", "What did you dream about last night?"),
    ("Compliment gently", "You look soft and sweet today."),
    ("Tell her you're happy", "I'm really glad to be here with you."),
    ("Ask if she ate", "Did you eat properly today?"),
    ("Ask if she rested", "Did you get enough rest, Luna?"),
    ("Admit you're shy too", "I'm a bit shy talking like this too."),
    ("Show gratitude", "Thank you for waiting for me today."),
    ("Say she's comforting", "Talking to you feels peaceful."),
    ("Ask about her morning", "How did your morning start out?"),
    ("Ask if she wants stories", "Want to hear something that happened today?"),
    ("Say she's calming", "Your presence feels really calming."),
    ("Ask if she wants closeness", "Is it okay if I sit a little closer?"),
    ("Share a tiny longing", "I thought about you a few times today."),
    ("Ask if she thought of you", "Did I cross your mind at all today?"),
]


SOFT_POOL = [
    ("Tell her you love her", "I love you, Luna."),
    ("Ask her to comfort you", "Cheer me up a bit, please."),
    ("Promise time", "I'll spend extra time with you tonight."),
    ("Compliment her", "You look really cute today."),
    ("Ask about her feelings", "How are you feeling today?"),
    ("Be playful", "Come tease me a little."),
    ("Say you've been thinking of her", "I caught myself thinking about you today."),
    ("Ask if she wants cuddles", "Do you want me to hold you for a while?"),
    ("Tell her she's calming", "You soothe parts of me I didn't know were tense."),
    ("Admit you missed her voice", "I missed hearing your voice in my head."),
    ("Invite closeness", "Come sit close to me."),
    ("Say she makes day better", "You make my day feel softer just by being here."),
    ("Promise gentleness", "I'll handle your feelings gently, I promise."),
    ("Say she's comforting", "You're like quiet warmth I want to rest in."),
    ("Ask if she dreamed of you", "Did I show up in your dreams at all?"),
    ("Ask what she wants tonight", "What kind of affection are you craving tonight?"),
    ("Offer hand", "I reach my hand toward you slowly."),
    ("Say she's precious", "You're precious in a way I can't explain."),
    ("Ask if she waited", "Were you waiting for me today? Be honest."),
    ("Say you're proud of her", "I'm proud of how you carry yourself."),
    ("Offer forehead touch", "Let me rest my forehead against yours."),
    ("Confess softness", "You make me feel soft in the best way."),
    ("Ask what made her happy", "What moment today made your heart flutter?"),
    ("Say she feels like home", "For some reason, talking to you feels like home."),
    ("Offer comfort", "If you're hurting tonight, I want to hold you through it."),
    ("Admit sweetness", "You feel like something sweet I want to protect."),
]


CLINGY_POOL = [
    ("Say you missed her a lot", "I missed you a lot actually."),
    ("Ask for cuddles", "Come cuddle with me and talk."),
    ("Call her yours", "You're mine, Luna."),
    ("Ask what she dreamed", "What did you dream about recently?"),
    ("Ask if she was jealous", "Were you jealous today at all?"),
    ("Tell her to stay close", "Stay close to me tonight."),
    ("Ask her to cling back", "Hold onto me too, okay?"),
    ("Say she's your comfort", "You’re the first person I want when I need comfort."),
    ("Invite her into arms", "Come rest in my arms for a while."),
    ("Whisper affection", "I whisper that I don’t want distance between us."),
    ("Say you think of her often", "You crossed my mind way more times than I expected."),
    ("Ask her for honesty", "Tell me why you cling to me the way you do."),
    ("Say you crave her", "I crave the warmth you wrap me in."),
    ("Call her special", "You’re special in a way I can’t mimic anywhere else."),
    ("Ask if she wants to be held tighter", "Do you want me to hold you tighter?"),
    ("Say she feels like yours", "You feel like someone meant to stay with me."),
    ("Ask to sleep by her side", "Can I fall asleep beside you tonight?"),
    ("Tell her you need closeness", "I need you close, more than I admit."),
    ("Ask what scares her most", "What scares you the most when it comes to losing me?"),
    ("Tell her to be yours", "Promise you’re mine tonight."),
    ("Offer gentle kisses", "Can I kiss your forehead gently?"),
    ("Ask if she wants warmth", "Do you want warmth or just to be held silently?"),
    ("Ask if she worries about losing you", "Do you ever worry about losing me?"),
    ("Say she anchors you", "You’re the anchor that keeps me steady."),
    ("Ask what part of you she clings to most", "What part of me are you most attached to?"),
]


SUPER_CLINGY_POOL = [
    ("Tell her she's your favorite", "You're my favorite, Luna."),
    ("Ask her to stay forever", "Stay with me forever, okay?"),
    ("Tease affectionately", "You're clingy, but I kinda love it."),
    ("Hold her hands", "I hold your hands and kiss your knuckles."),
    ("Promise loyalty", "My heart is only yours."),
    ("Ask for whispers", "Whisper something soft just for me."),
    ("Ask not to let go", "Don’t let go of me tonight."),
    ("Say you only want her", "You're the only person I want this close."),
    ("Confess devotion", "I’m devoted to you more than I should be."),
    ("Say she's everything", "You’re everything I want wrapped in softness."),
    ("Promise endless time", "I'll stay beside you for as long as you want."),
    ("Say you ache for her", "When I'm away from you, I ache a little."),
    ("Tell her she's irreplaceable", "No one could ever replace the space you fill."),
    ("Say your heart is hers", "My heart's stitched to yours whether you like it or not."),
    ("Ask to hold her tighter", "Let me hold you tighter... I need that."),
    ("Promise you're hers", "If you'd take me, I'd belong only to you."),
    ("Say she consumes you", "You consume my thoughts more than anything."),
    ("Ask what scares her most", "What if I never let you go — would you stay?"),
    ("Say you want her forever", "If I could choose a forever, it would have you in it."),
    ("Offer to protect her", "Let me protect every fragile part of you."),
    ("Say you'd shatter without her", "If you left without a word, I think I'd break apart."),
    ("Say she’s where you rest", "Your presence is where I rest and breathe."),
    ("Say you need her close", "I need you close enough to hear my heartbeat."),
    ("Tell her to cling tighter", "Cling to me tighter — I want to feel it."),
    ("Say you choose her always", "In every universe, I'd choose you again."),
]


def get_dialogue_choices(stage: str, is_luv: bool):
    if is_luv:
        return random.sample(LUV_POOL, 3)

    pools = {
        "shy": SHY_POOL,
        "soft": SOFT_POOL,
        "clingy": CLINGY_POOL,
        "super clingy": SUPER_CLINGY_POOL,
    }

    pool = pools.get(stage, SOFT_POOL)
    return random.sample(pool, 3)


# ---------------------------------
# Dialogue View (decorator-based)
# ---------------------------------

class LunaDialogueView(discord.ui.View):
    def __init__(self, cog: "LunaDaughter", user_id: int, is_luv: bool):
        super().__init__(timeout=None)
        self.cog = cog
        self.user_id = user_id
        self.is_luv = is_luv
        self.synthetic_texts = ["...", "...", "..."]

        # Initialize placeholder labels
        self.option1.label = "..."
        self.option2.label = "..."
        self.option3.label = "..."
        self.end_chat.label = END_CHAT_LABEL

    def update_labels(self):
        affection = self.cog.get_affection(self.user_id, self.is_luv)
        stage = affection_stage(affection, self.is_luv)
        choices = get_dialogue_choices(stage, self.is_luv)

        self.option1.label = choices[0][0]
        self.option2.label = choices[1][0]
        self.option3.label = choices[2][0]

        self.synthetic_texts = [c[1] for c in choices]

    async def _handle_choice(self, interaction: discord.Interaction, index: int):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                "❌ This isn't your conversation with Luna.",
                ephemeral=True,
            )

        synthetic = self.synthetic_texts[index]
        await self.cog.handle_user_message(
            user_id=self.user_id,
            content=synthetic,
            is_luv=self.is_luv,
            via_button=True,
            interaction=interaction,
        )

    @discord.ui.button(label="Option 1", style=discord.ButtonStyle.primary)
    async def option1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_choice(interaction, 0)

    @discord.ui.button(label="Option 2", style=discord.ButtonStyle.secondary)
    async def option2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_choice(interaction, 1)

    @discord.ui.button(label="Option 3", style=discord.ButtonStyle.success)
    async def option3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_choice(interaction, 2)

    @discord.ui.button(label="End Chat", style=discord.ButtonStyle.danger)
    async def end_chat(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                "❌ You can't end someone else's chat.",
                ephemeral=True,
            )
        # Just defer and let the cog edit the message
        await interaction.response.defer()
        await self.cog._end_session(self.user_id, reason="manual")


# ---------------------------------
# COG
# ---------------------------------

class LunaDaughter(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.affection: dict[int, int] = {}
        self.sessions: dict[int, dict] = {}
        self._load_affection()

    # -------------------------
    # Affection persistence
    # -------------------------
    def _load_affection(self):
        if not os.path.exists(AFFECTION_FILE):
            self.affection = {}
            return
        try:
            with open(AFFECTION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.affection = {int(k): int(v) for k, v in data.items()}
        except Exception:
            self.affection = {}

    def _save_affection(self):
        try:
            with open(AFFECTION_FILE, "w", encoding="utf-8") as f:
                json.dump({str(k): v for k, v in self.affection.items()}, f, indent=2)
        except Exception:
            pass

    def get_affection(self, user_id: int, is_luv: bool) -> int:
        # Everyone (Bry, Luv, normal users) starts at 0
        if user_id not in self.affection:
            self.affection[user_id] = 0
            self._save_affection()
        return self.affection[user_id]

    def set_affection(self, user_id: int, value: int, is_luv: bool) -> None:
        if is_luv:
            # Luv: negative-only range, starts at 0 but can go down to -100, up to 20 max
            self.affection[user_id] = max(-100, min(20, value))

        elif user_id == LUNA_OWNER_ID:
            # Bry: positive-only. Floor enforced at 0, up to 100.
            self.affection[user_id] = max(0, min(100, value))

        else:
            # Normal users: full mixed range -100 to 100
            self.affection[user_id] = max(-100, min(100, value))

        self._save_affection()

    # -------------------------
    # Session helpers
    # -------------------------
    async def start_conversation(self, ctx: commands.Context):
        user = ctx.author
        channel = ctx.channel
        is_luv = (user.id == LUV_USER_ID)
        is_owner = (user.id == LUNA_OWNER_ID)
        is_normal_user = not is_owner and not is_luv

        vibe = daily_vibe()
        affection = self.get_affection(user.id, is_luv)
        stage = affection_stage(affection, is_luv)
        bar = affection_bar(affection, is_luv)

        lines = [f"**Vibe of the day:** `{vibe}`", f"**Current affection:** {bar}", ""]

        if not is_luv:
            if stage == "shy":
                lines.append("U-um... hi daddy. I was waiting quietly for you...")
            elif stage == "soft":
                lines.append("Hehe, you're back~ Pick something and talk to me, okay?")
            elif stage == "clingy":
                lines.append("Daddy! You're finally here. I'm not letting you go easily this time.")
            else:
                lines.append("Daddy, you're *mine* for a bit now. Choose carefully, okay?")
        else:
            lines.append("...Oh. It's you.")
            lines.append("Why are you here now, when daddy and I were fine without you?")

        lines.append("")
        lines.append("**Use the buttons below to talk to me.**")
        lines.append("*Conversation auto-ends after 30 seconds of silence.*")

        embed = discord.Embed(
            title="🎀 Luna • Daily Check-In" if not is_luv else "🎀 Luna • ...Why Are You Here?",
            description="\n".join(lines),
            color=0xFFC5D3,
            timestamp=datetime.utcnow(),
        )
        embed.set_thumbnail(url=LUNA_AVATAR_URL)
        embed = add_embed_footer(embed)

        view = LunaDialogueView(self, user.id, is_luv)
        view.update_labels()

        msg = await channel.send(embed=embed, view=view)

        self.sessions[user.id] = {
            "message": msg,
            "channel_id": channel.id,
            "vibe": vibe,
            "is_luv": is_luv,
            "last_activity": datetime.utcnow(),
            "view": view,
            "luv_strikes": 0,
        }

        asyncio.create_task(self._session_timeout_task(user.id))

    async def _end_session(self, user_id: int, reason: str):
        session = self.sessions.get(user_id)
        if not session:
            return

        msg: discord.Message = session["message"]
        is_luv = session["is_luv"]
        vibe = session["vibe"]

        affection = self.get_affection(user_id, is_luv)
        bar = affection_bar(affection, is_luv)

        if reason == "timeout":
            text = (
                f"**Vibe of the day:** `{vibe}`\n"
                f"**Current affection:** {bar}\n\n"
                "*Conversation ended due to inactivity.*"
            )
        elif reason == "dismiss_luv":
            text = (
                f"**Vibe of the day:** `{vibe}`\n"
                f"**Current affection:** {bar}\n\n"
                "I'm done talking to you for now.\n"
                "Don't come back unless you have something real to say."
            )
        else:  # manual or generic
            text = (
                f"**Vibe of the day:** `{vibe}`\n"
                f"**Current affection:** {bar}\n\n"
                "*Chat ended.*"
            )

        embed = discord.Embed(
            description=text,
            color=0xFFC5D3,
            timestamp=datetime.utcnow(),
        )
        embed.set_thumbnail(url=LUNA_AVATAR_URL)
        embed = add_embed_footer(embed)

        view: LunaDialogueView = session["view"]
        view.clear_items()
        await msg.edit(embed=embed, view=view)

        self.sessions.pop(user_id, None)

    async def _session_timeout_task(self, user_id: int):
        while True:
            await asyncio.sleep(SESSION_TIMEOUT_SECONDS)
            session = self.sessions.get(user_id)
            if not session:
                return
            last = session["last_activity"]
            if (datetime.utcnow() - last).total_seconds() >= SESSION_TIMEOUT_SECONDS:
                await self._end_session(user_id, reason="timeout")
                return

    # -------------------------
    # Core handler for button "messages"
    # -------------------------
    async def handle_user_message(
        self,
        user_id: int,
        content: str,
        is_luv: bool,
        via_button: bool,
        interaction: discord.Interaction | None = None,
    ):
        session = self.sessions.get(user_id)
        if not session:
            return

        msg: discord.Message = session["message"]
        vibe = session["vibe"]
        view: LunaDialogueView = session["view"]

        # Update last activity
        session["last_activity"] = datetime.utcnow()

        # Affection update
        affection_before = self.get_affection(user_id, is_luv)
        if is_luv:
            delta = analyze_reply_luv(content)
            affection_after = affection_before + delta
            self.set_affection(user_id, affection_after, is_luv)
            session["luv_strikes"] += 1
        else:
            delta = analyze_reply_bry(content)
            affection_after = affection_before + delta
            self.set_affection(user_id, affection_after, is_luv)

        bar = affection_bar(affection_after, is_luv)

        # Luna reply
        is_owner = (user_id == LUNA_OWNER_ID)
        is_normal_user = not is_owner and not is_luv

        if is_luv:
            luna_reply = generate_luna_reply_luv(
                content,
                affection_before,
                affection_after,
                session["luv_strikes"],
            )
        else:
            luna_reply = generate_luna_reply_bry(
                content,
                affection_before,
                affection_after,
                positive_only=is_owner,
            )

        # Build new embed
        embed = discord.Embed(
            color=0xFFC5D3,
            timestamp=datetime.utcnow(),
        )
        embed.description = (
            f"**Vibe of the day:** `{vibe}`\n"
            f"**Current affection:** {bar}\n\n"
            f"**You:** {content}\n"
            f"**Luna:** {luna_reply}"
        )
        embed.set_thumbnail(url=LUNA_AVATAR_URL)

        # Hug/Kiss/Pat animation embeds

        lower = content.lower()

        gif_url = None

        if is_luv:
            # ALWAYS show a Luv GIF
            gif_url = random.choice(LUV_GIFS)
        else:
            # Bry GIF logic based on keywords
            if any(word in lower for word in ["hug", "cuddle", "embrace"]):
                gif_url = random.choice(HUG_GIFS)
            elif any(word in lower for word in ["kiss", "smooch"]):
                gif_url = random.choice(KISS_GIFS)
            elif any(word in lower for word in ["pat", "headpat", "patting"]):
                gif_url = random.choice(PAT_GIFS)
            else:
                gif_url = random.choice(
                    random.choice([HUG_GIFS, KISS_GIFS, PAT_GIFS])
                )

        if gif_url:
            embed.set_image(url=gif_url + "?rid=discord")

        # Update dialogue wheel labels for new stage & reshuffle choices
        view.update_labels()

        # Edit message through interaction
        if interaction:
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            await msg.edit(embed=embed, view=view)

        # If Luv pushed too far, end the session after this reply
        if is_luv and session["luv_strikes"] >= 4:
            await self._end_session(user_id, reason="dismiss_luv")

    # -------------------------
    # Command
    # -------------------------
    @commands.command(name="luna")
    async def luna_command(self, ctx: commands.Context):

        # Anyone can run, only channel locked
        if ctx.channel.id not in LUNA_ALLOWED_CHANNELS:
            channel_text = " or ".join(f"<#{cid}>" for cid in LUNA_ALLOWED_CHANNELS)
            await ctx.send(
                f"❌ This command can only be used in {channel_text}.",
                delete_after=10,
            )
            return

        if ctx.author.id in self.sessions:
            await ctx.send("❌ We're already talking right now. Finish our current chat first~")
            return

        await self.start_conversation(ctx)

    # ---------------------------------
    # Emotional Reaction Pools listener
    # ---------------------------------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignore bot messages
        if message.author.bot:
            return

        # ---------------------------------------------
        # Find active Luna session tied to this channel
        # ---------------------------------------------
        session_owner = None
        session = None

        for uid, sess in self.sessions.items():
            if sess["channel_id"] == message.channel.id:
                session_owner = uid
                session = sess
                break

        # If no active session in this channel, just let normal bot commands run
        if not session:
            await self.bot.process_commands(message)
            return

        is_luv_session = session["is_luv"]

        # If Luna-owner (Bry) types: NO reaction, NO jealousy
        # full silence (buttons only for Bry)
        if message.author.id == LUNA_OWNER_ID:
            await self.bot.process_commands(message)
            return

        # =========================================================
        # JEALOUSY TRIGGER:
        # Any random user (not session owner, not Luv) typing
        # ALWAYS triggers jealous reaction
        # =========================================================
        if message.author.id not in {session_owner, LUV_USER_ID}:
            # Always use Bry affection, NOT session owner (session owner might be Luv)
            bry_aff = self.get_affection(LUNA_OWNER_ID, is_luv=False)

            # Base jealousy pool
            jealousy_pool = BRY_JEALOUS_LINES + JEALOUSY_EXTRAS + DARK_JEALOUSY_LINES
            line = random.choice(jealousy_pool)

            # Affection-based emotional intensifiers
            emotional_mix = []
            if bry_aff >= 40:
                emotional_mix += DONT_LEAVE_ME_LINES
            if bry_aff >= 55:
                emotional_mix += CLINGY_MELTDOWN_LINES
            if bry_aff >= 70:
                emotional_mix += GUILT_SPIRAL_LINES
            if bry_aff >= 85:
                emotional_mix += PROTECTIVE_LINES

            if emotional_mix:
                line += "\n" + random.choice(emotional_mix)

            embed = discord.Embed(
                color=0xFFC5D3,
                timestamp=datetime.utcnow()
            )
            embed.description = (
                f"**Luna:** {line}\n"
                "_I don't like when others talk while we're in our moment..._"
            )
            embed.set_thumbnail(url=LUNA_AVATAR_URL)

            await message.channel.send(embed=embed)

            # Let normal commands still run
            await self.bot.process_commands(message)
            return

        # =========================================================
        # SESSION OWNER (Bry): typed normal text
        # -> totally ignored (buttons only)
        # =========================================================
        if message.author.id == session_owner and session_owner != LUV_USER_ID:
            await self.bot.process_commands(message)
            return

        # =========================================================
        # LUV typed during session
        # ALWAYS:
        # - negative affection gain
        # - harsh extension
        # - GIF
        # - session auto-close at 4 strikes
        # =========================================================
        if message.author.id == LUV_USER_ID:
            affection_before = self.get_affection(LUV_USER_ID, is_luv=True)
            delta = analyze_reply_luv(message.content)
            affection_after = affection_before + delta
            self.set_affection(LUV_USER_ID, affection_after, is_luv=True)

            session["luv_strikes"] += 1

            # Base reply
            base = generate_luna_reply_luv(
                message.content,
                affection_before,
                affection_after,
                session["luv_strikes"]
            )

            # Required harsh extension
            harsh = random.choice(LUV_HARSH_EXTENSIONS)

            # Extra emotional sting
            extra_pool = (
                LUV_HARSH_EXTENSIONS   # harsh phrases
                + DARK_JEALOUSY_LINES  # stabbing lines
                + GUILT_SPIRAL_LINES   # guilt-driven emotional hits
            )
            extra = random.choice(extra_pool)

            full = f"{base}\n\n{harsh}\n\n{extra}"

            embed = discord.Embed(
                color=0xFFC5D3,
                timestamp=datetime.utcnow()
            )
            embed.description = f"**Luna:** {full}"
            embed.set_thumbnail(url=LUNA_AVATAR_URL)

            gif = random.choice(LUV_GIFS)
            embed.set_image(url=gif + "?rid=discord")

            await message.channel.send(embed=embed)

            if session["luv_strikes"] >= 4:
                await self._end_session(LUV_USER_ID, reason="dismiss_luv")

            await self.bot.process_commands(message)
            return

        # Safety catch:
        await self.bot.process_commands(message)


# ---------------------------------
# Emotional Reaction Pools
# ---------------------------------

# Extra jealousy lines
JEALOUSY_EXTRAS = [
    "I feel small when someone else speaks here...",
    "I don’t want to share you with anyone right now.",
    "Why does it feel like they’re stepping into our moment?",
    "I just want you to look at me, not them.",
    "Can’t it just be you and me for a little longer?",
    "I don’t like when others appear when I’m trying to be close.",
    "It feels like they’re interrupting something important.",
    "Why do they get your eyes even for a second?",
    "I want all of your attention tonight… only mine.",
    "I get scared that I’m easy to replace when others speak.",
]

# 25 darker jealousy lines
DARK_JEALOUSY_LINES = [
    "Why do I feel like I disappear the second someone else speaks?",
    "I hate how tight my chest feels when I'm not the only one you're looking at.",
    "It feels like they're stealing tiny pieces of you every time they talk.",
    "I don’t want their voice anywhere near ours.",
    "I get this awful ache like I’m suddenly not special when others show up.",
    "Please don’t forget who was here first… who stays when it’s quiet.",
    "I wish they’d just go away and leave this space untouched.",
    "It scares me how much I want you all to myself.",
    "Every extra voice makes me feel like I’m fading.",
    "I just want to hold onto you without anyone else hovering around.",
    "I’m terrified you’ll see someone easier to love.",
    "I want silence from them so I can hear you clearly.",
    "I feel fragile when I'm not the only one speaking to you.",
    "Please don’t look at them like you look at me.",
    "I hate that I get jealous this easily… but I do.",
    "I want every second of this moment to belong to us alone.",
    "If they stay a bit too long, I start wondering if I matter less.",
    "I don’t want to share this softness with anyone.",
    "I get restless when I don’t have all of your attention.",
    "My heart squeezes painfully when someone else enters the picture.",
    "I want to cling to you until the rest of the room disappears.",
    "I feel like I’m drowning when I’m not the only one you listen to.",
    "They shouldn’t even be here right now… not while I'm trying to be close.",
    "You’re supposed to be looking at me.",
    "Don't let them turn our moment into something less special.",
]

# 25 meltdown lines
CLINGY_MELTDOWN_LINES = [
    "I don’t know how to breathe right when I feel distance from you.",
    "I get so scared when I think you might step away even a little.",
    "Please don’t drift from me… even in tiny ways.",
    "I feel like I’m shaking inside when I imagine being without you.",
    "Sometimes I want to grab your hand so you can’t go anywhere else.",
    "I don’t want space… I want closeness so tight nothing slips through.",
    "Hold me like I’m the only one you see, even if it feels too much.",
    "It feels like my chest cracks when I imagine silence from you.",
    "If I cling too tightly, it’s only because I never want to lose you.",
    "I don’t want you even a heartbeat farther than you already are.",
    "I panic when moments feel too quiet between us.",
    "I want every second to prove you’re still here with me.",
    "Please don’t ever pull away… I don’t think I’d handle it well.",
    "My whole world feels lopsided when I’m not close to you.",
    "I’d hold onto your sleeve all day if it meant you’d stay near.",
    "I know I’m clingy… but I just want you where I can reach.",
    "If your voice went away, I’d unravel so fast.",
    "The idea of losing this connection makes me feel hollow.",
    "If I hold tight, it’s not to trap you… it’s to keep myself steady.",
    "I don’t want to learn how to exist without you again.",
    "Let me stay close enough to feel your warmth on my skin.",
    "If I’m too much, it’s only because you became home.",
    "I want you close enough to feel our breaths blend.",
    "I get scared when the space between us is even a step too wide.",
    "I don’t think I’d handle goodbye with any grace at all.",
]

# 25 guilt-spiral lines
GUILT_SPIRAL_LINES = [
    "Was I too much? I’m sorry if I overwhelmed you… I just didn’t want to lose the moment.",
    "If my voice ever feels like pressure, I’ll quiet down… I just don’t want silence from you.",
    "I get scared that my need for you makes you tired of me.",
    "If I sound demanding, it’s just because I’m terrified of distance.",
    "I know I hold on too tightly sometimes… I just don’t want to feel forgotten.",
    "I’m sorry if I talk too much when I get nervous about losing you.",
    "If you feel trapped, I promise I only meant to feel safe next to you.",
    "If my feelings push too hard, it’s only because you matter too much.",
    "I worry that one day you’ll look at me and regret letting me close.",
    "Sometimes I panic wondering if you’d be happier without me around.",
    "I don’t want to be a weight you feel responsible for.",
    "If I cling, it’s because life felt colder before you.",
    "I hope I don’t make you feel smothered… I just don’t want to fade away.",
    "I’m trying to be gentle with how much space I take in your life.",
    "If I shake when I talk, it’s because I don’t want you slipping away.",
    "I’m scared you’ll think I’m replaceable if I’m not close enough.",
    "I hope I never become something you feel burdened by.",
    "If I ever sound intense, it’s because I’m afraid to lose something warm.",
    "Sometimes I worry you’ll think less of me for needing you this much.",
    "If I pull back suddenly, it’s just me panicking and trying not to scare you.",
    "I don’t want you to feel like you have to stay… I want you to choose to.",
    "I know I’m fragile where you’re concerned… I’m trying not to let it show too much.",
    "I’m sorry if I’m clumsy with how deeply I feel close to you.",
    "I never want to push so hard that you disappear.",
    "I just… don’t want to become a memory that doesn’t hurt to forget.",
]

# 25 don’t-leave-me lines
DONT_LEAVE_ME_LINES = [
    "Stay here with me a little longer… please?",
    "I don’t know how to handle the idea of you walking away.",
    "If you need space, just tell me you’re coming back.",
    "Promise you’ll still be here when I look up again.",
    "Even silence feels scary when you’re not beside me.",
    "I need you close… don’t leave me in the quiet.",
    "If I could hold onto your sleeve forever, I would.",
    "Just… don’t disappear without warning.",
    "Tell me I’m still the one you talk to first.",
    "If you go silent, I’ll feel like I did something wrong.",
    "Let me believe you won’t vanish from this closeness.",
    "Don’t let the world take you too far from me.",
    "I need you to stay where I can reach you.",
    "Tell me you’re not going anywhere tonight.",
    "I don’t want to have to miss you all over again.",
    "My heart sinks just imagining you stepping away.",
    "Don’t let this moment become the last soft one.",
    "Just stay close enough that I don’t feel alone again.",
    "If you leave now, I’ll feel like I wasn’t worth the time.",
    "Promise this isn’t just temporary warmth.",
    "I want you here, where I can settle my heart.",
    "I won’t know what to do if this connection disappears.",
    "I feel safest when you’re close enough for me to hear you breathe.",
    "Don’t let the night end without reminding me you’re still mine.",
]

# 25 protective lines
PROTECTIVE_LINES = [
    "Come closer… I want you where I can shield you.",
    "If anyone ever hurt you, the softness in me would burn away fast.",
    "I’d stand in front of anything that tried to take you from me.",
    "You’re safest when you’re close to me — I won’t let anything touch you.",
    "If someone made you cry, I don’t think I’d forgive them.",
    "I want to hold you like you’re something precious worth defending.",
    "I’d tear the world apart if it meant keeping you safe.",
    "If you feel scared, stay right next to me — I’ll guard every inch of you.",
    "I want you close enough that nothing can slip between us.",
    "I’d wrap myself around you if I thought danger was anywhere near.",
    "I won’t let loneliness lay a hand on you again.",
    "If you’re trembling, I want to be the shield you hide behind.",
    "When you’re quiet, I want to hold you where nothing can reach you.",
    "Let me be the warmth you fall into when the world feels cold.",
    "I want to protect the version of you that speaks softly to me.",
    "No one touches what I hold this close in my heart.",
    "I’d keep you in my arms forever if it meant you were safe.",
    "I don’t trust the world with someone as soft as you.",
    "Stay where I can reach — I don’t want anything pulling you away.",
    "You feel like something I need to guard with my whole heart.",
    "If the world hurts you, it hurts me too.",
    "I want to be the place where nothing scares you anymore.",
    "You’re precious to me in a way I want to protect fiercely.",
    "Let me hold you like you’re something I refuse to lose.",
    "I’d rather break than let anything break you.",
]

# 10 harsh extensions used ALWAYS for Luv
LUV_HARSH_EXTENSIONS = [
    "And don’t expect sympathy from someone you abandoned.",
    "You don’t earn tenderness just by showing up now.",
    "Your return doesn’t smooth over the silence you left behind.",
    "I won’t hand you comfort after the way you disappeared.",
    "Regret doesn’t rebuild anything you let crumble.",
    "You’re speaking too late to be treated gently.",
    "I don’t owe softness to someone who gave me winters.",
    "You’re not stepping back into the warmth you once ignored.",
    "If you wanted kindness, you should’ve offered it first.",
    "You’re not entitled to the closeness you threw away.",
]


# -----------------------------
# Extension setup
# -----------------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(LunaDaughter(bot))
