# new live lines
import time
import os.path
import requests

save_path = '/home/sippycups/Programming/PycharmProjects/live_lines/data'

root_url = 'https://www.bovada.lv'

pre_url = "https://www.bovada.lv/services/sports/event/v2/events/" \
           "A/description/basketball/nba?marketFilterId=def&preMatchOnly=true&lang=en"

live_url = "https://www.bovada.lv/services/sports/event/v2/events/A/" \
            "description/basketball/nba?marketFilterId=def&liveOnly=true&lang=en"

# live_url = "https://www.bovada.lv/services/sports/event/v2/events/A/" \
#            "description/basketball?marketFilterId=def&liveOnly=true&eventsLimit=8&lang=en"

# pre_url = "https://www.bovada.lv/services/sports/event/v2/events/A/" \
#           "description/basketball?marketFilterId=def&preMatchOnly=true&eventsLimit=50&lang=en"


scores_url = "https://services.bovada.lv/services/sports/results/api/v1/scores/"

all_games = []
headers = {'User-Agent': 'Mozilla/5.0'}


# data[0]['events'][0]['displayGroups'][0]['markets']
# TODO redo update, tries and excepts, add header function
# TODO add a file write that prints a readable non epoch time
# TODO convert last_mod_score to epoch
# TODO add restart/timeout
# TODO independent score checker
# TODO 'EVEN' fix

# add field: 1 for live, 0 for not live
# get_scores: separate Score class with its own update times,

 #    tot_a = markets[2].away
# IndexError: list index out of range
class Lines:
    def __init__(self, json_game, access_time):
        self.updated = 0

        [self.query_times, self.last_mod_lines, self.num_markets, self.a_odds_ml, self.h_odds_ml, self.a_deci_ml, self.h_deci_ml,
        self.a_odds_ps, self.h_odds_ps,
        self.a_deci_ps, self.h_deci_ps, self.a_hcap_ps, self.h_hcap_ps, 
        self.a_odds_tot, self.h_odds_tot,
        self.a_deci_tot, self.h_deci_tot, self.a_hcap_tot,
        self.h_hcap_tot] = ([] for i in range(19))

        self.param_list = \
            [
                # self.query_times,
                self.last_mod_lines, self.num_markets, self.a_odds_ml, self.h_odds_ml, self.a_deci_ml, self.h_deci_ml,
                self.a_odds_ps, self.h_odds_ps,
                self.a_deci_ps, self.h_deci_ps, self.a_hcap_ps, self.h_hcap_ps, 
                self.a_odds_tot, self.h_odds_tot,
                self.a_deci_tot, self.h_deci_tot, self.a_hcap_tot,
                self.h_hcap_tot]

    def update(self, json_game, access_time):
        
        self.updated = 0 

        json_markets = json_game['displayGroups'][0]['markets']

        markets = market_grab(json_markets)
        blank = {"american": 0, "decimal": 0, "handicap": 0}
        # by this point we should have guaranteed that there are no fields that will cause KeyErrors
        # going to mistake
        try:
            ps = markets[0]
            ml = markets[1]
            tot = markets[2]
        except IndexError:
            tot = ml
            tot = Market(blank, blank)

        json_params = [json_game['lastModified'], json_game['numMarkets'], ml.away['american'],
                       ml.home['american'], ml.away['decimal'], ml.home['decimal'], ps.away['american'],
                       ps.home['american'], ps.away['decimal'], ps.home['decimal'], ps.away['handicap'],
                       ps.home['handicap'], tot.away['american'], tot.home['american'], tot.away['decimal'],
                       tot.home['decimal'], tot.away['handicap'], tot.home['handicap']]

        # self.a_odds_ml, self.h_odds_ml, self.a_deci_ml, self.h_deci_ml, self.a_odds_ps, self.h_odds_ps,
        # self.a_deci_ps, self.h_deci_ps, self.a_hcap_ps, self.h_hcap_ps, self.a_odds_tot, self.h_odds_tot,
        # self.a_deci_tot, self.h_deci_tot, self.a_hcap_tot, self.h_hcap_tot
        i = 0

        for param in self.param_list:
            if len(param) > 1:
                if param[-1] == json_params[i]:
                    continue
            if json_params[i] is None:
                json_params[i] = "?"
            self.param_list[i].append(json_params[i])
            self.updated = 1
            i += 1

    def write_params(self, file):
        for param in self.param_list:
            file.write(str(param[-1]))
            file.write(",")
        # print("write_params called")


class Game:
    def __init__(self, json_game, access_time):
        self.sport = json_game['sport']
        self.game_id = json_game['id']
        self.a_team = json_game['description'].split('@')[0]
        self.h_team = json_game['description'].split('@')[1]
        self.start_time = json_game['startTime']
        # self.live = live_check(json_game)
        self.scores = Score(self.game_id)
        self.lines = Lines(json_game, access_time)
        self.link = json_game['link']

    def write_game(self, file):
        file.write(self.sport + ",")
        file.write(self.game_id + ",")
        file.write(self.a_team + ",")
        file.write(self.h_team + ",")
        self.scores.write_scores(file)
        self.lines.write_params(file)
        file.write(self.link + ",")
        file.write(str(self.start_time) + ",")
        delta = self.lines.last_mod_lines[-1] - self.start_time
        file.write(str(delta) + '\n')
        """sport, game_id, a_team, h_team, time_cst, last_mod_score, quarter, secs, 
        a_pts, h_score,  clock_dir, num_quarters, link, game_start_time"""


class Score:
    def __init__(self, game_id):

        [self.last_mod_score, self.quarter, self.secs, self.a_pts, self.h_pts,
                        self.status, self.dir_isdown, self.num_quarters] = (0 for i in range(8))

        self.update_scores(game_id)

        self.params = [self.last_mod_score, self.quarter, self.secs, self.a_pts, self.h_pts,
                        self.status]
                        # self.dir_isdown, self.num_quarters] - these really are more gunna be used for other sports, leaving them out for now

    def update_scores(self, game_id):

        data = get_json(scores_url + game_id)

        try:
            clock = data['clock']

            self.quarter = clock['periodNumber']
            self.num_quarters = clock['numberOfPeriods']
            self.secs = clock['relativeGameTimeInsecs']
            self.last_mod_score = data['lastUpdated']

            self.a_pts = data['latestScore']['visitor']
            self.h_pts = data['latestScore']['home']

            if clock['isTicking'] == 'true':
                self.is_ticking = 1
            else:
                self.is_ticking = 0

            if clock['direction'] == 'down':
                self.dir_isdown = 1
            else:
                self.dir_isdown = 0

            if data['gameStatus'] == "IN_PROGRESS":
                self.status = 1
            else:
                self.status = 0
        except:
            [self.quarter, self.num_quarters, self.secs, self.is_ticking,
             self.status, self.dir_isdown, self.last_mod_score,
             self.a_pts, self.h_pts] = (0 for i in range(9))

        self.params = [ self.last_mod_score, self.quarter, self.secs, self.a_pts, self.h_pts,
                        self.status, self.dir_isdown, self.num_quarters]

    def write_scores(self, file):
        for param in self.params:
            # print(str(param))
            file.write(str(param) + ',')


class Market:
    def __init__(self, away, home):
        self.away = away
        self.home = home


def market_grab(markets):
    market_list = []
    data = {"american": 0, "decimal": 0, "handicap": 0}
    team_mkts = [data, data]

    for market in markets:
        outcomes = market['outcomes']
        i = 0

        for outcome in outcomes:
            try:
                price = outcome['price']
                team_mkts[i]['american'] = price['american']
                team_mkts[i]['decimal'] = price['decimal']
                team_mkts[i]['handicap'] = price['handicap']
            except KeyError: 
                pass
            i += 1

        m = Market(team_mkts[0], team_mkts[1])
        market_list.append(m)
    # print(str(market_list))
    return market_list


def live_check(event):
    try:
        print(event['gameStatus'])
        if event['gameStatus'] == "IN_PROGRESS":

            return 1
    except:
        return 0
    return 0


def cur_games(json_games, access_time):
    for event in json_games:
        exists = 0
        for game in all_games:
            if event['id'] == game.game_id:
                Lines.update(game.lines, event, access_time)
                Score.update_scores(game.scores, event['id'])
                exists = 1
                break
        if exists == 0:
            new_game(event, access_time)


def update_games_list(json_games):
    in_json = 0
    for game in all_games:
        game_id = game.game_id
        for event in json_games:
            if game_id == event['id']:
                in_json = 1
                break
        if in_json == 0:
            all_games.remove(game)


def get_json(url):
    try:
        r = requests.get(url, headers=headers)
    except:
        print("miss")
    try:
        data = r.json()
    except:
        data = None
    return data


def open_file(file_name):
    complete_name = os.path.join(save_path, file_name + ".csv")
    file = open(complete_name, "a", encoding="utf-8")  # line below probably better called in caller or add another arg
    return file


def write_json(file_name, json):
    file = open_file(file_name)
    file.write(json)
    file.write('\n')
    file.close()


def new_game(game, access_time):
    x = Game(game, access_time)
    all_games.insert(0, x)


def init_games(json_games, access_time):
    for event in json_games:
        new_game(event, access_time)


def json_events():
    games = []
    pre_json = get_json(pre_url)

    if pre_json:
        pre_games = pre_json[0]['events']
        games += pre_games

    live_json = get_json(live_url)

    if live_json:
        live_games = live_json[0]['events']
        games += live_games

    return games


def write_header(file):
    file.write("sport, game_id, a_team, h_team, ")
    file.write("last_mod_score, quarter, secs, a_pts, h_pts, status, ")
    file.write("last_mod_lines, num_markets, a_odds_ml, h_odds_ml, a_deci_ml, h_deci_ml, ")
    file.write("a_odds_ps, h_odds_ps, a_deci_ps, h_deci_ps, a_hcap_ps, h_hcap_ps, a_odds_tot, ")
    file.write("h_odds_tot, a_deci_tot, h_deci_tot, a_hcap_tot, h_hcap_tot, ")
    file.write("link, game_start_time, last_mod_to_start \n")
    #last_mod_to_start is last_mod_lines - game_start_time


def main(wait_time, file_name):
    counter = 0

    file = open_file(file_name)
    write_header(file)

    access_time = time.time()
    json_games = json_events()

    init_games(json_games, access_time)

    while True:
        access_time = time.time()
        events = json_events()

        cur_games(events, access_time)
        time.sleep(wait_time)

        print("counter: " + str(counter) + " time: " + str(time.time()))
        counter += 1

        if counter % 20 == 1:

            print("before" + str(len(all_games)))

            update_games_list(events)

            print("after" + str(len(all_games)))

        for game in all_games:

            if game.lines.updated == 1:

                game.write_game(file)


main(1, "1 19 19")
