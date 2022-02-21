from collections import defaultdict

from load_schedules import *
from nfl_tiebreakers import *


# Starting in 2002, this rotation repeats every 3 years.
# Note that this is the same for both conferences
# Taken from https://en.wikipedia.org/wiki/NFL_regular_season#Scheduled_division_matchups
intraconf_matchup_rotation = [  {'W': 'E', 'E': 'W', 'N': 'S', 'S': 'N'},
                                {'W': 'N', 'N': 'W', 'E': 'S', 'S': 'E'},
                                {'W': 'S', 'S': 'W', 'N': 'E', 'E': 'N'}]

# Starting in 2021, this rotation repeats every 4 years.
# Taken from https://en.wikipedia.org/wiki/NFL_regular_season#Scheduled_division_matchups
interconf_matchup_rotation = [  {'AFCE': 'NFCE', 'AFCN': 'NFCW', 'AFCS': 'NFCS', 'AFCW': 'NFCN'},
                                {'AFCE': 'NFCW', 'AFCN': 'NFCE', 'AFCS': 'NFCN', 'AFCW': 'NFCS'},
                                {'AFCE': 'NFCS', 'AFCN': 'NFCN', 'AFCS': 'NFCW', 'AFCW': 'NFCE'},
                                {'AFCE': 'NFCN', 'AFCN': 'NFCS', 'AFCS': 'NFCE', 'AFCW': 'NFCN'}]
# Add the reverse for ease-of-use
for year in interconf_matchup_rotation:
    for k, v in year.copy().items():
        year[v] = k

# This is the 17th game.
def get_interconference_ranked_opponents(year, prev_div_rankings):
    assert year >= 2021
    div_matchups = interconf_matchup_rotation[(year-2021) % len(interconf_matchup_rotation)]
    team_matchups = {}
    for div, opp_div in div_matchups.items():
        div_rankings = prev_div_rankings[div]
        opp_rankings = prev_div_rankings[opp_div]
        assert len(div_rankings) == len(opp_rankings)
        for rank_idx in range(len(div_rankings)):
            team_matchups[div_rankings[rank_idx]] = opp_rankings[rank_idx]
            if opp_rankings[rank_idx] in team_matchups:
                assert div_rankings[rank_idx] == team_matchups[opp_rankings[rank_idx]]

    assert len(team_matchups) == 32
    return dict(team_matchups)

def get_intraconference_ranked_opponents(year, prev_div_rankings):
    assert year >= 2002
    div_matchups = intraconf_matchup_rotation[(year-2002) % len(intraconf_matchup_rotation)]
    team_matchups = defaultdict(list)
    for conf in ['NFC', 'AFC']:
        for div, match_div in div_matchups.items():
            div, match_div = conf+div, conf+match_div
            div_rankings = prev_div_rankings[div]

            # These two "ranked" games are from the two divisions
            # which are *NOT* matched up this year. (All of the
            # match up teams already play each other.)
            conf_nonmatchup_divs = [d for d in divisions.keys() if\
                d.startswith(conf) and d not in [div, match_div]]
            assert len(conf_nonmatchup_divs) == 2
            for opp_div in conf_nonmatchup_divs:
                opp_rankings = prev_div_rankings[opp_div]
                assert len(div_rankings) == len(opp_rankings)
                for rank_idx in range(len(div_rankings)):
                    team_matchups[div_rankings[rank_idx]].append(opp_rankings[rank_idx])

    assert len(team_matchups) == 32
    assert all([len(opps) == 2 for opps in team_matchups.values()])
    return dict(team_matchups)

def get_schedules_without_17th(schedules, year, prev_div_rankings):
    assert year >= 2021
    new_schedules = {}
    for team, games in schedules.items():
        interconf_opps = get_interconference_ranked_opponents(year, prev_div_rankings)
        new_schedules[team] = [game for game in games\
            if get_game_opponent(game, team) != interconf_opps[team]]
        assert len(new_schedules[team]) == len(schedules[team]) - 1

    return new_schedules

def get_schedules_without_ranked_opps(schedules, year, prev_div_rankings):
    assert year >= 2002
    if year >= 2021:
        schedules = get_schedules_without_17th(schedules, year, prev_div_rankings)

    new_schedules = {}
    for team, games in schedules.items():
        intraconf_opps = get_intraconference_ranked_opponents(year, prev_div_rankings)
        new_schedules[team] = [game for game in games\
            if get_game_opponent(game, team) not in intraconf_opps[team]]
        assert len(new_schedules[team]) == len(schedules[team]) - len(intraconf_opps[team])

    return new_schedules

def verify_ranked_games(schedules, year, prev_div_rankings):
    assert year >= 2002
    intraconf_opps = get_intraconference_ranked_opponents(year, prev_div_rankings)
    interconf_opps = get_interconference_ranked_opponents(year, prev_div_rankings) if year >= 2021 else None
    for team, games in schedules.items():
        opps = get_all_opponents(schedules, team)
        assert team in intraconf_opps
        for opp in intraconf_opps[team]:
            assert opp in opps

        if interconf_opps is not None:
            assert team in interconf_opps
            assert interconf_opps[team] in opps
        

def list_teams(games):
    teams = set()
    for game in games:
        teams.add(game['Winner']) 
        teams.add(game['Loser'])
    return teams

def team_schedules(games, year):
    schedules = {} 
    for team in list_teams(games):
        schedules[team] = [game for game in games if team in [game['Loser'], game['Winner']]]
        assert len(schedules[team]) == 16 if year < 2021 else 17
    return schedules


def main():
    # TODO Handle the 2002 realignment corner case 
    prev_div_rankings = None
    for year in range(2002, 2021+1):
        games, playoff_games = load_year(year)
        schedules = team_schedules(games, year)
        div_rankings = rank_divisions(schedules)

        print(f'{year}: Number of games, {len(games)}', end='; ')
        print("Teams, ", len(list_teams(games)))

        def print_seeds(conf):
            seeds_without_17th, seeds_without_ranked_opps = None, None
            seeds = get_seeds(schedules, conf, year)
            verify_seeds(playoff_games, seeds)

            # TODO Remove the if-statement once 2002 realignment is handled
            if prev_div_rankings is not None:
                verify_ranked_games(schedules, year, prev_div_rankings)

                if year >= 2021:
                    schedules_without_17th = get_schedules_without_17th(schedules, year, prev_div_rankings)
                    seeds_without_17th = get_seeds(schedules_without_17th, conf, year)

                schedules_without_ranked_opps = get_schedules_without_ranked_opps(schedules, year, prev_div_rankings)
                seeds_without_ranked_opps = get_seeds(schedules_without_ranked_opps, conf, year)

            print(f"\t{conf} Playoff Seeds:", seeds)
            if seeds_without_17th is not None and seeds_without_17th != seeds:
                print(f"No 17th {conf} Playoff Seeds:", seeds_without_17th)
            if seeds_without_ranked_opps is not None and seeds_without_ranked_opps != seeds:
                print(f"No rank {conf} Playoff Seeds:", seeds_without_ranked_opps)

        print_seeds('AFC')
        print_seeds('NFC')
        print("\tDivision rankings:", div_rankings)
        
        prev_div_rankings = div_rankings

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'trace':
        trace_on = True
    main()
