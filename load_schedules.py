import csv

trace_on = False
def trace_print(msg):
    if trace_on:
        print(msg)

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
