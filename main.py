import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Greedy, Context

import os
from dotenv import load_dotenv
from typing import Literal, Optional, overload
from datetime import datetime
from pymongo import MongoClient

import bson
from bson import ObjectId

# .env imports
load_dotenv()
disc_token = os.getenv('DISCORD_TOKEN')

# Setup MongoDB
try:
    mdbClient = MongoClient('127.0.0.1', 27017)
    print("Connected successfully!!!")
except:
    print("Could not connect to MongoDB")


# create database for each guild on join
# delete database on guild leave

# Declare intents
intents = discord.Intents.none()
intents.message_content = True
intents.guild_messages = True
intents.members = True


def int_from_object_id(obj):
    return int(str(obj))


def object_id_from_int(n):
    s = str(n)
    s = '0' * (24 - len(s)) + s
    return bson.ObjectId(s)


# Word Class
# name - name string
# definitions - dictionary of definitions
# writeup - writeup on word
class Word:
    def __init__(self, id, name, pronounciation, definitions, writeup):
        self._id = id
        self.name = name
        self.definitions = definitions
        self.writeup = writeup
        self.pronounciation = pronounciation
        self.time_created = datetime.now()

    def fromdict(self, dict_in):
        self._id = int_from_object_id(dict_in.get('_id'))
        self.name = dict_in.get('name')
        self.definitions = dict_in.get('definitions')
        self.writeup = dict_in.get('writeup')
        self.pronounciation = dict_in.get('pronounciation')
        self.time_created = dict_in.get('time_created')

    def todict(self):
        ret = {
            '_id': object_id_from_int(self._id),
            'name': self.name,
            'pronounciation': self.pronounciation,
            'definitions': self.definitions,
            'writeup': self.writeup,
            'time_created': self.time_created
        }
        return ret

    @property
    def id(self):
        return self._id


# Temporary testing variables
abstract_word = Word(id=3, name="Abstract", pronounciation="ˈæbˌstɹækt", definitions={
    "Adjective": "Disassociated from any specific instance",
    "Noun": "A summary of points usually presented in skeletal form",
    "Verb": "To remove or separate"
},
                 writeup="Late 14c., originally in grammar (in reference to nouns that do not name concrete things), "
                         "from Latin abstractus \"drawn away,\" past participle of abstrahere \"to drag away, detach, "
                         "pull away, divert,\" also used figuratively; from assimilated form of ab \"off, away from\" "
                         "(see ab-) + trahere \"to draw\" (from PIE root *tragh- \"to draw, drag, move;\" see tract (n.1))."
                         "\n\nThe meaning in philosophy, \"withdrawn or separated from material objects or practical matters\" "
                         "(opposed to concrete) is from mid-15c. That of \"difficult to understand, abstruse\" is from "
                         "c. 1400. \n\nIn the fine arts, \"characterized by lack of representational qualities\" by 1914; "
                         "it had been a term at least since 1847 for music without accompanying lyrics. "
                         "Abstract expressionism as an American-based uninhibited approach to art exemplified by "
                         "Jackson Pollock is from 1952, but the term itself had been used in the 1920s of Kandinsky and others.")

word_list = [Word(id=1, name="Contrast", pronounciation="eh", definitions={"A": "lorum ipsum"}, writeup="dolor sit amet"),
             Word(id=2, name="Flippant", pronounciation="eh", definitions={"A": "lorum ipsum"}, writeup="dolor sit amet"),
             abstract_word]


def addWord(name, pronounciation, definitions, writeup):
    new_id = word_list[-1].id + 1
    word = Word(new_id, name, pronounciation, definitions, writeup)
    word_list.append(word)


addWord(name='jettison',
        pronounciation='ˈdʒɛt ə sən, -zən',
        definitions={
            'Noun': 'The act of casting goods from a vessel or aircraft to lighten or stabilize it.',
            'Verb': 'To cast (goods) overboard in order to lighten a vessel or aircraft or to improve its stability in an emergency.'
        },
        writeup='1848, to throw overboard," especially to save a ship in danger, from jettison (n.) '
                      '"act of throwing overboard" to lighten a ship. This noun was an 18c. Marine '
                      'Insurance writers\' restoration of the earlier form and original sense of the '
                      '15c. word that had become jetsam, probably because jetsam had taken on a sense '
                      'of "things cast overboard" and an unambiguous word was needed for "act of '
                      'casting things overboard." \n\nMiddle English jetteson (n.) "act of throwing overboard" '
                      'is from Anglo-French getteson, Old French getaison "act of throwing (goods overboard)," '
                      'especially to lighten a ship in distress, from Late Latin iactationem (nominative iactatio) '
                      '"a throwing, act of throwing," noun of action from past participle stem of iactare "to throw, '
                      'toss about" (from PIE root *ye- "to throw, impel"). Related: Jettisoned.')

word_list[3].time_created = datetime(2022, 12, 28, 23, 55, 59, 342380)


# Basic bot functionality/setup
class MyBot(commands.Bot):
    async def on_ready(self):
        print('Logged on as', self.user)
        activity = discord.CustomActivity(name="Word of the week: " + word_list[-1].name, emoji="💡")
        game = discord.Game(name="With Words")
        await bot.change_presence(status=discord.Status.online, activity=game)
        await bot.add_cog(Points())
        await bot.add_cog(WordOfTheWeek())
        await bot.add_cog(Maintenance())


# Timed messages and word descriptions
class WordOfTheWeek(commands.Cog):
    @app_commands.rename(word_str='word')
    @app_commands.command(description="Display the word of the week")
    async def word(self, ctx: Context, word_str: Optional[str] = None):
        if word_str is None:
            w = word_list[-1]
        else:
            w = next((word for word in word_list if word.name.lower() == word_str.lower()), [word_list[-1]])

        if not isinstance(w, Word):
            await ctx.response.send_message(ephemeral=True, content=f"{word_str} is not a current or previous word of the week.")
            return

        link = "https://www.merriam-webster.com/dictionary/" + w.name.lower()
        embed = discord.Embed(title=f"{w.name}  -  [{w.pronounciation}]",
                              colour=discord.Colour(0x5e7a7c),
                              description=f"_Find this word on [merriam-webster.]({link})_",
                              timestamp=datetime.now())

        embed.set_author(name=bot.user.name, icon_url=bot.user.avatar)
        embed.set_footer(text="Word of the Week", icon_url=bot.user.avatar)

        # Definitions loop
        for (k, v) in w.definitions.items():
            embed.add_field(name="**"+k+"**", value=v)

        embed.add_field(name="Etymology", value=w.writeup + "\n\n_sourced from etymonline.com and dictionaryapi.dev_", inline=False)

        await ctx.response.send_message(ephemeral=True, embed=embed)


# Point tracking, leaderboard updates nad requests
class Points(commands.Cog):
    @commands.Cog.listener()
    async def on_message(self, message):
        # don't respond to ourselves
        if message.author == bot.user:
            return

        words = message.content.lower()
        if words.find(word_list[-1].name.lower()) != -1:
            await message.add_reaction("💡")
        for w in word_list:
            if words.find(w.name.lower()) != -1:
                await message.add_reaction("💡")


# Command syncing and general maintenance
class Maintenance(commands.Cog):
    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def sync(
            self, ctx: Context, guilds: Greedy[discord.Object], spec: Optional[Literal["~", "*", "^"]] = None) -> None:
        if not guilds:
            if spec == "~":
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                ctx.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "^":
                ctx.bot.tree.clear_commands(guild=ctx.guild)
                await ctx.bot.tree.sync(guild=ctx.guild)
                synced = []
            else:
                synced = await ctx.bot.tree.sync()

            await ctx.send(
                f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
            )
            return

        ret = 0
        for guild in guilds:
            try:
                await ctx.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                ret += 1

        await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")

    @commands.command(name="createDB")
    @commands.guild_only()
    @commands.is_owner()
    async def create_database(self, ctx: Context):
        print(ctx.guild.id)
        guilds = mdbClient['guilds']
        guilddb = guilds[str(ctx.guild.id)]
        if guilddb.find({'_id': object_id_from_int(0)}) is None:
            guilddb.insert_one({'_id': object_id_from_int(0), 'time_created': datetime.now()})
        async for m in ctx.guild.fetch_members(limit=None):
            if guilddb.find({'_id': object_id_from_int(m.id)}) is None:
                print(f"  {m.id}")
                member_unit = {
                    '_id': object_id_from_int(m.id),
                    'points': 0
                }
                guilddb.insert_one(member_unit)
        print(guilddb)

    @commands.command(name="createWordDB")
    @commands.guild_only()
    @commands.is_owner()
    async def word_database(self, ctx: Context):
        gwords = mdbClient.words[str(ctx.guild.id)]
        bwords = mdbClient.words.default
        guilds = mdbClient['guilds']
        guilddb = guilds[str(ctx.guild.id)]
        for w in word_list:
            if gwords.find({'_id': object_id_from_int(w.id)}) is None:
                if w.time_created > guilddb.find_one({'_id': object_id_from_int(0)}).get('time_created'):
                    gwords.insert_one(w.todict())
            if bwords.find({'_id': object_id_from_int(w.id)}) is None:
                bwords.insert_one(w.todict())


# Instantiate & Run Bot
bot = MyBot(command_prefix=commands.when_mentioned_or('>'), description="Word Of The Week Bot", intents=intents)
bot.run(token=disc_token)
