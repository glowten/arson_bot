from __future__ import absolute_import
from utils import *
import os
import discord
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--token", type=str, required=True)

args = parser.parse_args()

token = args.token

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
client = discord.Client(intents=intents)

player_save_trigger = '!psave'
user_save_trigger = '!usave'

@client.event
async def on_ready():
    for guild in client.guilds:
        print(
            f"{client.user} is connected to the following servers:\n"
            f"{guild.name}(id: {guild.id})"
        )

@client.event
async def on_message(message):
    try:
        if message.author == client.user:
            return
        if message.content.startswith(player_save_trigger) or message.content.lower().startswith('!psave'):
            store_player(message.author.id, message.guild.id, message.content[7:])
            await message.channel.send('Player stored')
        if message.content.startswith(user_save_trigger):
            store_username(message.author.id, message.guild.id, message.content[7:])
            await message.channel.send('User stored')

        stats = process_stats(message)
        if not stats is None:
            await message.channel.send(embed=stats)

        arson_msg = arson(message)
        if not arson_msg is None:
            await message.channel.send(arson_msg)

        cube_msg = cube(message)
        cube_msg = check_message(cube_msg)
        if not cube_msg is None:
            await message.channel.send(cube_msg)

        casino_msg = casino(message)
        if not casino_msg is None:
            await message.channel.send(str(casino_msg))

        ge_msg = geify(message)
        ge_msg = check_message(ge_msg)
        if not ge_msg is None:
            await message.channel.send(ge_msg)

        floosh_msg = floosh(message)
        if not floosh_msg is None:
            await message.channel.send(floosh_msg)

        roster_msg = check_roster(message)
        if not roster_msg is None:
            for out_msg in roster_msg:
                await message.channel.send(out_msg)

    except (discord.errors.HTTPException, TooLongException) as e:
        print('this broke', message.content)
        print(e)
        await message.channel.send("don't break me please <:devilssadge:813211885750452244>")


client.run(token)