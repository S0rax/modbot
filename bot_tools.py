import discord
from discord.ext import commands

import re
import json
import os


def _get_from_guilds(bot, getter, argument):
    result = None
    for guild in bot.guilds:
        result = getattr(guild, getter)(argument)
        if result:
            return result
    return result


async def get_member(ctx, guild, argument):
    bot = ctx.bot
    match = re.match(r'([0-9]{15,21})$', argument) or re.match(r'<@!?([0-9]+)>$', argument)
    # guild = ctx.guild
    result = None
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
    pass


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
