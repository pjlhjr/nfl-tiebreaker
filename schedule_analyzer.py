import csv

# Team names/cities that have changed since 2002 are changed to 2021 designator of the same francise
team_abbrev = {
    'Indianapolis Colts': 'IND',
    'Jacksonville Jaguars': 'JAC',
    'Baltimore Ravens': 'BAL',
    'New York Giants': 'NYG', 
    'Tennessee Titans': 'TEN', 
    'Las Vegas Raiders': 'LV',
    'Oakland Raiders': 'LV', # Formerly OAK
    'Buffalo Bills': 'BUF',
    'Cincinnati Bengals': 'CIN', 
    'Tampa Bay Buccaneers': 'TB', 
    'Pittsburgh Steelers': 'PIT',
    'Atlanta Falcons': 'ATL',
    'Houston Texans': 'HOU', 
    'Seattle Seahawks': 'SEA', 
    'New Orleans Saints': 'NO', 
    'Philadelphia Eagles': 'PHI', 
    'Los Angeles Chargers': 'LAC', 
    'San Diego Chargers': 'LAC', # Formerly SD
    'Arizona Cardinals': 'AZ', 
    'Minnesota Vikings': 'MIN', 
    'Cleveland Browns': 'CLE', 
    'New England Patriots': 'NE', 
    'Los Angeles Rams': 'LAR', 
    'St. Louis Rams': 'LAR', # Formerly STL
    'Washington Football Team': 'WAS', 
    'Washington Redskins': 'WAS', # Former name of WAS
    'New York Jets': 'NYJ', 
    'Kansas City Chiefs': 'KC', 
    'Dallas Cowboys': 'DAL', 
    'San Francisco 49ers': 'SF', 
    'Carolina Panthers': 'CAR', 
    'Miami Dolphins': 'MIA', 
    'Detroit Lions': 'DET', 
    'Denver Broncos': 'DEN', 
    'Chicago Bears': 'CHI', 
    'Green Bay Packers': 'GB'
}

divisions = {
    'NFCN': ['CHI', 'MIN', 'GB',  'DET'],
    'NFCE': ['NYG', 'DAL', 'WAS', 'PHI'],
    'NFCS': ['TB',  'ATL', 'NO',  'CAR'],
    'NFCW': ['LAR', 'SF',  'SEA', 'AZ' ],
    'AFCN': ['BAL', 'CLE', 'PIT', 'CIN'],
    'AFCE': ['NE',  'BUF', 'MIA', 'NYJ'],
    'AFCS': ['IND', 'JAC', 'HOU', 'TEN'],
    'AFCW': ['KC',  'DEN', 'LV',  'LAC']
}

team_division = {}
for div in divisions:
    for team in div:
        team_division[team] = div

trace_on = False
def trace_print(msg):
    if trace_on:
        print(msg)

# Returns 1 for a win, 0.5 for a tie, 0 for a lose.
# Raises if an exception if the team did not play in the game.
def game_result(game, team):
    assert team in [game['Winner'], game['Loser']]
    if game['PtsW'] == game['PtsL']:
        return 0.5
    elif game['Winner'] == team:
        return 1.0
    else:
        assert game['Loser'] == team
        return 0.0

# Games is a list of games (can be a subset of full schedule)
def get_team_record(games, team):
    return sum(map(lambda game: game_result(game, team), games))

def get_game_opponent(game, team):
    assert team in [game['Winner'], game['Loser']]
    return game['Winner'] if game['Winner'] != team else game['Loser']

def get_all_opponents(schedules, team):
    return set(map(lambda game: get_game_opponent(game, team), schedules[team]))

def get_common_games(schedules, teams):
    # First, need to get common opponents
    common_opponents = None
    for team in teams:
        opponents = get_all_opponents(schedules, team)
        if common_opponents is None:
            common_opponents = opponents
        else:
            common_opponents = common_opponents.intersection(opponents)

    # Then, we'll go back and get the games
    common_games = {}
    for team in teams:
        common_games[team] = [game for game in schedules[team] if get_game_opponent(game, team) in common_opponents]

    return common_games

# Returns a list of the team(s) with the best record.
# Records should be a dict {team: wins}
# Assumes an equal number of games played
def get_best_record(records):
    best_record = max(records.values())
    return [team for team, record in records.items() if record == best_record]

def get_head_to_head_records(schedules, teams):
    h2h_records = {}
    for team in teams:
        h2h_games = [game for game in schedules[team] if get_game_opponent(game, team) in teams]
        h2h_records[team] = get_team_record(h2h_games, team)
    return h2h_records

# Returns a list of teams in the same conference as the given list of teams.
# Will raise an exception if all teams are not in the same conference.
def get_conf_teams(teams):
    # Get the teams of the two conferences.
    nfc_teams, afc_teams = [], []
    for div, div_teams in divisions.items():
        if div.startswith('NFC'):
            nfc_teams += div_teams
        else:
            assert div.startswith('AFC')
            afc_teams += div_teams
    assert len(nfc_teams) == len(afc_teams)
    
    # All teams should be in the same conference
    if all([team in nfc_teams for team in teams]):
        conf_teams = nfc_teams
    else:
        assert all([team in afc_teams for team in teams])
        conf_teams = afc_teams

    return conf_teams


# Ok, having a better record really isn't a tiebreak per se.
# You need to tie first, to break a tie.
# But treating it as such makes things easiest.
# Send your complaints to Rodger.
def best_record_tiebreak(schedules, teams, tiebreaker_type):
    team_records = {team: get_team_record(schedules[team], team) for team in teams}
    trace_print(f"[ ] Team records: {team_records}")
    return get_best_record(team_records)

def head_to_head_tiebreak(schedules, teams, tiebreaker_type):
    teams, og_teams = teams.copy(), teams

    h2h_records = get_head_to_head_records(schedules, teams)
    trace_print(f"[ ] Head-to-head records: {h2h_records}")
    if tiebreaker_type == 'wc':
        # For the Wild Card, only applied if one team beat every other team, or
        # if one team lost to every other team. For Wild Card opponents, each
        # pair of teams can meet at most once.
        for team in teams:
            if h2h_records[team] == len(teams) - 1:
                trace_print(f"[ ] {team} beat all teams in {teams}")
                return [team]

        # To state the obvious, only one team can lose against every 
        # head-to-head opponent. 
        #
        # The "win" loop must be seperate from and preceed this "lose" loop.
        # In the case where one team goes undefeated (head-to-head) at the same time
        # that another goes winless, the undefeated wins this tiebreak.
        for team in teams:
            # The team was winless head-to-head...
            if h2h_records[team] == 0.0: 
                opponents = get_all_opponents(schedules, team)
                # ...and the team played all other teams in the season.
                if all([opp in opponents for opp in teams if opp != team]):
                    teams.remove(team)
                    trace_print(f"[ ] {team} lost to each of {teams}")
                    return teams

        # If no-team either won all or lost all games head-to-head,
        # then this step in not applicable.
        trace_print(f"[ ] WildCard head-to-head did not chagne {teams}")
        return teams
    else:
        # For the division, best record in head-to-head always applies.
        # (Presumably b/c each team plays every division opponent twice.)
        assert tiebreaker_type == 'div'
        return get_best_record(h2h_records)

def div_tiebreak(schedules, teams, tiebreaker_type):
    div_records = {}
    for team in teams:
        for div_teams in divisions.values():
            if team in div_teams:
               curr_div_records = get_head_to_head_records(schedules, div_teams)
               div_records[team] = curr_div_records[team]
               break 
        else:
            raise Exception(f"Couldn't find division for {team}")

    # All teams have the same number of division games
    trace_print(f"[ ] Div records: {div_records}")
    return get_best_record(div_records)

def conf_tiebreak(schedules, teams, tiebreaker_type):
    conf_teams = get_conf_teams(teams)

    # Over-doing it a bit by getting the conference record of
    # everytime, not just the teams that we're applying the 
    # tiebreaker for. It's just easier to write this way.
    conf_records = get_head_to_head_records(schedules, conf_teams)
    # Now, widdle it down to just the ones that we care about.
    tied_conf_records = {team: record for team, record in conf_records.items() if team in teams}
    # As with the division, all teams played the same number of conference games.
    trace_print(f"[ ] Conf records: {tied_conf_records}")
    return get_best_record(tied_conf_records)

# TODO Might be possible to have a different number of common games. This would break in that case.
def common_games_tiebreak(schedules, teams, tiebreak_type):
    common_games = get_common_games(schedules, teams)
    
    # Skip this tiebreak if less than minimum 4 common games (WC-only)
    if tiebreak_type == 'wc' and all([len(games) < 4 for games in common_games.values()]):
        trace_print(f"[!] Common games tiebreak skipped in WC for {teams}")
        return teams

    common_records = {team: get_team_record(common_games[team], team) for team in teams}

    trace_print(f"[ ] Common records: {common_records}")
    return get_best_record(common_records)

def strength_of_victory_tiebreak(schedules, teams, tiebreak_type):
    teams_sov = {}
    for team in teams:
        teams_sov[team] = 0.0
        for game in schedules[team]:
            if game_result(game, team) == 1.0:
                beaten_opponent = get_game_opponent(game, team)
                teams_sov[team] += get_team_record(schedules[beaten_opponent], beaten_opponent)

    trace_print(f"[ ] SoV: {teams_sov}")
    return get_best_record(teams_sov)

def strength_of_schedule_tiebreak(schedules, teams, tiebreak_type):
    teams_sos = {}
    for team in teams:
        teams_sos[team] = 0.0
        for game in schedules[team]:
            opponent = get_game_opponent(game, team)
            teams_sos[team] += get_team_record(schedules[opponent], opponent)

    trace_print(f"[ ] SoS: {teams_sov}")
    return get_best_record(teams_sos)

# pointsFunc should be a function that takes (game, team),
# and return a point value for that game. This is intended to
# be either the points scored for or the points scored against,
# but in reality this could be anything numeric. This setup
# removes duplication of logic otherwise necessary to rank both.
def rank_teams(schedules, teams, pointsFunc):
    pointsDict = {}

    for team in teams:
        pointsDict[team] = 0
        for game in schedules[team]:
            pointsDict[team] += gamePointsFunc(game, team)

    # Create a list of (team, points) tuples, 
    # sorted from highest to lowest by points
    ranking = list(pointsDict.items())
    ranking.sort(key=lambda x: x[1], reverse=True)

    # Create a team -> integer ranking dictionary.
    # Rankings are 1-indexed.
    rankingDict = {}
    # The previous score & the index of the FIRST appearance of that score.
    # Needed to deal with ties.
    prev_score, tied_score_idx = ranking[0][1], 0
    for idx, team_tup in enumerate(ranking):
        team, score = team_tup
        rankingDict[team] = idx+1 if score != prev_score else tied_score_idx+1
        
        if prev_score != score:
            tied_score_idx = idx
        prev_score = score

    trace_print(f"[ ] Ranking ({str(pointsDict)}): {ranking}\n\t{rankingDict}")
    return rankingDict

def rank_teams_points_for(schedules, teams):
    def get_points_for(game, team):
        return game['PtsW'] if game_result(game, team) == 1.0 else game['PtsL']
    return rank_teams(schedules, teams, get_points_for)

def rank_teams_points_against(schedules, teams):
    def get_points_against(game, team):
        return game['PtsL'] if game_result(game, team) == 1.0 else game['PtsW']
    return rank_teams(schedules, teams, get_points_against)

def conf_combined_ranking_tiebreak(schedules, teams, tiebreak_type):
    conf_teams = get_conf_teams(teams)
    points_for_ranks = rank_teams_points_for(schedules, conf_teams)
    points_against_ranks = rank_teams_points_against(schedules, conf_teams)

    combined_ranks = {}
    for team in teams:
        # Need to invert the ranks for get_best_record function to work.
        combined_ranks[team] = len(points_for_ranks) - points_for_ranks[team]
        combined_ranks[team] += len(points_against_ranks) - points_against_ranks[team]

    trace_print(f"[ ] Conf combined rank: {combined_ranks}")
    return get_best_record(combined_ranks)

def combined_ranking_tiebreak(schedules, teams, tiebreak_type):
    all_teams = []
    for div_teams in divisions.values():
        all_teams += div_teams
    points_for_ranks = rank_teams_points_for(schedules, all_teams)
    points_against_ranks = rank_teams_points_against(schedules, all_teams)

    combined_ranks = {}
    for team in teams:
        # Need to invert the ranks for get_best_record function to work.
        combined_ranks[team] = len(points_for_ranks) - points_for_ranks[team]
        combined_ranks[team] += len(points_against_ranks) - points_against_ranks[team]

    trace_print(f"[ ] Combined rank: {combined_ranks}")
    return get_best_record(combined_ranks)

# TODO It's common games, not conference games :(
# "Net points" == points scored - points allowed
def conf_net_points_tiebreak(schedules, teams, tiebreak_type):
    conf_teams = get_conf_teams(teams)
    team_points = {}
    for team in teams:
        team_points[team] = 0
        for game in schedules[team]:
            if get_game_opponent(game, team) in conf_teams:
                if team == game['Winner']:
                    team_points[team] += game['PtsW'] - game['PtsL']
                # Lose or tie
                else:
                    team_points[team] += game['PtsL'] - game['PtsW']

    trace_print(f"[ ] Conf net points: {team_points}")
    return get_best_record(team_points)

def net_points_tiebreak(schedules, teams, tiebreak_type):
    team_points = {}
    for team in teams:
        team_points[team] = 0
        for game in schedules[team]:
            if team == game['Winner']:
                team_points[team] += game['PtsW'] - game['PtsL']
            # Lose or tie
            else:
                team_points[team] += game['PtsL'] - game['PtsW']

    trace_print(f"[ ] Net points: {team_points}")
    return get_best_record(team_points)

def net_touchdowns_tiebreak(schedules, teams, tiebreak_type):
    raise NotImplemented("Data set doesn't include touchdowns. Hopefully this isn't needed.")

def coin_toss_tiebreak(schedules, teams, tiebreak_type):
    raise NotImplemented("Coin-toss!?! Sigh, I was hoping that I could keep this deterministic/not have special handling of a corner case.")


div_tiebreak_funcs = [best_record_tiebreak, head_to_head_tiebreak,\
    div_tiebreak, common_games_tiebreak, conf_tiebreak,\
    strength_of_victory_tiebreak, strength_of_schedule_tiebreak,\
    conf_combined_ranking_tiebreak, combined_ranking_tiebreak,\
    conf_net_points_tiebreak, net_points_tiebreak, net_touchdowns_tiebreak,\
    coin_toss_tiebreak]

wc_tiebreak_funcs = [best_record_tiebreak, head_to_head_tiebreak,\
    conf_tiebreak, common_games_tiebreak, strength_of_victory_tiebreak,\
    strength_of_schedule_tiebreak, conf_combined_ranking_tiebreak,\
    combined_ranking_tiebreak, conf_net_points_tiebreak, net_points_tiebreak,\
    net_touchdowns_tiebreak, coin_toss_tiebreak]

# TODO For WC b/w two teams in the same div, apply div procedure
# See https://www.nfl.com/standings/tie-breaking-procedures
def get_best_team(schedules, teams, tiebreaker_type):
    teams, og_teams = teams.copy(), teams

    assert tiebreaker_type in ['div', 'wc']

    # Only one team from each division can advance to the WC tiebreak steps.
    # 
    # Unlike the other tiebreakers, this step is not re-applied
    # following elimination of a team.
    #
    # Note as the tiebreak rules are written, the below only applies to the 3+ clubs
    # WC tiebreak. However, this also works to apply the earlier 
    # "If the tied clubs are from the same division, apply division tiebreaker." rule
    # for all WC tiebreaks (whether 2 clubs or 3+ clubs).
    if tiebreaker_type == 'wc':
        for div, div_teams in divisions.items():
            div_ties = set(div_teams).intersection(teams)
            if len(div_ties) < 2:
                continue

            best_of_div = get_best_team(schedules, div_ties, 'div')
            div_ties.remove(best_of_div)
            for div_eliminated in div_ties:
                teams.remove(div_eliminated)

    # The 4 team cap has two different origins, baked into one:
    # For WC, only 4 divisions per conference & only one team per conference should remain.
    # For Division, only 4 teams per division.
    assert len(teams) <= 4
    assert len(teams) > 0
    if len(teams) == 1:
        team = teams.pop()
        trace_print(f"[+] Only team ({team}) is best team, out of original {og_teams}")
        return team
        
    # Chose which tiebreak steps to follow
    if tiebreaker_type == 'div':
        tiebreak_funcs = div_tiebreak_funcs 
    else:
        assert tiebreaker_type == 'wc'
        tiebreak_funcs = wc_tiebreak_funcs

    for tiebreak_func in tiebreak_funcs:
        remaining_teams = tiebreak_func(schedules, teams, tiebreaker_type)
        assert all([remaining_team in teams for remaining_team in remaining_teams])

        # If the tie-break has been resolved
        if len(remaining_teams) == 1:
            trace_print(f"[+] {remaining_teams[0]} selected out of {og_teams} using {str(tiebreak_func.__name__)}")
            return remaining_teams[0]
        # If a team was eliminated, restart tiebreak from the beginning
        elif remaining_teams != teams:
            trace_print(f"[-] {remaining_teams} remain out of {og_teams} using {str(tiebreak_func.__name__)}")
            return get_best_team(schedules, remaining_teams, tiebreaker_type)
        # If no changes in the teams, continue to the next tiebreaker
        else:
            pass
    else:
        raise Exception("All tiebreaks applied without resolution")

def get_seeds(schedules, conf, year):
    seeds = []
    div_champs = []
    remaining_teams = []

    # Get division champs & put everyone else in remaining teams
    for div, teams in divisions.items():
        if not div.startswith(conf):
            continue
        div_champs.append(get_best_team(schedules, teams, 'div'))
        trace_print(f"[*] {div_champs[-1]} won the {div}")
        remaining_teams += [team for team in teams if team != div_champs[-1]]
    assert len(div_champs) == 4
    assert len(remaining_teams) == 12

    # Seed div champs
    remaining_div_champs = div_champs.copy()
    for seed_idx in range(len(remaining_div_champs)):
        # The NFL Tiebreaking Procedures specify that the Wild Card
        # tiebreaking procedures should be applied to determine home
        # field advantage between division winnners.
        #
        # They also specify that only one team advances on any given
        # tie-breaking step. Remaining teams revert to the first step.
        seeds.append(get_best_team(schedules, remaining_div_champs, 'wc'))
        trace_print(f"[*] Selected {seeds[-1]} as #{seed_idx+1} seed")
        remaining_div_champs.remove(seeds[-1])
    assert len(remaining_div_champs) == 0
    assert len(seeds) == 4

    # Get Wild Cards
    num_wcs = 2 if year < 2020 else 3
    for wc_num in range(num_wcs):
        seeds.append(get_best_team(schedules, remaining_teams, 'wc'))
        trace_print(f"[*] Selected {seeds[-1]} as #{wc_num+1} WC / #{len(seeds)} seed")
        remaining_teams.remove(seeds[-1])
    assert len(seeds) + len(remaining_teams) == 16

    return seeds


# Get a mapping from the name of column to its index number
def get_header_indexes(header_row, wanted_columns):
    column_indexes = {}

    for column in wanted_columns:
        for idx, header in enumerate(header_row):
            if column == header:
                column_indexes[column] = idx
                break

    return column_indexes

# NOTE The "Playoffs" heading row should be removed from the CSV data
# TODO Verify that games happen within expected timerange
def load_year(year):
    games = []
    playoff_games = []
    wanted_columns = ["Week", "Day", "Winner/tie", "Loser/tie", "PtsW", "PtsL"]
    week_list = [str(week+1) for week in range(18 if year >= 2021 else 17)]

    with open(f'data/{year}.csv', 'r') as year_csv:
        csv_reader = csv.reader(year_csv)

        header_row = next(csv_reader)
        column_indexes = get_header_indexes(header_row, wanted_columns)

        # The CSV denotes the home team by putting an "@" symbol between
        # the Winner & Loser columns if the away team wins. Otherwise, the
        # column is left empty. The "Winner/tie" column contains the home team
        # in case of a tie. "N" is used for neutral site (i.e. the Super Bowl).
        assert column_indexes["Winner/tie"] + 2 == column_indexes["Loser/tie"]
        for game_entry in csv_reader:
            game_dict = {}
            for column, idx in column_indexes.items():

                if column == "Winner/tie":
                    if game_entry[idx+1] in ['', 'N']:
                        assert 'Home' not in game_dict
                        game_dict['Home'] = team_abbrev[game_entry[idx]]
                    else:
                        assert(game_entry[idx+1] == '@')

                    game_dict['Winner'] = team_abbrev[game_entry[idx]]

                elif column == "Loser/tie":
                    if game_entry[idx-1] == '@':
                        assert 'Home' not in game_dict
                        game_dict['Home'] = team_abbrev[game_entry[idx]]
                    else:
                        assert(game_entry[idx-1] in ['', 'N'])

                    game_dict['Loser'] = team_abbrev[game_entry[idx]]

                else:
                    game_dict[column] = game_entry[idx]

            assert 'Home' in game_dict

            # Only regular season games
            if game_dict['Week'] in week_list:
                games.append(game_dict)
            else:
                assert(game_dict['Week'] in ['WildCard', 'Division', 'ConfChamp', 'SuperBowl'])
                playoff_games.append(game_dict)

    return games, playoff_games


# I could bring in another dataset here to get the actual seeding results,
# but we can also just look at the games played (including who hosted the game).
def verify_seeds(playoff_games, predicted_seeds):
    # Treat a bye as a WC win
    wc_winners = []
    wc_matchups = [(3, 6), (4, 5)]
    if len(predicted_seeds) == 7:
        wc_matchups.append((2, 7))
        wc_winners.append(predicted_seeds[0])
    else:
        assert len(predicted_seeds) == 6
        wc_winners += predicted_seeds[0:2]
    
    def verify_playoff_winner(home_team, away_team, playoff_round):
        for game in playoff_games:
            if game['Week'] != playoff_round:
                continue

            if game['Home'] == home_team:
                assert home_team in [game['Winner'], game['Loser']]
                assert away_team in [game['Winner'], game['Loser']]

                return game['Winner']

        raise Exception(f"{home_team} did not host {away_team} in the {playoff_round} round")

    for home_seed, away_seed in wc_matchups:
        home_team = predicted_seeds[home_seed-1]
        away_team = predicted_seeds[away_seed-1]
        wc_winners.append(verify_playoff_winner(home_team, away_team, 'WildCard'))

    # Re-seed teams for divisional round.
    assert len(wc_winners) == 4
    wc_winners.sort(key=lambda team: predicted_seeds.index(team))
    # Check the division games, but discard the winners as there's 
    # no need to check the Conference Champion game.
    verify_playoff_winner(wc_winners[0], wc_winners[3], 'Division')
    verify_playoff_winner(wc_winners[1], wc_winners[2], 'Division')


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
    for year in range(2002, 2021):
        games, playoff_games = load_year(year)
        schedules = team_schedules(games, year)
        afc_seeds = get_seeds(schedules, 'AFC', year)
        verify_seeds(playoff_games, afc_seeds)
        nfc_seeds = get_seeds(schedules, 'NFC', year)
        verify_seeds(playoff_games, nfc_seeds)

        print(f'{year}: Number of games, {len(games)}', end='; ')
        print("Teams, ", len(list_teams(games)))
        print("\tAFC Playoff Seeds:", afc_seeds)
        print("\tNFC Playoff Seeds:", nfc_seeds)

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'trace':
        trace_on = True
    main()
