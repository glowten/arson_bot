import os
import urllib.request
import urllib.error
import json
from functools import partial, lru_cache

import discord
import pandas as pd
import numpy as np
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
            skater_out = get_player_stats(player)
            if not isinstance(skater_out, tuple):
                return skater_out
            goalie_out = get_player_stats(player, is_goalie=True)
            if not isinstance(goalie_out, tuple):
                return goalie_out

            return fuzzy_name_match(player, skater_out, goalie_out)
            # return not_found(f'Player not found: {player}')
        except urllib.error.HTTPError as err:
            return error_embed(err)

    return None

def fuzzy_name_match(player, skater_out, goalie_out):
    player = player.lower()
    # player not found, do fuzzy string matching
    match_partial = partial(lev_dist, str_in=player)
    # shl skater
    skater_out[0]['distance'] = skater_out[0]['name'].iloc[np.random.permutation(len(skater_out[0]))].apply(match_partial)
    shl_skater = skater_out[0].sort_values('distance', ascending=True).iloc[0].squeeze()
    # j skater
    skater_out[1]['distance'] = skater_out[1]['name'].iloc[np.random.permutation(len(skater_out[1]))].apply(match_partial)
    j_skater = skater_out[1].sort_values('distance', ascending=True).iloc[0].squeeze()
    # shl goalie
    goalie_out[0]['distance'] = goalie_out[0]['name'].iloc[np.random.permutation(len(goalie_out[0]))].apply(match_partial)
    shl_goalie = goalie_out[0].sort_values('distance', ascending=True).iloc[0].squeeze()
    # j goalie
    goalie_out[1]['distance'] = goalie_out[1]['name'].iloc[np.random.permutation(len(goalie_out[1]))].apply(match_partial)
    j_goalie = goalie_out[1].sort_values('distance', ascending=True).iloc[0].squeeze()

    min_match = min(shl_skater['distance'], j_skater['distance'], shl_goalie['distance'], j_goalie['distance'])
    if shl_skater['distance'] == min_match:
        return format_skater_stats(shl_skater)
    if j_skater['distance'] == min_match:
        return format_skater_stats(j_skater)
    if shl_goalie['distance'] == min_match:
        return format_goalie_stats(shl_goalie)
    if j_goalie['distance'] == min_match:
        return format_goalie_stats(j_goalie)

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
        # return '```' + casino_lines[['team', 'gp', 'wins', 'line', 'trend', 'projected']].to_string(index=False) + '```'
        return format_df('Casino Projections', '', casino_lines[['team', 'gp', 'wins', 'line', 'trend', 'projected']])
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

def get_player_stats(player_name, is_goalie=False):
    player_name = player_name.lower()
    # SHL playoffs
    api_link = 'https://index.simulationhockey.com/api/v1/players/stats?type=playoffs'
    if is_goalie:
        api_link = 'https://index.simulationhockey.com/api/v1/goalies/stats?type="playoffs"'
    request = urllib.request.Request(api_link, headers=headers)
    playoff_stats = urllib.request.urlopen(request).read()
    playoff_stats = pd.read_json(playoff_stats)

    # SHL reg season
    api_link = 'https://index.simulationhockey.com/api/v1/players/stats'
    if is_goalie:
        api_link = 'https://index.simulationhockey.com/api/v1/goalies/stats'
    request = urllib.request.Request(api_link, headers=headers)
    reg_stats = urllib.request.urlopen(request).read()
    reg_stats = pd.read_json(reg_stats)

    if playoff_stats.loc[0, 'season'] == reg_stats.loc[0, 'season']:
        shl_stats = playoff_stats
    else:
        shl_stats = reg_stats

    match = shl_stats[shl_stats['name'].str.lower() == player_name]
    if len(match) > 0:
        if is_goalie:
            return format_goalie_stats(match.iloc[0].squeeze())
        return format_skater_stats(match.iloc[0].squeeze())

    # SMJHL playoffs
    api_link = 'https://index.simulationhockey.com/api/v1/players/stats?league=1&type=playoffs'
    if is_goalie:
        api_link = 'https://index.simulationhockey.com/api/v1/goalies/stats?league=1&type="playoffs"'
    request = urllib.request.Request(api_link, headers=headers)
    playoff_stats = urllib.request.urlopen(request).read()
    playoff_stats = pd.read_json(playoff_stats)

    # SMJHL reg season
    api_link = 'https://index.simulationhockey.com/api/v1/players/stats?league=1'
    if is_goalie:
        api_link = 'https://index.simulationhockey.com/api/v1/goalies/stats?league=1'
    request = urllib.request.Request(api_link, headers=headers)
    reg_stats = urllib.request.urlopen(request).read()
    reg_stats = pd.read_json(reg_stats)

    if playoff_stats.loc[0, 'season'] == reg_stats.loc[0, 'season']:
        j_stats = playoff_stats
    else:
        j_stats = reg_stats

    match = j_stats[j_stats['name'].str.lower() == player_name]
    if len(match) > 0:
        if is_goalie:
            return format_goalie_stats(match.iloc[0].squeeze())
        return format_skater_stats(match.iloc[0].squeeze())

    return shl_stats, j_stats


def format_df(title, desc, df):
    embed = discord.Embed(title=title, description=desc, colour=discord.Colour.red())
    embed.set_footer(text='go fire chickens', icon_url='https://cdn.discordapp.com/emojis/780630737799741461.png?v=1')
    for col in df.columns:
        embed.add_field(name=col, value='\n'.join(df[col]))
    return embed


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

def get_applied_tpe(team_name):
    show_all_shl = False
    show_all_j = False
    team_in_shl = False
    team_in_j = False
    team_abbrev = ''
    if team_name is None or team_name.lower() == 'shl':
        show_all_shl = True
    elif team_name.lower() == 'j' or team_name.lower() == 'smjhl':
        show_all_j = True
    else:
        team_name = team_name.lower()
        # find team in teams first to determine league
        api_link = 'https://index.simulationhockey.com/api/v1/teams'
        request = urllib.request.Request(api_link, headers=headers)
        json_out = urllib.request.urlopen(request).read()
        teams_df = pd.read_json(json_out, orient='records')
        teams_df = teams_df[(teams_df['name'].str.lower() == team_name) | (teams_df['abbreviation'].str.lower() == team_name) |
                            (teams_df['location'].str.lower() == team_name)]
        if len(teams_df) > 0:
            team_in_shl = True
            team_abbrev = teams_df['abbreviation'].iloc[0]

        else:
            api_link += '?league=1'
            request = urllib.request.Request(api_link, headers=headers)
            json_out = urllib.request.urlopen(request).read()
            teams_df = pd.read_json(json_out, orient='records')
            teams_df = teams_df[(teams_df['name'].str.lower() == team_name) | (teams_df['abbreviation'].str.lower() == team_name) |
                                (teams_df['location'].str.lower() == team_name)]
            if len(teams_df) > 0:
                team_in_j = True
                team_abbrev = teams_df['abbreviation'].iloc[0]

        if not (team_in_shl or team_in_j):
            return None

    api_link = 'https://index.simulationhockey.com/api/v1/players/ratings'
    if team_in_j or show_all_j:
        api_link += '?league=1'

    request = urllib.request.Request(api_link, headers=headers)
    json_out = urllib.request.urlopen(request).read()
    players_df = pd.read_json(json_out, orient='records')
    players_df = players_df[['team', 'name', 'position', 'appliedTPE']]
    # aggregate player positions
    players_df.loc[(players_df['position'] == 'LD') | (players_df['position'] == 'RD'), 'position'] = 'Defenseman'
    players_df.loc[(players_df['position'] == 'LW') | (players_df['position'] == 'C') |
                   (players_df['position'] == 'RW'), 'position'] = 'Forward'

    # add goalies
    api_link = 'https://index.simulationhockey.com/api/v1/goalies/ratings'
    if team_in_j or show_all_j:
        api_link += '?league=1'
    request = urllib.request.Request(api_link, headers=headers)
    json_out = urllib.request.urlopen(request).read()
    goalies_df = pd.read_json(json_out, orient='records')
    goalies_df = goalies_df[['team', 'name', 'position', 'appliedTPE']]
    goalies_df['position'] = 'Goalie'
    players_df = pd.concat([players_df, goalies_df])

    if show_all_shl or show_all_j:
        # total
        total_team_tpe_df = players_df.groupby(
            ['team'])['appliedTPE'].mean().reset_index().sort_values('appliedTPE', ascending=False, ignore_index=True)
        # position wise
        team_tpe_df = players_df.groupby(
            ['team', 'position'])['appliedTPE'].mean().reset_index().sort_values('appliedTPE', ascending=False,
                                                                                 ignore_index=True)
        team_f_df = team_tpe_df[team_tpe_df['position'] == 'Forward'].reset_index(drop=True)
        team_d_df = team_tpe_df[team_tpe_df['position'] == 'Defenseman'].reset_index(drop=True)
        team_g_df = team_tpe_df[team_tpe_df['position'] == 'Goalie'].reset_index(drop=True)
        # skater tpe
        team_s_df = players_df[
            (players_df['position'] == 'Forward') | (players_df['position'] == 'Defenseman')].groupby(
            ['team'])['appliedTPE'].mean().reset_index().sort_values('appliedTPE', ascending=False, ignore_index=True)

        # index by 1
        total_team_tpe_df.index += 1
        team_f_df.index += 1
        team_d_df.index += 1
        team_g_df.index += 1
        team_s_df.index += 1

        out_dict = {
            'total': total_team_tpe_df,
            'f': team_f_df,
            'd': team_d_df,
            'g': team_g_df,
            's': team_s_df,
            'league': 'SHL' if show_all_shl else 'SMJHL',
        }
        return out_dict

    else:
        # filter team
        players_df = players_df[players_df['team'] == team_abbrev]
        total_tpe = players_df['appliedTPE'].mean()
        # position wise
        position_tpe = players_df.groupby(
            ['position'])['appliedTPE'].mean().reset_index()
        team_f = position_tpe[position_tpe['position'] == 'Forward']['appliedTPE']
        team_d = position_tpe[position_tpe['position'] == 'Defenseman']['appliedTPE']
        team_g = position_tpe[position_tpe['position'] == 'Goalie']['appliedTPE']
        team_s = players_df[(players_df['position'] == 'Forward') |
                            (players_df['position'] == 'Defenseman')]['appliedTPE'].mean()

        individual = players_df.sort_values('appliedTPE', ascending=False, ignore_index=True)

        # index by 1
        individual.index += 1

        out_dict = {
            'individual': individual,
            'total': total_tpe,
            'f': float(team_f),
            'd': float(team_d),
            'g': float(team_g),
            's': float(team_s),
            'team': team_abbrev,
        }
        return out_dict


def check_roster(msg):
    if msg.content.lower().startswith('!roster'):
        rest = msg.content.lower().lstrip('!roster').lstrip()
        roster_input = None
        if not len(rest) == 0:
            roster_input = rest
        out_dict = get_applied_tpe(roster_input)
        if out_dict is None:
            return 'Team ' + rest + ' not found'
        else:
            # individual team
            if 'individual' in out_dict.keys():
                out_str = []
                # team name
                out_str.append(f"{out_dict['team']} TPE Breakdown")
                # individual
                out_str.append(f"```{out_dict['individual'].to_string()}```")
                # f
                out_str.append(f"Forwards Average TPE: {out_dict['f']:.2f}")
                # d
                out_str.append(f"Defensemen Average TPE: {out_dict['d']:.2f}")
                # g
                out_str.append(f"Goalies Average TPE: {out_dict['g']:.2f}")
                # s
                out_str.append(f"Skaters Average TPE: {out_dict['s']:.2f}")
                # total
                out_str.append(f"Average TPE: {out_dict['total']:.2f}")
                return ['\n'.join(out_str)]

            else:
                out = []
                out.append(f"{out_dict['league']} TPE Breakdown")
                # total
                out.append(f"Average TPE\n```{out_dict['total'].to_string()}```")
                # f
                out.append(f"Average Forward TPE\n```{out_dict['f'].to_string()}```")
                # d
                out.append(f"Average Defenseman TPE\n```{out_dict['d'].to_string()}```")
                # g
                out.append(f"Average Goalie TPE\n```{out_dict['g'].to_string()}```")
                # s
                out.append(f"Average Skater TPE\n```{out_dict['s'].to_string()}```")
                return out

    return None

def close_match(other_str, str_in):
    # other_str (assume str_in is normalized)
    other_str_norm = ''.join(other_str.lower().encode('ascii', errors='ignore').decode('ascii').split())
    # vectorize words
    vec_str_in = word_vec(str_in)
    vec_other_str = word_vec(other_str_norm)
    # iterate over string subsets
    min_len = min(len(vec_str_in), len(vec_other_str))
    num_iter = abs(len(vec_str_in) - len(vec_other_str))
    dists = []
    # expand into vector of ascii encoding
    epsilon = 1e-7
    # just take distance
    if num_iter == 0:
        return euclidean_distance(vec_str_in.flatten(), vec_other_str.flatten()) + epsilon
    for i in range(num_iter):
        if len(str_in) > len(other_str_norm):
            strs = vec_str_in[i:len(str_in) - num_iter + i].flatten(), vec_other_str.flatten()
        else:
            strs = vec_str_in.flatten(), vec_other_str[i:len(other_str_norm) - num_iter + i].flatten()
        dists.append((euclidean_distance(*strs) + epsilon))

    return min(dists)

def euclidean_distance(vec1, vec2):
    return np.linalg.norm(vec1-vec2)

def word_vec(word):
    asciied = [ord(c) for c in word]
    # one hot encode the ascii
    one_hot = np.zeros((len(asciied), 128))
    one_hot[:, asciied] = 1
    return one_hot


def lev_dist(other_string, str_in):
    """
    calc levenshtein distance between strings other_string and str_in
    """
    str_in = str_in.lower()
    other_string = other_string.lower()
    if len(str_in) > 30:
        str_in = str_in[:30]
    if len(other_string) > 30:
        other_string = other_string[:30]

    @lru_cache(1024)  # for memoization
    def min_dist(p1, p2):
        if p1 == len(str_in) or p2 == len(other_string):
            return len(str_in) - p1 + len(other_string) - p2
        # no change required
        if str_in[p1] == other_string[p2]:
            return min_dist(p1 + 1, p2 + 1)
        return 1 + min(
            min_dist(p1, p2 + 1),  # insert
            min_dist(p1 + 1, p2),  # delete
            min_dist(p1 + 1, p2 + 1),  # replace
        )
    return min_dist(0, 0)

def check_message(text):
    if text is not None and len(text) < 2000:
        return text
    if text is not None and len(text) >= 2000:
        raise TooLongException('lol message too long')
    return None

