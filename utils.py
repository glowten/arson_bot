import os
import urllib.request
import urllib.error
import json
import discord
import pandas as pd
pd.options.display.float_format = '{:,.2f}'.format

db_loc = os.path.join(os.getcwd(), 'db_files')
FANTASY = 'fantasy'
POINTS = 'points'
PTs = 'pts'

fantasy_trigger = '!f'
stats_trigger = '!p'
pt_trigger = '!tpe'

user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
headers = {'User-Agent': user_agent}


def get_logo(franchise_name):
    return f'https://simulationhockey.com/images/smilies/{franchise_name.lower()}.png'

team_dict = {
    'BUF': get_logo('stampede'),
    'CHI': get_logo('syndicate'),
    'HAM': get_logo('steelhawks'),
    'TOR': get_logo('stars'),
    'MAN': get_logo('rage'),
    'NEW': get_logo('wolfpack'),
    'TBB': get_logo('barracuda'),
    'BAP': get_logo('platoon'),
    'CGY': get_logo('dragons'),
    'EDM': get_logo('blizzard'),
    'MIN': get_logo('monarchs'),
    'WPG': get_logo('aurora'),
    'SFP': get_logo('pride'),
    'NOL': get_logo('specters'),
    'TEX': get_logo('renegades'),
    'ATL': get_logo('inferno'),
    'SEA': get_logo('argonauts'),
}

shl_player_dict = []
smjhl_player_dict = []

def process_stats(msg):
    player = None
    if msg.content.lower().startswith(stats_trigger):
        if msg.content.lower() == stats_trigger:
            p = get_player(msg.author.id, msg.guild.id)
            if p is None:
                return not_found('Player not saved, please save with !psave {PLAYER_NAME}')
            player = p
        elif msg.content[2] == ' ':
            player = msg.content[3:]
        else:
            return None
        try:
            stats_skater = get_stats_skater(player)
            if not stats_skater is None:
                return stats_skater
            stats_goalie = get_stats_goalie(player)
            if not stats_goalie is None:
                return stats_goalie
            return not_found(f'Player not found: {player}')
        except urllib.error.HTTPError as err:
            return error_embed(err)

    return None

def arson(msg):
    if msg.content.lower() == '!arson':
        return '🔥 🔥 🔥'
    if msg.content.lower() == '!burnitdown':
        return '<a:atlcatjam:775600939935334430> <a:atlcatjam:775600939935334430> <a:atlcatjam:775600939935334430>'
    if msg.content.lower() == '!gabe':
        return '<:bigmadge:834516093405757520>'

    return None

def casino(msg):
    if msg.content.lower() == '!casino':
        casino_lines = pd.read_csv(os.path.join(db_loc, 'casino.csv'))
        api_link = 'https://index.simulationhockey.com/api/v1/standings'
        request = urllib.request.Request(api_link, headers=headers)
        stan = json.loads(urllib.request.urlopen(request).read())
        df = []
        total_games = 66
        for team in stan:
            team_dict = {}
            team_dict['team'] = team['abbreviation']
            team_dict['wins'] = int(team['wins'])
            team_dict['gp'] = int(team['gp'])
            team_dict['trend'] = team_dict['wins'] + ((total_games - team_dict['gp']) * float(team_dict['wins']) / team_dict['gp'])
            df.append(pd.DataFrame([team_dict]))
        df = pd.concat(df)
        casino_lines = pd.merge(casino_lines, df, on='team')
        casino_lines['projected'] = 'EVEN'
        casino_lines.loc[casino_lines['trend'] > casino_lines['line'], 'projected'] = 'OVER'
        casino_lines.loc[casino_lines['trend'] == casino_lines['line'], 'projected'] = 'EVEN'
        casino_lines.loc[casino_lines['trend'] < casino_lines['line'], 'projected'] = 'UNDER'
        casino_lines.loc[casino_lines['wins'] > casino_lines['line'], 'projected'] = 'OVER CONFIRMED'
        casino_lines.loc[casino_lines['wins'] + (total_games - casino_lines['gp']) < casino_lines['line'],
                         'projected'] = 'UNDER CONFIRMED'
        return '```' + casino_lines[['team', 'gp', 'wins', 'line', 'trend', 'projected']].to_string(index=False) + '```'
    return None


def cube(msg):
    if msg.content.lower() == '!cube':
        return format_cube('<a:atlcatjam:775600939935334430>')
    if msg.content.lower().startswith('!cube') and msg.content[5] == ' ':
        return format_cube(msg.content[6:])
    return None

def format_cube(emote):
    l1 = f'..............{emote}{emote} {emote} {emote}'
    l2 = f'       {emote}              {emote} {emote}'
    l3 = f'{emote} {emote} {emote} {emote}       {emote}'
    l4 = f'{emote}               {emote}       {emote}'
    l5 = f'{emote}               {emote} {emote}'
    l6 = f'{emote} {emote} {emote} {emote}'
    return '\n'.join([l1, l2, l3, l4, l5, l6])

def not_found(thing):
    return discord.Embed(title='Not Found', description=thing)

def error_embed(err):
    embed = discord.Embed(title='Error', description=str(err))
    embed.add_field(name='Oh no what did you do', value='Please try again')

def get_stats_skater(player_name):
    player_name = player_name.lower()
    # SHL playoffs
    api_link = 'https://index.simulationhockey.com/api/v1/players/stats?type=playoffs'
    request = urllib.request.Request(api_link, headers=headers)
    playoff_stats = json.loads(urllib.request.urlopen(request).read())

    # SHL reg season
    api_link = 'https://index.simulationhockey.com/api/v1/players/stats'
    request = urllib.request.Request(api_link, headers=headers)
    reg_stats = json.loads(urllib.request.urlopen(request).read())

    if playoff_stats[0]['season'] == reg_stats[0]['season']:
        stats = playoff_stats
    else:
        stats = reg_stats

    for i, p in enumerate(stats):
        if p['name'].lower() == player_name:
            return format_skater_stats(p)


    # SMJHL playoffs
    api_link = 'https://index.simulationhockey.com/api/v1/players/stats?league=1&type=playoffs'
    request = urllib.request.Request(api_link, headers=headers)
    playoff_stats = json.loads(urllib.request.urlopen(request).read())

    # SMJHL reg season
    api_link = 'https://index.simulationhockey.com/api/v1/players/stats?league=1'
    request = urllib.request.Request(api_link, headers=headers)
    reg_stats = json.loads(urllib.request.urlopen(request).read())

    if playoff_stats[0]['season'] == reg_stats[0]['season']:
        stats = playoff_stats
    else:
        stats = reg_stats

    for i, p in enumerate(stats):
        if p['name'].lower() == player_name:
            return format_skater_stats(p)

    return None

def get_stats_goalie(player_name):
    player_name = player_name.lower()
    # SHL playoffs
    api_link = 'https://index.simulationhockey.com/api/v1/goalies/stats?type="playoffs"'
    request = urllib.request.Request(api_link, headers=headers)
    stats = json.loads(urllib.request.urlopen(request).read())
    playoff_p = None
    for i, p in enumerate(stats):
        if p['name'].lower() == player_name and p['gamesPlayed'] > 0:
            playoff_p = p
            break
    # SHL reg season
    api_link = 'https://index.simulationhockey.com/api/v1/goalies/stats'
    request = urllib.request.Request(api_link, headers=headers)
    stats = json.loads(urllib.request.urlopen(request).read())
    for i, p in enumerate(stats):
        if p['name'].lower() == player_name:
            if playoff_p is not None and p['season'] == playoff_p['season']:
                return format_goalie_stats(playoff_p)
            return format_goalie_stats(p)

    # SMJHL playoffs
    api_link = 'https://index.simulationhockey.com/api/v1/goalies/stats?league=1&type="playoffs"'
    request = urllib.request.Request(api_link, headers=headers)
    stats = json.loads(urllib.request.urlopen(request).read())
    for i, p in enumerate(stats):
        if p['name'].lower() == player_name and p['gamesPlayed'] > 0:
            playoff_p = p
            break
    # SMJHL reg season
    api_link = 'https://index.simulationhockey.com/api/v1/goalies/stats?league=1'
    request = urllib.request.Request(api_link, headers=headers)
    stats = json.loads(urllib.request.urlopen(request).read())
    for i, p in enumerate(stats):
        if p['name'].lower() == player_name:
            if playoff_p is not None and p['season'] == playoff_p['season']:
                return format_goalie_stats(playoff_p)
            return format_goalie_stats(p)

    return None

def format_skater_stats(raw_json):
    embed = discord.Embed(title=f'{raw_json["team"]} - {raw_json["name"]} - {raw_json["position"]}', description=f'Games Played: {raw_json["gamesPlayed"]}', colour=discord.Colour.red())
    if raw_json['team'] in team_dict.keys():
        embed.set_thumbnail(url=team_dict[raw_json['team']])
    embed.set_footer(text='go fire chickens', icon_url='https://cdn.discordapp.com/emojis/780630737799741461.png?v=1')
    embed.add_field(name='Even Strength', value=f"Goals: {raw_json['goals']}\nAssists: {raw_json['assists']}"
                                        f"\nPoints: {raw_json['points']}\n+/-: {raw_json['plusMinus']}"
                                        f"\nShots: {raw_json['shotsOnGoal']}\nGiveaways: {raw_json['giveaways']}"
                                        f"\nFights: {raw_json['fights']}")
    embed.add_field(name='** **', value=f"Hits: {raw_json['hits']}\nBlocks: {raw_json['shotsBlocked']}"
                                        f"\nPIMs: {raw_json['pim']}"
                                        f"\nATOI: {float(raw_json['timeOnIce'])/(60 * float(raw_json['gamesPlayed'])):.2f}"
                                        f"\nShot Pct: {100*float(raw_json['goals'])/float(raw_json['shotsOnGoal']):.2f}%"
                                        f"\nTakeaways: {raw_json['takeaways']}\nFights Won: {raw_json['fightWins']}")

    embed.add_field(name='Special Teams', value=f"PP Goals: {raw_json['ppGoals']}"
                                                f"\nPP Assists: {raw_json['ppAssists']}"
                                                f"\nPP Points: {raw_json['ppPoints']}"
                                                f"\nSH Points: {raw_json['shPoints']}", inline=False)


    return embed

def format_goalie_stats(raw_json):
    embed = discord.Embed(title=f'{raw_json["team"]} - {raw_json["name"]} - {raw_json["position"]}', description=f'Games Played: {raw_json["gamesPlayed"]}', colour=discord.Colour.red())
    if raw_json['team'] in team_dict.keys():
        embed.set_thumbnail(url=team_dict[raw_json['team']])
    embed.set_footer(text='go fire chickens', icon_url='https://cdn.discordapp.com/emojis/780630737799741461.png?v=1')
    embed.add_field(name='Stats', value=f"Wins: {raw_json['wins']}\nLosses: {raw_json['losses']}"
                                        f"\nOT Losses: {raw_json['ot']}"
                                        f"\nRating: {raw_json['gameRating']}")
    embed.add_field(name='** **', value=f"Shutouts: {raw_json['shutouts']}\nSave Pct: {raw_json['savePct']}"
                                        f"\nGAA: {raw_json['gaa']}"
                                        f"\nSAA: {float(raw_json['shotsAgainst'])/float(raw_json['gamesPlayed']):.2f}")
    return embed

def process_pts(msg, server_id):
    pass

def get_db_file(server_id):
    file_loc = os.path.join(db_loc, str(server_id), 'db.json')
    server_path = os.path.join(db_loc, str(server_id))

    if not os.path.exists(db_loc):
        os.mkdir(db_loc)

    if not os.path.exists(server_path):
        os.mkdir(server_path)

    if os.path.isfile(file_loc):
        with open(file_loc, 'r') as f:
            db = json.load(f)
    else:
        with open(file_loc, 'w') as f:
            json.dump({}, f)
        db = {}
    return db, file_loc

def show_help():
    pass

def get_player(user_id, server_id):
    server_id = str(server_id)
    db, _ = get_db_file(server_id)
    if str(user_id) in db.keys():
        return db[str(user_id)]['player_name']
    return None

def get_username(user_id, server_id):
    db, _ = get_db_file(server_id)
    if str(user_id) in db.keys():
        return db[str(user_id)]['username']
    return None

def store_username(user_id, server_id, username):
    db, file_loc = get_db_file(server_id)
    if not str(user_id) in db.keys():
        db[str(user_id)] = {'username': None, 'player_name': None}
    db[str(user_id)]['username'] = str(username)
    with open(file_loc, 'w') as f:
        json.dump(db, f)

def store_player(user_id, server_id, player_name):
    db, file_loc = get_db_file(server_id)
    if not str(user_id) in db.keys():
        db[str(user_id)] = {'username': None, 'player_name': None}
    db[str(user_id)]['player_name'] = str(player_name)
    with open(file_loc, 'w') as f:
        json.dump(db, f)

class TooLongException(RuntimeError):
    def __init__(self, msg):
        super().__init__(msg)

def geify(msg):
    if msg.content.startswith('!ge'):
        split_msg = msg.content[4:].split()
        out = []
        for s in split_msg:
            out_msg = ''
            if ')' in s:
                t = s.split(')')
                if t[0][-1].isupper():
                    t[0] += 'GE'
                else:
                    t[0] += 'ge'
                out_msg = ')'.join(t)
            elif ',' in s:
                t = s.split(',')
                if t[0][-1].isupper():
                    t[0] += 'GE'
                else:
                    t[0] += 'ge'
                out_msg = ','.join(t)
            elif '.' in s:
                t = s.split('.')
                if t[0][-1].isupper():
                    t[0] += 'GE'
                else:
                    t[0] += 'ge'
                out_msg = '.'.join(t)
            else:
                if s[-1].isupper():
                    out_msg = s + 'GE'
                else:
                    out_msg = s + 'ge'
            out.append(out_msg)

        # out = [s + 'ge' for s in split_msg]
        return ' '.join(out)
    return None

def floosh(msg):
    if msg.content.startswith('!penis'):
        return '<:flooshed:785647715425976332> <:flooshed:785647715425976332> <:flooshed:785647715425976332>'
    return None

def get_fantasy_points():
    # SHL reg season
    api_link = 'https://index.simulationhockey.com/api/v1/players/stats'
    request = urllib.request.Request(api_link, headers=headers)
    reg_stats = json.loads(urllib.request.urlopen(request).read())
    p_dict = {}
    for p in reg_stats:
        f_p = (int(p['goals']) * 4) + (int(p['assists']) * 3) + (int(p['hits']) * .4) + (int(p['shotsOnGoal']) * .3)
        f_p += int(p['shotsBlocked']) * .9 if 'D' in p['position'] else int(p['shotsBlocked']) * .6
        p_dict[p['name']] = f_p
    return p_dict

def get_fantasy_teams():
    with open(os.path.join(db_loc, 'fantasy_link.txt')) as f_l:
        fantasy_link = f_l.read()


def check_message(text):
    if text is not None and len(text) < 2000:
        return text
    if text is not None and len(text) >= 2000:
        raise TooLongException('lol message too long')
    return None

# print(get_stats_goalie('Scoochie Stratton'))