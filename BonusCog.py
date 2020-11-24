# -*- coding: utf-8 -*-
"""
Created on Mon Oct 26 09:29:26 2020

@author: Max
"""
import re, discord, asyncio
from fuzzywuzzy import fuzz
from main import get_global_state, is_in_session, html_to_discord, Session, category_alias_to_id, subcat_alias_to_id, subcat_id_to_alias, get_bonuses, category_id_to_name, Args, get_bonus_command, isInt, get_session, get_tossups, get_tossup_command
from discord.ext import commands
from answerchecker import checkAnswer, removeDiacritics
from collections import namedtuple
from recordclass import recordclass
TossupReader = recordclass("TossupReader","message,tossupQuestion,tossupParts,index, number")
def setup(bot):
    bot.add_cog(QbCog(bot))




class BonusSessionState:
    def __init__(self):
        self.bonuses = []
        self.bonus_parts_answered = 0
        self.bonuses_answered = -1
        self.points = 0
        self.current_bonus = None
        self.prompting = False
        self.type = 'bonus'
    
class TossupSessionState:
    def __init__(self, insta):
        self.tossups = []
        self.tossups_answered = 0
        self.points = 0
        self.current_tossup = None
        self.prompting = False
        self.type = 'tossup'
        self.reading = None
        self.buzzed = False
        self.currently_reading = None
        self.insta = insta


class QbCog(commands.Cog):
    def skipMessage(self, ctx):
        state = get_global_state()
        state.skip_message = ctx.message
    
    def parseArgs(self, args, gt):
        print(args)
        difficulties = []
        categories = []
        subcategories = []
        years = []
        unresolved_args = []
        catorsub = ""
        for arg in args:
            resolved = False
            split = arg.split("-")
            #this does difficulty ranges or year ranges
            if len(split) > 1:
                if isInt(split[0]) and isInt(split[1]):
                    isDiff = (len(split[0])<=2 and len(split[1])<=2)
                    isYear = (len(split[0])==4 and len(split[1])==4)
                    if isDiff:
                        difficulties += list(range(int(split[0]),int(split[1])+1))
                        resolved=True
                    if isYear:
                        years+=list(range(int(split[0]),int(split[1])+1))
                        resolved=True
                '''try:
                    difficulties += list(range(int(split[0]), int(split[1])+1))
                    resolved = True
                except:
                    pass'''
            if arg.lower() in category_alias_to_id:
                categories.append(category_alias_to_id[arg.lower()])
                resolved = True
            if arg.lower() in subcat_alias_to_id:
                subcategories.append(subcat_alias_to_id[arg.lower()][0])
                resolved = True
            if isInt(arg):
                if len(arg)<=2:
                    difficulties.append(int(arg))
                    resolved=True
                if len(arg)==4:
                    years.append(int(arg))
                    resolved=True
            if not resolved:
                unresolved_args.append(arg)
        if subcategories:
            categories = []
            catorsub = "sub"
        if categories:
            catorsub = "cat"
        print(unresolved_args)
        difficulties, categories, subcategories, years = list(dict.fromkeys(difficulties)), list(dict.fromkeys(categories)), list(dict.fromkeys(subcategories)),list(dict.fromkeys(years))
        embed = discord.Embed(color=0x0000ff, title="Starting new {}".format(gt))
        if difficulties:
            embed.add_field(name="Difficulties", value=", ".join([str(difficulty) for difficulty in difficulties]))
        if categories:
            embed.add_field(name="Categories", value=", ".join([category_id_to_name[ids] for ids in categories]))
        if subcategories:
            embed.add_field(name="Subcategories", value=", ".join([subcat_id_to_alias[ids] for ids in subcategories]))
        if years:
            embed.add_field(name="Years", value=", ".join([str(year) for year in years]))
        if len(unresolved_args)>0:
            embed.add_field(name="Couldn't resolve args", value = ", ".join([f"`{arg}`" for arg in unresolved_args]))
        return Args(difficulties,categories,subcategories,years), catorsub, embed
    
    def splitString(self, n, text):
        text = text.split(' ')
        return [' '.join(text[i:i+n]) for i in range(0,len(text),n)]
    
    @commands.command()
    async def getcats(self, ctx):
        self.skipMessage(ctx)
        cats = list(category_alias_to_id.keys())
        await ctx.send("```"+", ".join(cats)+"```")
    
    @commands.command()
    async def getsubcats(self, ctx, *args):
        self.skipMessage(ctx)
        if args:
            for arg in args:
                if arg.lower() in category_alias_to_id:
                    message = "Subcategories for {}\n".format(arg)
                    ids = category_alias_to_id[arg.lower()]
                    subcats = []
                    for subcat in subcat_alias_to_id:
                        if subcat_alias_to_id[subcat][1] == ids:
                            subcats.append(subcat)
                    message+="```{}```".format(", ".join(subcats))
                    await ctx.send(message)
                else:
                    await ctx.send("Could not find category {}".format(arg))
                    
        else:
            subcats = list(subcat_alias_to_id.keys())
            await ctx.send("```"+", ".join(subcats)+"```")
    
    @commands.command()
    async def pk(self, ctx, *args):
        self.skipMessage(ctx)
        
        #await ctx.send(self.argsToSql(self.parseArgs(args)))
        if is_in_session(ctx.author):
            await ctx.send(f'{ctx.author} is already in a session.')
        else:
            #pass
            argstuple, catorsub, embed = self.parseArgs(args, "pk")
            new_session = Session(ctx, argstuple, catorsub, get_bonus_command(argstuple.difficulties, argstuple.categories, argstuple.subcategories, argstuple.years), BonusSessionState())
            get_global_state().sessions.append(new_session)
            await ctx.send(embed=embed)
            await self.send_question(ctx.channel, new_session)
    
    @commands.command()
    async def instatk(self, ctx, *args):
        self.skipMessage(ctx)
        if is_in_session(ctx.author):
            await ctx.send(f'{ctx.author} is already in a session')
            return
        argstuple, catorsub, embed = self.parseArgs(args, "instatk")
        new_session = Session(ctx, argstuple, catorsub, get_tossup_command(argstuple.difficulties, argstuple.categories, argstuple.subcategories, argstuple.years), TossupSessionState(True))
        get_global_state().sessions.append(new_session)
        await ctx.send(embed=embed)
        await self.send_question(ctx.channel, new_session)
    
    @commands.command()
    async def tk(self, ctx, *args):
        self.skipMessage(ctx)
        if is_in_session(ctx.author):
            await ctx.send(f'{ctx.author} is already in a session.')
        else:
            #pass
            argstuple, catorsub, embed = self.parseArgs(args, "tk")
            new_session = Session(ctx, argstuple, catorsub, get_tossup_command(argstuple.difficulties, argstuple.categories, argstuple.subcategories, argstuple.years), TossupSessionState(False))
            get_global_state().sessions.append(new_session)
            await ctx.send(embed=embed)
            await self.send_question(ctx.channel, new_session)
    
    @commands.command()
    async def end(self, ctx, *args):
        self.skipMessage(ctx)
        session = get_session(ctx.author)
        if session is not None:
            await self.stats(ctx)
            if session.session_state.type == "tossup" and session.session_state.insta==False:
                session.session_state.currently_reading.number += 1
            get_global_state().sessions.remove(session)
    
    @commands.command()
    async def stats(self, ctx):
        self.skipMessage(ctx)
        session = get_session(ctx.author)
        if session is not None:
            msg = discord.Embed(color=0xff0000, title="Stats")
            msg.set_thumbnail(url=ctx.author.avatar_url)
            if session.argstuple.difficulties:
                msg.add_field(name="Difficulty", value=", ".join([str(x) for x in session.argstuple.difficulties]))
            if session.catorsub == "cat":
                msg.add_field(name="Categories", value=", ".join([category_id_to_name[id] for id in session.argstuple.categories]))
            if session.session_state.type == "bonus":
                msg.add_field(name='Bonuses', value=str(session.session_state.bonuses_answered))
                msg.add_field(name='Points', value=str(session.session_state.points))
                ppb = str(session.session_state.points/session.session_state.bonuses_answered) if session.session_state.bonuses_answered>0 else 'N/A'
                msg.add_field(name="PPB", value=ppb)
            else:
                msg.add_field(name="Tossups", value=str(session.session_state.tossups_answered))
                msg.add_field(name="Points", value=str(session.session_state.points))
                ppb = str(session.session_state.points/session.session_state.tossups_answered) if session.session_state.tossups_answered>0 else 'N/A'
            await ctx.send(embed=msg)
    
    
    def checkAnswer(self, given, correct):
        return checkAnswer(given, correct)
    
    def generate_tossup_embed(self, avatar_url, display_name, tournament, level, text, number, cat, subcat):
        embed = discord.Embed(color=0x0000ff, title=f"{tournament} - level {level}")
        footer = f"Tossup {number}"
        if subcat != None:
            footer += " - "+subcat_id_to_alias[subcat]
        elif cat != None:
            footer += " - "+category_id_to_name[cat]
        embed.set_footer(text=footer)
        embed.description = html_to_discord(text)
        embed.set_author(name=f"for {display_name}", icon_url = avatar_url)
        return embed
    
    
    def get_tossup_part(self, session, index=None):
        if not index:
            index = session.session_state.currently_reading.index
        session_state = session.session_state
        tossups_answered = session_state.tossups_answered
        split = session_state.currently_reading.tossupParts
        n = index
        display_name = session.context.author.display_name
        avatar_url = session.context.author.avatar_url
        text = " ".join(split[0:n+1])
        tournament = session_state.current_tossup.tournament_name
        level = session_state.current_tossup.difficulty
        return self.generate_tossup_embed(avatar_url, display_name, tournament, level, text, tossups_answered, session_state.current_tossup.category, session_state.current_tossup.subcategory)
    
    async def read_tossup(self, session, channel):
        toEdit = await channel.send(embed=self.get_tossup_part(session))
        fullMessage = self.get_tossup_part(session, len(session.session_state.currently_reading.tossupParts))
        session.session_state.currently_reading.message = toEdit
        tossupNumber = session.session_state.tossups_answered
        while True:
            if not (session.session_state.prompting or session.session_state.buzzed):
                session.session_state.currently_reading.index += 1
                currently_reading = session.session_state.currently_reading
                if currently_reading.index >= len(session.session_state.currently_reading.tossupParts):
                    break
                if currently_reading.number != tossupNumber:
                    break
                await toEdit.edit(embed=self.get_tossup_part(session))
            
            await asyncio.sleep(1)
            
        await toEdit.edit(embed=fullMessage)

    async def send_question(self, channel, session):
        session_state = session.session_state
        if session_state.type == 'bonus':
            if len(session_state.bonuses) <= 1:
                try:
                    session_state.bonuses.extend(get_bonuses(session.sql))
                except Exception as e:
                    await channel.send("Error: "+str(e))
            if session_state.current_bonus is None or session_state.bonus_parts_answered == len(session_state.current_bonus[1]):
                try:
                    session_state.current_bonus = session_state.bonuses.pop()
                except IndexError:
                    await channel.send("No results found. Ending PK")
                    await self.end(session.context)
                    return
                session_state.bonuses_answered += 1
                leadin_msg = discord.Embed(color=0x00FF00)#, title=session_state.current_bonus[0].leadin)
                leadin_msg.add_field(name=f'{session_state.current_bonus[0].name} - level {session_state.current_bonus[0].difficulty}', value=f'{html_to_discord(session_state.current_bonus[0].leadin)}')
                leadin_msg.set_author(name=f' for {session.context.author.display_name}', icon_url=session.context.author.avatar_url)
                if session_state.current_bonus[0].subcategory != None:
                    leadin_msg.set_footer(text=subcat_id_to_alias[session_state.current_bonus[0].subcategory])
                elif session_state.current_bonus[0].category != None:
                    leadin_msg.set_footer(text=category_id_to_name[session_state.current_bonus[0].category])
                
                await channel.send(embed=leadin_msg)
                session_state.bonus_parts_answered = 0
            bonus_part = discord.Embed(color=0x0000ff)
            bonus_part.description = html_to_discord(session_state.current_bonus[1][session_state.bonus_parts_answered].formatted_text)
            bonus_part.set_author(name=f' for {session.context.author.display_name}',icon_url=session.context.author.avatar_url)
            footer = f"Part {session_state.bonus_parts_answered + 1}"
            
            bonus_part.set_footer(text=footer)
            await channel.send(embed=bonus_part)
        elif session_state.type == 'tossup':
            if len(session_state.tossups) <= 1:
                print("here")
                try:
                    session_state.tossups.extend(get_tossups(session.sql))
                    
                except Exception as e:
                    await channel.send("Error: "+str(e))
                    
            session_state.current_tossup = session_state.tossups.pop()
            if not session_state.insta:
                split = self.splitString(3, session_state.current_tossup.text)
                session_state.currently_reading = TossupReader(None,session_state.current_tossup.formatted_text, split, 0, session_state.tossups_answered)
                await self.read_tossup(session, channel)
            else:
                embed = self.generate_tossup_embed(session.context.author.avatar_url, session.context.author.display_name, session_state.current_tossup.tournament_name, session_state.current_tossup.difficulty, session_state.current_tossup.text, session_state.tossups_answered+1, session_state.current_tossup.category, session_state.current_tossup.subcategory)
                await channel.send(embed=embed)
            #tossup_msg = self.get_tossup_part(session)
            #toEdit = await channel.send(embed=tossup_msg)
            
            '''for i in range(len(split)):
                session_state.currently_reading.index += 1
                await toEdit.edit(embed=self.get_tossup_part(session))
                await asyncio.sleep(1)'''
    
                
            
            
    @commands.Cog.listener()
    async def on_message(self, message):
        if (get_global_state().skip_message is not None and message.id == get_global_state().skip_message.id) or message.content.startswith("_"):
            return
        session = get_session(message.author)
        if session is not None and session.context.channel == message.channel:
            if session.session_state.prompting:
                session.session_state.prompting = False
                if message.content.lower().startswith("y"):
                    session.session_state.points += 10
                if session.session_state.type == 'bonus':
                    session.session_state.bonus_parts_answered += 1
                if session.session_state.type == 'tossup':
                    session.session_state.tossups_answered += 1
                await self.send_question(message.channel, session)
                return

            if session.session_state.type == 'bonus':
                correctanswerformatted, correctanswer = session.session_state.current_bonus[1][session.session_state.bonus_parts_answered].formatted_answer, session.session_state.current_bonus[1][session.session_state.bonus_parts_answered].answer
                
                if message.content.lower() in ["idk","n"]:
                    incorrect_msg = discord.Embed(color=0xff0000)
                    incorrect_msg.add_field(name="Incorrect", value=html_to_discord(correctanswer))
                    incorrect_msg.set_author(name=f' for {session.context.author.display_name}', icon_url=session.context.author.avatar_url)
                    await message.channel.send(embed=incorrect_msg)
                    session.session_state.bonus_parts_answered += 1
                    await self.send_question(message.channel, session)
                    return
                
                if self.checkAnswer(message.content, correctanswer):
                    session.session_state.points+=10
                    session.session_state.bonus_parts_answered += 1
                    correct_msg = discord.Embed(color=0x0000ff)
                    correct_msg.add_field(name="Correct", value=html_to_discord(correctanswer))
                    await message.channel.send(embed=correct_msg)
                    await self.send_question(message.channel, session)
                else:
                    session.session_state.prompting=True
                    incorrect_msg = discord.Embed(color=0xff0000)
                    incorrect_msg.add_field(name="Were you correct? [y/n]", value=html_to_discord(correctanswer))
                    incorrect_msg.set_author(name=f' for {session.context.author.display_name}', icon_url=session.context.author.avatar_url)
                    await message.channel.send(embed=incorrect_msg)
            if session.session_state.type == 'tossup':
                correctanswerformatted, correctanswer = session.session_state.current_tossup.formatted_answer, session.session_state.current_tossup.answer
                if message.content.lower() in ["buzz","bz"] and session.session_state.buzzed==False:
                    print("here")
                    session.session_state.buzzed = True
                    buzz_msg = discord.Embed(color=0x0000ff, title=f"{message.author.display_name}'s buzz")
                    await message.channel.send(embed=buzz_msg)
                    return
                
                session.session_state.buzzed = False

                if message.content.lower() in ["idk","n"]:
                    incorrect_msg = discord.Embed(color=0xff0000)
                    incorrect_msg.add_field(name="Incorrect", value=html_to_discord(correctanswerformatted))
                    incorrect_msg.set_author(name=f' for {session.context.author.display_name}', icon_url=session.context.author.avatar_url)
                    session.session_state.tossups_answered += 1
                    await message.channel.send(embed=incorrect_msg)
                    await self.send_question(message.channel, session)
                    return
                
                if self.checkAnswer(message.content, correctanswer):
                    session.session_state.points += 10
                    session.session_state.tossups_answered += 1
                    correct_msg = discord.Embed(color=0x0000ff)
                    correct_msg.add_field(name="Correct", value=html_to_discord(correctanswerformatted))
                    await message.channel.send(embed=correct_msg)
                    await self.send_question(message.channel, session)
                else:
                    session.session_state.prompting = True
                    session.session_state.prompting=True
                    incorrect_msg = discord.Embed(color=0xff0000)
                    incorrect_msg.add_field(name="Were you correct? [y/n]", value=html_to_discord(correctanswerformatted))
                    incorrect_msg.set_author(name=f' for {session.context.author.display_name}', icon_url=session.context.author.avatar_url)
                    await message.channel.send(embed=incorrect_msg)
