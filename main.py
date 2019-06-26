import discord
from discord.ext import commands

from pytimeparse import parse as parse_time

import datetime
import json

from bot_tools import setup, get_member, error_embed, success_embed, log, mute_member, check_mutes

with open("credentials.json", "r") as creds:
    credentials = json.load(creds)

bot = commands.Bot(
    command_prefix=credentials["prefix"],
    description="SpeedRunners ModBot"
)
bot.remove_command("help")

sr = credentials["server_main"]
sr_admin = credentials["admin_main"]

srm = credentials["server_management"]
srm_admin = credentials["admin_management"]

edit_log = credentials["edit_log"]
delete_log = credentials["delete_log"]
mute_log = credentials["mute_log"]
kick_log = credentials["kick_log"]
ban_log = credentials["ban_log"]


def is_admin() -> bool:
    # @is_admin()
    async def predicate(ctx: commands.Context) -> bool:
        user_roles = [role.id for role in ctx.author.roles]
        return (sr_admin in user_roles or
                srm_admin in user_roles)

    return commands.check(predicate)


@bot.listen()
async def on_ready() -> None:
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    setup(credentials, bot, mute_log)
    bot.loop.create_task(check_mutes())


@bot.listen()
async def on_message_edit(before: discord.Message, after: discord.Message) -> None:
    if (after.author.bot or
            after.guild == bot.get_guild(sr) or
            before.content == after.content):
        return

    desc = await log("edited_messages", {
        "ID": after.id,
        "User": str(after.author),
        "Channel": after.channel.name,
        "Before": before.clean_content,
        "After": after.clean_content,
        "Jump To": f"[Link]({after.jump_url})",
        "Timestamp": (after.edited_at.now().isoformat()
                      if after.edited_at is not None else
                      after.created_at.now().isoformat())
    })

    desc = "\n".join([line for line in desc.split("\n") if not line.startswith("**User**")])

    embed = discord.Embed(description=desc, color=0xFFA500)
    embed.set_author(name=str(after.author),
                     url=after.author.avatar_url,
                     icon_url=after.author.avatar_url
                     )

    channel = bot.get_channel(edit_log)
    await channel.send(embed=embed)


@bot.listen()
async def on_message_delete(message: discord.Message) -> None:
    if message.author.bot or message.guild != bot.get_guild(sr):
        return

    desc = await log("deleted_messages",
                     {"ID": message.id,
                      "User": str(message.author),
                      "Channel": message.channel.name,
                      "Message": message.clean_content,
                      "Timestamp": (message.edited_at.now().isoformat()
                                    if message.edited_at is not None else
                                    message.created_at.now().isoformat())
                      })

    desc = "\n".join([line for line in desc.split("\n") if not line.startswith("**User**")])

    embed = discord.Embed(description=desc, color=0xFF0000)
    embed.set_author(
        name=str(message.author),
        url=message.author.avatar_url,
        icon_url=message.author.avatar_url
    )

    channel = bot.get_channel(delete_log)
    await channel.send(embed=embed)


@bot.command()
async def help(ctx: commands.Context) -> None:
    kick = f"\t{bot.command_prefix}**kick** <member> <reason>"
    ban = f"\t{bot.command_prefix}**ban** <member> <reason>"
    help = f"\t{bot.command_prefix}**help**"
    online = f"\t{bot.command_prefix}**online**"
    uptime = f"Bot uptime: {str(datetime.datetime.now() - start_time)[:-7]}"

    embed = discord.Embed(color=0x506600)
    embed.add_field(
        name="Commands:",
        value="\n".join([kick, ban, online, help, "", uptime])
    )

    await ctx.send(embed=embed)


@bot.command()
async def online(ctx: commands.Context) -> None:
    guild = bot.get_guild(sr)
    member_count = guild.member_count
    status_count = [0, 0, 0, 0, 0]  # online, offline, idle, dnd, invisible
    status_list = list(discord.Status)
    for member in guild.members:
        status_count[status_list.index(member.status)] += 1

    stats = discord.Embed(color=0x506600)
    stats.add_field(name=f"Total members: {member_count}", value="\n".join([
        f"<:online:572884944813031434>{status_count[0]}",
        f"<:idle:572884943898673174>{status_count[2]}",
        f"<:do_not_disturb:572884944016113666>{status_count[3]}",
        f"<:offline:572884944343269378>{status_count[1] + status_count[4]}"]))
    await ctx.send(embed=stats)


@bot.command()
async def ping(ctx: commands.Context):
    await ctx.send(f"Pong! ({round(bot.latency, 3) * 1000}ms)")


@bot.command()
@is_admin()
async def mute(ctx: commands.Context, user: str, *args: str) -> None:
    member = await get_member(ctx, bot.get_guild(sr), user)
    if member is None:
        await ctx.send(embed=await error_embed(f"Unknown user '{user}''"))

    n_seconds = parse_time("".join(*args))
    if n_seconds is None:
        await ctx.send(embed=await error_embed(f"Unknown time period '{' '.join(*args)}'"))

    await mute_member(member, n_seconds)
    await ctx.send(embed=await success_embed(f"Muted '{user}' for {str(datetime.timedelta(seconds=n_seconds))}"))

    desc = await log("mutes", {"Muted": member.name,
                               "Muted by": ctx.message.author.name,
                               "Time period": str(datetime.timedelta(seconds=n_seconds)),
                               "Timestamp": ctx.message.created_at.now().isoformat()})

    embed = discord.Embed(title="Muted member", description=desc, color=0xFFA500)
    channel = bot.get_channel(mute_log)
    await channel.send(embed=embed)


@bot.command()
@is_admin()
async def kick(ctx: commands.Context, user: str, *args: str) -> None:
    member = await get_member(ctx, bot.get_guild(sr), user)
    if member is None:
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
async def ban(ctx: commands.Context, user: str, *args: str) -> None:
    member = await get_member(ctx, bot.get_guild(sr), user)
    if member is None:
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
