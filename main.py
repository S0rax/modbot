import discord
from discord.ext import commands

import datetime
import json

from bot_tools import get_member, error_embed, success_embed, log

bot = commands.Bot(command_prefix='!', description="Speedrunners ModBot")
bot.remove_command("help")
with open("credentials.json", "r") as creds:
    credentials = json.load(creds)

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

# CHECKS 
def is_admin():
    # @is_admin()
    async def predicate(ctx):
        user_roles = [role.id for role in ctx.author.roles]
        return ((sr_admin in user_roles) or
               (srm_admin in user_roles) or
               (test_admin in user_roles))
    return commands.check(predicate)

# LISTEN EVENTS
@bot.listen()
async def on_message_edit(before, after):
    if after.author.bot:
        return
    if not after.guild == bot.get_guild(sr):
        return

    desc = await log("edited_messages", {"ID": after.id, "User": after.author.name, "Channel": after.channel.name, "Before": before.content, "After": after.content, 
                                         "Timestamp": (after.edited_at.now().isoformat() if not after.edited_at == None else after.created_at.now().isoformat())})

    embed = discord.Embed(title="Edited Message", description=desc, color=0xFFA500)
    channel = bot.get_channel(edit_log)
    await channel.send(embed=embed)

@bot.listen()
async def on_message_delete(message):
    if message.author.bot:
        return
    if not message.guild == bot.get_guild(sr):
        return

    desc = await log("deleted_messages", {"ID": message.id, "User": message.author.name, "Channel": message.channel.name, "Message": message.content, 
                     "Timestamp": (message.edited_at.now().isoformat() if not message.edited_at == None else message.created_at.now().isoformat())})
    
    embed = discord.Embed(title="Deleted Message", description=desc, color=0xCC0000)
    channel = bot.get_channel(delete_log)
    await channel.send(embed=embed)
        
# COMMANDS

@bot.command()
async def help(ctx):
    description = "A discord bot for moderating the server\n\nCommands:"
    mute = f"\t{bot.command_prefix}mute <member> <reason>"
    kick = f"\t{bot.command_prefix}kick <member> <reason>"
    ban = f"\t{bot.command_prefix}ban <member> <reason>"
    help = f"\t{bot.command_prefix}help"

    embed = discord.Embed(description=("\n".join([description, mute, kick, ban, help])).replace("\t", "　　"))
    await ctx.send(embed=embed)

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

bot.run(credentials["token"])
