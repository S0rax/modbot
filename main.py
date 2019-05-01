import discord
from discord.ext import commands

import datetime
import json

from bot_tools import get_member, error_embed, success_embed, log


with open("credentials.json", "r") as creds:
    credentials = json.load(creds)

bot = commands.Bot(command_prefix=credentials["prefix"], description="Speedrunners ModBot")
bot.remove_command("help")

# Speedrunners
sr = credentials["server_main"]
sr_admin = credentials["admin_main"]

# SR Management
srm = credentials["server_management"]
srm_admin = credentials["admin_management"]

# Channels
edit_log = credentials["edit_log"]
delete_log = credentials["delete_log"]
mute_log = credentials["mute_log"]
kick_log = credentials["kick_log"]
ban_log = credentials["ban_log"]

def is_admin():
    # @is_admin()
    async def predicate(ctx):
        user_roles = [role.id for role in ctx.author.roles]
        return ((sr_admin in user_roles) or
               (srm_admin in user_roles) or
               (test_admin in user_roles))
    return commands.check(predicate)

@bot.listen()
async def on_message_edit(before, after):
    if after.author.bot:
        return
    if not after.guild == bot.get_guild(sr):
        return
    if before.content == after.content:
        return

    desc = await log("edited_messages", {"ID": after.id, "User": str(after.author), "Channel": after.channel.name, 
                                         "Before": before.clean_content, "After": after.clean_content, "Jump To": f"[Link]({after.jump_url})",
                                         "Timestamp": (after.edited_at.now().isoformat() if not after.edited_at == None else after.created_at.now().isoformat())})

    embed = discord.Embed(description="\n".join([line for line in desc.split("\n") if not line.startswith("**User**")]), color=0xFFA500)
    embed.set_author(name=str(after.author), url=after.author.avatar_url, icon_url=after.author.avatar_url)

    channel = bot.get_channel(edit_log)
    await channel.send(embed=embed)

@bot.listen()
async def on_message_delete(message):
    if message.author.bot:
        return
    if not message.guild == bot.get_guild(sr):
        return

    desc = await log("deleted_messages", {"ID": message.id, "User": str(message.author), "Channel": message.channel.name, "Message": message.clean_content, 
                     "Timestamp": (message.edited_at.now().isoformat() if not message.edited_at == None else message.created_at.now().isoformat())})
    
    embed = discord.Embed(description="\n".join([line for line in desc.split("\n") if not line.startswith("**User**")]), color=0xFF0000)
    embed.set_author(name=str(message.author), url=message.author.avatar_url, icon_url=message.author.avatar_url)
    channel = bot.get_channel(delete_log)
    await channel.send(embed=embed)

@bot.command()
async def help(ctx):
    kick = f"\t{bot.command_prefix}**kick** <member> <reason>"
    ban = f"\t{bot.command_prefix}**ban** <member> <reason>"
    help = f"\t{bot.command_prefix}**help**"
    online = f"\t{bot.command_prefix}**online**"
    uptime = f"Bot uptime: {str(datetime.datetime.now() - start_time)[:-7]}"

    embed = discord.Embed(color=0x506600)
    embed.add_field(name="Commands:", value="\n".join([kick, ban, online, help, "", uptime]))
    await ctx.send(embed=embed)

@bot.command()
async def online(ctx):
    guild = bot.get_guild(sr)
    member_count = guild.member_count
    status_count = [0,0,0,0] # online, idle, dnd, offline
    for member in guild.members:
        if member.status is discord.Status.online:
            status_count[0] += 1
        elif member.status is discord.Status.idle:
            status_count[1] += 1
        elif member.status is discord.Status.do_not_disturb:
            status_count[2] += 1
        else:
            status_count[3] += 1

    stats = discord.Embed(color=0x506600)
    stats.add_field(name=f"Total members: {member_count}", value="\n".join([
                                             f"<:online:572884944813031434>{status_count[0]}",
                                             f"<:idle:572884943898673174>{status_count[1]}",
                                             f"<:do_not_disturb:572884944016113666>{status_count[2]}",
                                             f"<:offline:572884944343269378>{status_count[3]}"]))
    await ctx.send(embed=stats)


@bot.command()
@is_admin()
async def kick(ctx, user, *args):
    member = await get_member(ctx, bot.get_guild(sr), user)
    if member == None:
        await ctx.send(embed=await error_embed(f"Unknown user '{user}''"))
    
    try:
        await bot.get_guild(sr).kick(member, reason=" ".join(args))
        await ctx.send(embed=await success_embed(f"Kicked '{user}'"))
    except discord.Forbidden:
        await ctx.send(embed=await error_embed(f"This bot does not have the `kick_members` permission."))
        return
    except discord.HTTPException:
        await ctx.send(embed=await error_embed(f"HTTP Error, try again?"))
        return
        
    desc = await log("kicks", {"Kicked": member.name, 
                                "Kicked by": ctx.message.author.name, 
                                "Reason": " ".join(args), 
                                "Timestamp": ctx.message.created_at.now().isoformat()})
    embed = discord.Embed(title="Kicked member", description=desc, color=0xFFA500)
    channel = bot.get_channel(kick_log)
    await channel.send(embed=embed)

@bot.command()
@is_admin()
async def ban(ctx, user, *args):
    member = await get_member(ctx, bot.get_guild(sr), user)
    if member == None:
        await ctx.send(embed=await error_embed(f"Unknown user '{user}''"))
    
    try:
        await bot.get_guild(sr).ban(member, reason=" ".join(args))
        await ctx.send(embed=await success_embed(f"Banned '{user}'"))
    except discord.Forbidden:
        await ctx.send(embed=await error_embed(f"This bot does not have the `ban_members` permission."))
        return
    except discord.HTTPException:
        await ctx.send(embed=await error_embed(f"HTTP Error, try again?"))
        return
        
    desc = await log("bans", {"Banned": member.name, 
                                "Banned by": ctx.message.author.name, 
                                "Reason": " ".join(args), 
                                "Timestamp": ctx.message.created_at.now().isoformat()})
    embed = discord.Embed(title="Banned member", description=desc, color=0xCC0000)
    channel = bot.get_channel(ban_log)
    await channel.send(embed=embed)

start_time = datetime.datetime.now()

bot.run(credentials["token"])


    
