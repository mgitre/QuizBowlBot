# -*- coding: utf-8 -*-
"""
Created on Sun Oct 25 12:19:01 2020

@author: Max
"""

import psycopg2
#from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from collections import namedtuple
from discord.ext import commands
import json

with open("env.json","r") as f:
    env = json.load(f)


maxBonuses = 15


Bonus = namedtuple("Bonus","id,leadin,name,difficulty,category,subcategory")
BonusPart = namedtuple("BonusPart","formatted_text, formatted_answer, answer")
Session = namedtuple("Session","context,argstuple,catorsub,sql,session_state")
Args = namedtuple("Args","difficulties,categories,subcategories,years")
Tossup = namedtuple("Tossup","formatted_text, formatted_answer, difficulty, tournament_name, text, answer, category, subcategory")

category_alias_to_id = {
    'geo': 20,
    'geography': 20,
    'hist': 18,
    'history': 18,
    'lit': 15,
    'literature': 15,
    'm': 14,
    'myth': 14,
    'p': 25,
    'philo': 25,
    'r': 19,
    'religion': 19,
    'sci': 17,
    'science': 17,
    'ss': 22,
    'socialscience': 22,
    'trash': 16,
    'ce': 26,
    'currentevents': 26,
    'fa': 21,
    'finearts': 21
}

subcat_alias_to_id ={
 'euro_lit': (1, 15),
 'visual_art': (2, 21),
 'american_lit': (4, 15),
 'chem': (5, 17),
 'british_history': (6, 18),
 'auditory_art': (8, 21),
 'misc_sci': (10, 17),
 'american_history': (13, 18),
 'biology': (14, 17),
 'classical_history': (16, 18),
 'physics': (18, 17),
 'world_history': (20, 18),
 'british_lit': (22, 15),
 'comp_sci': (23, 17),
 'european_history': (24, 18),
 'fine_arts_other': (25, 21),
 'math': (26, 17),
 'audiovisual_art': (27, 21),
 'misc_history': (28, 18),
 'misc_lit': (29, 15),
 'classical_lit': (30, 15),
 'american_religion': (31, 19),
 'american_trash': (32, 16),
 'american_myth': (33, 14),
 'american_ss': (34, 22),
 'fine_arts_american': (35, 21),
 'american_sci': (36, 17),
 'world_sci': (37, 17),
 'american_geo': (38, 20),
 'american_phil': (39, 25),
 'america_current_events': (40, 26),
 'misc_current_events': (42, 26),
 'fine_arts_world': (43, 21),
 'world_geo': (44, 20),
 'fine_arts_british': (45, 21),
 'indian_myth': (46, 14),
 'chinese_myth': (47, 14),
 'east_asian_myth': (49, 14),
 'japanese_myth': (48, 14),
 'fine_arts_european': (50, 21),
 'east_asian_religion': (51, 19),
 'east_asian_phil': (52, 25),
 'video_games': (53, 16),
 'misc_myth': (54, 14),
 'sports': (55, 16),
 'economics': (56, 22),
 'christianity': (57, 19),
 'greco_roman_myth': (58, 14),
 'misc_trash': (59, 16),
 'misc_ss': (60, 22),
 'classical_phil': (61, 25),
 'world_lit': (12, 15),
 'misc_religion': (62, 19),
 'norse_myth': (63, 14),
 'political_science': (64, 22),
 'egyptian_myth': (65, 14),
 'european_phil': (66, 25),
 'music': (67, 16),
 'islam': (68, 19),
 'judaism': (69, 19),
 'television': (70, 16),
 'psychology': (71, 22),
 'movies': (72, 16),
 'sociology': (73, 22),
 'misc_phil': (74, 25),
 'linguistics': (75, 22),
 'anthropology': (76, 22),
 'opera': (77, 21)
 }

subcat_id_to_alias = {
 1: 'Literature European',
 2: 'Fine Arts Visual',
 4: 'Literature American',
 5: 'Science Chemistry',
 6: 'History British',
 8: 'Fine Arts Auditory',
 10: 'Science Other',
 13: 'History American',
 14: 'Science Biology',
 16: 'History Classical',
 18: 'Science Physics',
 20: 'History World',
 22: 'Literature British',
 23: 'Science Computer Science',
 24: 'History European',
 25: 'Fine Arts Other',
 26: 'Science Math',
 27: 'Fine Arts Audiovisual',
 28: 'History Other',
 29: 'Literature Other',
 30: 'Literature Classical',
 31: 'Religion American',
 32: 'Trash American',
 33: 'Mythology American',
 34: 'Social Science American',
 35: 'Fine Arts American',
 36: 'Science American',
 37: 'Science World',
 38: 'Geography American',
 39: 'Philosophy American',
 40: 'Current Events American',
 42: 'Current Events Other',
 43: 'Fine Arts World',
 44: 'Geography World',
 45: 'Fine Arts British',
 46: 'Mythology Indian',
 47: 'Mythology Chinese',
 49: 'Mythology Other East Asian',
 48: 'Mythology Japanese',
 50: 'Fine Arts European',
 51: 'Religion East Asian',
 52: 'Philosophy East Asian',
 53: 'Trash Video Games',
 54: 'Mythology Other',
 55: 'Trash Sports',
 56: 'Social Science Economics',
 57: 'Religion Christianity',
 58: 'Mythology Greco-Roman',
 59: 'Trash Other',
 60: 'Social Science Other',
 61: 'Philosophy Classical',
 12: 'Literature World',
 62: 'Religion Other',
 63: 'Mythology Norse',
 64: 'Social Science Political Science',
 65: 'Mythology Egyptian',
 66: 'Philosophy European',
 67: 'Trash Music',
 68: 'Religion Islam',
 69: 'Religion Judaism',
 70: 'Trash Television',
 71: 'Social Science Psychology',
 72: 'Trash Movies',
 73: 'Social Science Sociology',
 74: 'Philosophy Other',
 75: 'Social Science Linguistics',
 76: 'Social Science Anthropology',
 77: 'Fine Arts Opera'}

category_id_to_name = {14: 'Mythology',
 15: 'Literature',
 16: 'Trash',
 17: 'Science',
 18: 'History',
 19: 'Religion',
 20: 'Geography',
 21: 'Fine Arts',
 22: 'Social Science',
 25: 'Philosophy',
 26: 'Current Events'}

client = commands.Bot("-")

years_to_ids = {2014: [29, 19, 8, 65, 12, 16, 33, 93, 59, 46, 14, 38, 20, 43, 67, 47, 52, 21, 70, 64, 262, 187, 238, 217, 237, 211, 215, 200, 275, 277, 301, 208, 222, 63, 250, 362], 2013: [30, 26, 22, 15, 2, 10, 45, 76, 49, 37, 54, 66, 11, 17, 53, 81, 69, 13, 263, 239, 206, 247, 214, 201, 283, 302, 276, 225, 221, 41, 308, 34, 36, 230, 359, 360], 2012: [23, 68, 3, 25, 7, 42, 5, 60, 50, 18, 31, 83, 48, 72, 1, 79, 212, 205, 248, 267, 244, 258, 94, 303, 292, 274, 299, 295, 224, 220, 229, 40, 336, 32, 264], 2015: [92, 96, 27, 28, 75, 87, 95, 98, 261, 227, 252, 245, 82, 249, 285, 218, 313, 304, 335, 287, 246, 270, 307, 334, 309, 350, 351, 352, 353, 354, 268], 2011: [4, 24, 9, 80, 39, 143, 88, 57, 118, 117, 102, 116, 119, 154, 101, 203, 122, 153, 235, 282, 207, 51, 71, 273, 289, 293, 312, 223, 228, 290, 103, 104, 105, 130, 107, 106, 138, 108, 127, 137, 265], 2009: [55, 144, 61, 112, 140, 177, 184, 134, 181, 169, 188, 163, 232, 179, 162, 189, 190, 266, 149, 161, 172, 186, 142, 183, 231, 297, 271, 310, 332, 150, 296, 113, 135, 156, 136, 141, 155, 62], 2008: [58, 84, 166, 145, 191, 180, 210, 192, 193, 195, 196, 216, 281, 194, 219, 173, 178, 164, 114, 176, 115, 165], 2010: [73, 85, 139, 121, 109, 111, 110, 120, 129, 148, 158, 151, 133, 131, 123, 132, 126, 125, 174, 100, 167, 168, 157, 147, 152, 159, 170, 175, 124, 298, 319, 329, 291, 317, 226, 128, 146, 160, 97], 2017: [182, 316, 240, 288, 326, 314, 328, 305, 300, 321, 315, 259, 256, 306, 185, 342, 324, 346, 344, 279, 348, 349, 355, 358, 361, 363, 365, 366, 367, 368, 372, 378, 381, 391], 2016: [255, 260, 171, 99, 209, 254, 272, 278, 284, 89, 91, 253, 322, 330, 311, 325, 280, 269, 318, 294, 286, 337, 320, 341, 343, 345, 357, 257], 2007: [242, 197], 2005: [233], 2006: [198], 2018: [364, 369, 370, 371, 373, 374, 375, 376, 377, 379, 380, 382, 383, 384, 385, 386, 387, 388, 389, 390, 392, 396, 398, 404, 406, 408, 395], 2019: [393, 394, 399, 401, 402, 403, 400, 405, 407, 409, 410, 412, 414, 415, 418, 419], 2020: [411, 413, 416, 417]}

def getConnection():
    return psycopg2.connect(database=env["database"],user=env['user'],password=env['password'],host=env['host'],port=env['port'])

def get_bonus_command(difficulties=[], categories=[], subcategories=[], years=[]):
    sqlstring = "SELECT id, leadin, tournament_name, difficulty, category_id, subcategory_id FROM bonusesformatted"

    sqlConditions = []
    if difficulties:
        sqlConditions.append("difficulty in ("+",".join([str(diff) for diff in difficulties])+")")
    if categories:
        sqlConditions.append("category_id in ("+",".join([str(cat) for cat in categories])+")")
    if subcategories:
        sqlConditions.append("subcategory_id in ("+",".join([str(subcat) for subcat in subcategories])+")")
    if years:
        yearIds = []
        for year in years:
            yearIds+=years_to_ids[year]
        sqlConditions.append("tournament_id in ("+",".join([str(yearid) for yearid in yearIds])+")")
    if sqlConditions:
        sqlstring += " WHERE "
    return sqlstring + " AND ".join(sqlConditions)  + " ORDER BY RANDOM() LIMIT {}".format(maxBonuses)


def get_tossup_command(difficulties=[], categories=[], subcategories=[], years=[]):
    sqlstring = "SELECT formatted_text, formatted_answer, difficulty, tournament_name, text, answer, category_id, subcategory_id FROM tossupsformatted"
    sqlConditions = []
    if difficulties:
        sqlConditions.append("difficulty in ("+",".join([str(diff) for diff in difficulties])+")")
    if categories:
        sqlConditions.append("category_id in ("+",".join([str(cat) for cat in categories])+")")
    if subcategories:
        sqlConditions.append("subcategory_id in ("+",".join([str(subcat) for subcat in subcategories])+")")
    if years:
        yearIds = []
        for year in years:
            yearIds+=years_to_ids[year]
        sqlConditions.append("tournament_id in ("+",".join([str(yearid) for yearid in yearIds])+")")
    if sqlConditions:
        sqlstring += " WHERE "
    return sqlstring + " AND ".join(sqlConditions) + " ORDER BY RANDOM() LIMIT {}".format(maxBonuses)
        

def get_tossups(sqlstring, conn=getConnection()):
    #tossups = []
    cursor = conn.cursor()
    cursor.execute(sqlstring)
    return list(map(Tossup._make, cursor.fetchall()))

def isInt(var):
    try:
        int(var)
        return True
    except ValueError:
        return False


def get_bonuses(sqlstring, conn=getConnection()):
    bonuses = []
    cursor = conn.cursor()
    cursor.execute(sqlstring)
    for bonus in map(Bonus._make, cursor.fetchall()):
        cursor.execute(f"SELECT formatted_text, formatted_answer, answer FROM bonus_parts WHERE bonus_id={bonus.id} ORDER BY number ASC")
        bonus_parts = list(map(BonusPart._make, cursor.fetchall()))
        if len(bonus_parts) == 0:
            continue
        bonuses.append((bonus, bonus_parts))
    return bonuses


def get_session(author):
    for session in get_global_state().sessions:
        if session.context.author == author:
            return session
    return None


def html_to_discord(html_text):
    html_text = html_text.replace('<em>', '*').replace('<b>', '**').replace('<u>', '__').replace('<strong>', '**').replace('&lt;', '<')
    html_text = html_text.replace('</em>', '*').replace('</b>', '**').replace('</u>', '__').replace('</strong>', '**').replace('&gt;', '>')
    return html_text


def get_global_state():
    global state
    return state


def is_in_session(author):
    return not all([author != session.context.author for session in get_global_state().sessions])

class GlobalState:
    sessions = []
    skip_message = None


state = GlobalState()


class UserSession:
    def __init__(self, ctx):
        self.ctx = ctx
        self.user_id = ctx.author.id

client.load_extension("BonusCog")
client.run(env['token'])
