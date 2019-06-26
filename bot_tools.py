import discord
import datetime
import asyncio
from discord.ext import commands

import re
import json
import os

mute_cache = []
credentials = None
bot = None
mute_log = None


def setup(creds, client, mutes) -> None:
    global credentials, bot, mute_log
    credentials = creds
    bot = client
    mute_log = mutes


def _get_from_guilds(bot, getter, argument):
    result = None
    for guild in bot.guilds:
        result = getattr(guild, getter)(argument)
        if result:
            return result
    return result


async def get_member(ctx, guild, argument):
    match = re.match(r'([0-9]{15,21})$', argument) or re.match(r'<@!?([0-9]+)>$', argument)
    if match is None:
        # not a mention...
        if guild:
            result = guild.get_member_named(argument)
        else:
            result = _get_from_guilds(bot, 'get_member_named', argument)
    else:
        user_id = int(match.group(1))
        if guild:
            result = guild.get_member(user_id)
        else:
            result = _get_from_guilds(bot, 'get_member', user_id)

    return result


async def mute_member(member: discord.Member, n_seconds: int) -> None:
    guild = discord.utils.get(bot.guilds, id=credentials["server_main"])
    role = discord.utils.get(guild.roles, id=credentials["mute_role"])
    await member.add_roles(role)
    mute_cache.append((member, datetime.datetime.now(), n_seconds))


async def check_mutes() -> None:
    global mute_cache
    while True:
        guild = discord.utils.get(bot.guilds, id=credentials["server_main"])
        role = discord.utils.get(guild.roles, id=credentials["mute_role"])

        removed = []
        for index, (member, timestamp, n_seconds) in enumerate(mute_cache):
            if (datetime.datetime.now() - timestamp).seconds > n_seconds:
                await member.remove_roles(role)
                removed.append(index)
                desc = await log("mutes", {"Unmuted": member.name,
                                           "Timestamp": datetime.datetime.now().isoformat()})

                embed = discord.Embed(title="Unmuted member", description=desc, color=0x00CC00)
                channel = bot.get_channel(mute_log)
                await channel.send(embed=embed)
            else:
                try:
                    await member.add_roles(role)
                except discord.errors.NotFound as e:
                    pass

        mute_cache = [mute for index, mute in enumerate(mute_cache) if index not in removed]

        await asyncio.sleep(1)


async def log(logname, data):
    json_data = json.dumps(data)
    with open(os.path.join("logs", f"{logname}.log"), "a") as logfile:
        logfile.write(json_data + "\n")
    desc = "\n".join([f"**{k}**: {v}" for k, v in data.items()])
    if len(desc) > 1900:
        if "ID" in data:
            return f"**ID**: {data['ID']}" \
                f"This log is too large to fit on discord." \
                f"If you want to view it, \nsend me the ID and I can check the bot logs"

        else:
            return f"This log is too large to fit on discord"
    else:
        return desc


async def error_embed(message):
    return discord.Embed(description=f":x: Error: {message}", color=0xCC0000)


async def success_embed(message):
    return discord.Embed(description=f":white_check_mark: {message}", color=0x00CC00)
