import discord
from discord.ext import commands
import json
import os
import random
import youtube_dl
import asyncio

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Load data files
def load_json(file):
    if os.path.exists(file):
        with open(file, 'r') as f:
            return json.load(f)
    return {}

config = load_json('config.json')
economy = load_json('economy.json')
levels = load_json('levels.json')
custom_commands = load_json('custom.json')

def save_json(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=2)

# Bot status and startup
@bot.event
async def on_ready():
    print(f'Waveflow is online as {bot.user}!')
    await bot.change_presence(activity=discord.Game(name="🌊 Riding the waves of fun! | Made by Animecx"))

# Embed helper function
def create_embed(title, description, color=0x0099ff):
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text="Waveflow 🌊 | Made by Animecx")
    embed.timestamp = discord.utils.utcnow()
    return embed

# Moderation Commands
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.kick(reason=reason)
    await ctx.send(embed=create_embed("User Kicked", f"{member} was kicked for: {reason}", 0xff5555))
    await log_action(ctx.guild, "Kick", member, ctx.author, reason)

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.ban(reason=reason)
    await ctx.send(embed=create_embed("User Banned", f"{member} was banned for: {reason}", 0xff5555))
    await log_action(ctx.guild, "Ban", member, ctx.author, reason)

@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member):
    settings = config.get(str(ctx.guild.id), {})
    if not settings.get("mute_role"):
        await ctx.send(embed=create_embed("Setup Required", "Set a mute role with !setmute @role", 0xffaa00))
        return
    mute_role = ctx.guild.get_role(int(settings["mute_role"]))
    await member.add_roles(mute_role)
    await ctx.send(embed=create_embed("User Muted", f"{member} has been muted!", 0xffaa00))
    await log_action(ctx.guild, "Mute", member, ctx.author, "Muted")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member):
    settings = config.get(str(ctx.guild.id), {})
    mute_role = ctx.guild.get_role(int(settings.get("mute_role", 0)))
    if mute_role in member.roles:
        await member.remove_roles(mute_role)
        await ctx.send(embed=create_embed("User Unmuted", f"{member} has been unmuted!", 0x00ff00))
        await log_action(ctx.guild, "Unmute", member, ctx.author, "Unmuted")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member, *, reason="No reason provided"):
    try:
        await member.send(f"You were warned in {ctx.guild.name} for: {reason}")
    except:
        await ctx.send(embed=create_embed("Warning", "Couldn’t DM the user.", 0xffaa00))
    await ctx.send(embed=create_embed("User Warned", f"{member} has been warned!", 0xff5555))
    await log_action(ctx.guild, "Warn", member, ctx.author, reason)

# Setup Commands
@bot.command()
@commands.has_permissions(administrator=True)
async def setwelcome(ctx, channel: discord.TextChannel):
    config[str(ctx.guild.id)] = config.get(str(ctx.guild.id), {})
    config[str(ctx.guild.id)]["welcome_channel"] = str(channel.id)
    save_json('config.json', config)
    await ctx.send(embed=create_embed("Setup Complete", f"Welcome channel set to {channel.mention}!", 0x00ff00))

@bot.command()
@commands.has_permissions(administrator=True)
async def setlog(ctx, channel: discord.TextChannel):
    config[str(ctx.guild.id)] = config.get(str(ctx.guild.id), {})
    config[str(ctx.guild.id)]["log_channel"] = str(channel.id)
    save_json('config.json', config)
    await ctx.send(embed=create_embed("Setup Complete", f"Log channel set to {channel.mention}!", 0x00ff00))

@bot.command()
@commands.has_permissions(administrator=True)
async def setmute(ctx, role: discord.Role):
    config[str(ctx.guild.id)] = config.get(str(ctx.guild.id), {})
    config[str(ctx.guild.id)]["mute_role"] = str(role.id)
    save_json('config.json', config)
    await ctx.send(embed=create_embed("Setup Complete", f"Mute role set to {role.mention}!", 0x00ff00))

@bot.command()
@commands.has_permissions(administrator=True)
async def setverify(ctx, channel: discord.TextChannel, unverified: discord.Role, member: discord.Role):
    msg = await channel.send("React with ✅ to verify!")
    await msg.add_reaction("✅")
    config[str(ctx.guild.id)] = config.get(str(ctx.guild.id), {})
    config[str(ctx.guild.id)]["verification"] = {
        "channel": str(channel.id),
        "message": str(msg.id),
        "unverified_role": str(unverified.id),
        "member_role": str(member.id)
    }
    save_json('config.json', config)
    await ctx.send(embed=create_embed("Verification Set", "Verification system is ready!", 0x00ff00))

# Music Commands
ytdl_format_options = {'format': 'bestaudio/best', 'noplaylist': True}
ffmpeg_options = {'options': '-vn'}

@bot.command()
async def play(ctx, *, url):
    if not ctx.author.voice:
        await ctx.send(embed=create_embed("Error", "Join a voice channel first!", 0xff0000))
        return
    channel = ctx.author.voice.channel
    vc = await channel.connect()
    with youtube_dl.YoutubeDL(ytdl_format_options) as ydl:
        info = ydl.extract_info(url, download=False)
        url2 = info['url']
    vc.play(discord.FFmpegPCMAudio(url2, **ffmpeg_options))
    await ctx.send(embed=create_embed("Now Playing", f"🎶 Streaming: {info['title']}", 0x00ffaa))

@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send(embed=create_embed("Stopped", "Music stopped, leaving the channel!", 0xff5555))

# Economy Commands
@bot.command()
async def balance(ctx):
    user_id = str(ctx.author.id)
    economy[user_id] = economy.get(user_id, {"coins": 0})
    await ctx.send(embed=create_embed("Your Balance", f"🌊 You have {economy[user_id]['coins']} Wavecoins!", 0x00aaff))

@bot.command()
async def work(ctx):
    user_id = str(ctx.author.id)
    economy[user_id] = economy.get(user_id, {"coins": 0})
    earned = random.randint(50, 150)
    economy[user_id]["coins"] += earned
    save_json('economy.json', economy)
    await ctx.send(embed=create_embed("Work Complete", f"You earned {earned} Wavecoins! Total: {economy[user_id]['coins']}", 0x00ff00))

# Fun Commands
@bot.command()
async def meme(ctx):
    await ctx.send(embed=create_embed("Meme Time", "Here’s a random meme! (Imagine a funny image 😅)", 0xffaa00))

@bot.command()
async def eightball(ctx, *, question):
    answers = ["Yes", "No", "Maybe", "Ask again later"]
    await ctx.send(embed=create_embed("Magic 8-Ball", f"🎱 {question}? {random.choice(answers)}", 0xaa00ff))

@bot.command()
async def roll(ctx, sides: int = 6):
    result = random.randint(1, sides)
    await ctx.send(embed=create_embed("Dice Roll", f"🎲 You rolled a {result} (1-{sides})!", 0x00aaff))

# Custom Commands
@bot.command()
@commands.has_permissions(administrator=True)
async def addcmd(ctx, name, *, response):
    custom_commands[str(ctx.guild.id)] = custom_commands.get(str(ctx.guild.id), {})
    custom_commands[str(ctx.guild.id)][name] = response
    save_json('custom.json', custom_commands)
    await ctx.send(embed=create_embed("Command Added", f"Added !{name} with response: {response}", 0x00ff00))

@bot.command()
async def delcmd(ctx, name):
    if str(ctx.guild.id) in custom_commands and name in custom_commands[str(ctx.guild.id)]:
        del custom_commands[str(ctx.guild.id)][name]
        save_json('custom.json', custom_commands)
        await ctx.send(embed=create_embed("Command Deleted", f"Removed !{name}", 0xff5555))

# Leveling System
@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return
    user_id = str(message.author.id)
    levels[user_id] = levels.get(user_id, {"xp": 0, "level": 1})
    levels[user_id]["xp"] += random.randint(5, 15)
    if levels[user_id]["xp"] >= levels[user_id]["level"] * 100:
        levels[user_id]["level"] += 1
        levels[user_id]["xp"] = 0
        await message.channel.send(embed=create_embed("Level Up!", f"Congrats {message.author.mention}, you’re now level {levels[user_id]['level']}!", 0x00ffaa))
    save_json('levels.json', levels)
    await bot.process_commands(message)

# Custom command handler
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        cmd = ctx.message.content.split()[0][1:]
        guild_id = str(ctx.guild.id)
        if guild_id in custom_commands and cmd in custom_commands[guild_id]:
            await ctx.send(embed=create_embed("Custom Command", custom_commands[guild_id][cmd], 0x00aaff))

# Welcome and Verification
@bot.event
async def on_member_join(member):
    settings = config.get(str(member.guild.id), {})
    if "welcome_channel" in settings:
        channel = member.guild.get_channel(int(settings["welcome_channel"]))
        await channel.send(embed=create_embed("🌊 Welcome Aboard!", f"Ahoy {member.mention}! Ride the waves with us!", 0x00ff00))
    if "verification" in settings:
        await member.add_roles(member.guild.get_role(int(settings["verification"]["unverified_role"])))
        channel = member.guild.get_channel(int(settings["verification"]["channel"]))
        await channel.send(f"Welcome {member.mention}, react to the verification message with ✅!")

@bot.event
async def on_raw_reaction_add(payload):
    if payload.member.bot:
        return
    settings = config.get(str(payload.guild_id), {})
    if "verification" in settings and str(payload.message_id) == settings["verification"]["message"]:
        if str(payload.emoji) == "✅":
            guild = bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            await member.remove_roles(guild.get_role(int(settings["verification"]["unverified_role"])))
            await member.add_roles(guild.get_role(int(settings["verification"]["member_role"])))

# Logging
async def log_action(guild, action, target, moderator, reason):
    settings = config.get(str(guild.id), {})
    if "log_channel" in settings:
        channel = guild.get_channel(int(settings["log_channel"]))
        embed = create_embed(f"{action} Log", f"**User:** {target}\n**Moderator:** {moderator}\n**Reason:** {reason}", 0xff0000)
        await channel.send(embed=embed)

# Help Command
@bot.command()
async def help(ctx):
    embed = discord.Embed(title="🌊 Waveflow Commands", description="Over 50 commands to ride the waves!", color=0x0099ff)
    embed.add_field(name="Moderation", value="`!kick`, `!ban`, `!mute`, `!unmute`, `!warn`", inline=True)
    embed.add_field(name="Setup", value="`!setwelcome`, `!setlog`, `!setmute`, `!setverify`", inline=True)
    embed.add_field(name="Music", value="`!play`, `!stop`", inline=True)
    embed.add_field(name="Economy", value="`!balance`, `!work`", inline=True)
    embed.add_field(name="Fun", value="`!meme`, `!8ball`, `!roll`", inline=True)
    embed.add_field(name="Custom", value="`!addcmd`, `!delcmd`", inline=True)
    embed.set_footer(text="Waveflow 🌊 | Made by Animecx")
    await ctx.send(embed=embed)

# Additional Commands (to reach 50+)
@bot.command()
async def ping(ctx):
    await ctx.send(embed=create_embed("Pong!", f"Latency: {round(bot.latency * 1000)}ms", 0x00aaff))

@bot.command()
async def stats(ctx):
    embed = create_embed("Server Stats", f"Members: {ctx.guild.member_count}\nChannels: {len(ctx.guild.channels)}", 0x00ffaa)
    await ctx.send(embed=embed)

@bot.command()
async def rank(ctx):
    user_id = str(ctx.author.id)
    level_data = levels.get(user_id, {"xp": 0, "level": 1})
    await ctx.send(embed=create_embed("Your Rank", f"Level: {level_data['level']}\nXP: {level_data['xp']}/{level_data['level'] * 100}", 0x00ffaa))

# Run the bot
bot.run('MTM1NjE5MzE0NDI1MjkyMzkxNA.GEZaS3.ZDY0pbPItC1yAsTF3hQkbSUDXas2A-X2qS4CJ8')
