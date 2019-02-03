import time
import os.path
import requests
import argparse

save_path = '/home/sippycups/Programming/PycharmProjects/live_lines/data'
root_url = 'https://www.bovada.lv'
scores_url = "https://services.bovada.lv/services/sports/results/api/v1/scores/"
headers = {'User-Agent': 'Mozilla/5.0'}

# TODO redo update, tries and excepts, add header function
# TODO add a file write that prints a readable non epoch time
# TODO convert last_mod_score to epoch
# TODO add restart/timeout
# TODO independent score checker
# TODO 'EVEN' fix
# TODO get_scores: separate Score class with its own update times,
# TODO write the league, so as to differentiate between college and NBA
# TODO add short circuit to the score updater, if last_mod_score == cur last mod score, then return.
# TODO upon removing games that are no longer in json, this is a good point to calculate the actual profit of RL bot
# TODO add feature to csv that is a binary saying if information is 0/missing. it will help correct
#  for not knowing when lines close
# TODO add Over Under field and use it for one hot encoding


class Sippy:
    def __init__(self, file_name, header, is_nba):
        print("~~~~sippywoke~~~~")
        self.games = []
        self.links = []
        self.events = []
        self.set_league(is_nba)
        self.json_events()
        self.counter = 0
        self.file = open_file(file_name)
        access_time = time.time()
        self.init_games(access_time)
        if header == 1:
            self.write_header()

    def step(self):  # eventually main wont have a wait_time because wait depnt on the queue and the Q space
        # print("entered main loop")
        access_time = time.time()
        self.json_events()
        self.cur_games(access_time)

        print("self.counter: " + str(self.counter) + " time: " + str(time.localtime()))

        self.counter += 1
        if self.counter % 20 == 1:
            print("before" + str(len(self.games)))
            self.update_games_list()
            print("after" + str(len(self.games)))

        for game in self.games:
            if game.lines.updated == 1:
                game.write_game(self.file)
                game.lines.updated = 0

    def write_header(self):
        self.file.write("sport,game_id,a_team,h_team,")
        self.file.write("last_mod_score,quarter,secs,a_pts,h_pts,status,a_win,h_win,last_mod_to_start,")
        self.file.write("last_mod_lines,num_markets,a_odds_ml,h_odds_ml,a_deci_ml,h_deci_ml,")
        self.file.write("a_odds_ps,h_odds_ps,a_deci_ps,h_deci_ps,a_hcap_ps,h_hcap_ps,a_odds_tot,")
        self.file.write("h_odds_tot,a_deci_tot,h_deci_tot,a_hcap_tot,h_hcap_tot,")
        self.file.write("game_start_time\n")

    def cur_games(self, access_time):
        for event in self.events:
            exists = 0
            for game in self.games:
                if event['id'] == game.game_id:
                    game.lines.update(event)
                    game.scores.update(game.game_id)
                    # Lines.update(game.lines, event)
                    # Score.update(game.scores, event['id'])
                    exists = 1
                    break
            if exists == 0:
                self.new_game(event, access_time)

    def update_games_list(self):
        in_json = 0
        for game in self.games:
            game_id = game.game_id
            for event in self.events:
                if game_id == event['id']:
                    in_json = 1
                    break
            if in_json == 0:
                self.games.remove(game)

    def new_game(self, game, access_time):
        x = Game(game, access_time)
        self.games.insert(0, x)

    def init_games(self, access_time):
        for event in self.events:
            self.new_game(event, access_time)

    def json_events(self):
        pages = []
        games = []
        for link in self.links:
            pages.append(req(link))
        for page in pages:
            try:
                for league in page:
                    games += league['events']
            except TypeError:
                pass
        self.events = games

    def set_league(self, is_nba):
        if is_nba == 1:
            self.links = ["https://www.bovada.lv/services/sports/event/v2/events/A/" 
                          "description/basketball/nba?marketFilterId=def&liveOnly=true&lang=en",
                          "https://www.bovada.lv/services/sports/event/v2/events/" 
                          "A/description/basketball/nba?marketFilterId=def&preMatchOnly=true&lang=en"]
        else:
            self.links = ["https://www.bovada.lv/services/sports/event/v2/events/A/" 
                          "description/basketball?marketFilterId=def&liveOnly=true&eventsLimit=8&lang=en",
                          "https://www.bovada.lv/services/sports/event/v2/events/A/" 
                          "description/basketball?marketFilterId=def&preMatchOnly=true&eventsLimit=50&lang=en"]


class Game:
    def __init__(self, json_game, access_time):
        self.init_time = access_time
        self.sport = json_game['sport']
        self.game_id = json_game['id']
        self.a_team = json_game['description'].split('@')[0]
        self.h_team = json_game['description'].split('@')[1]
        self.teams = [self.a_team, self.h_team]
        self.start_time = json_game['startTime']
        self.scores = Score(self.game_id)
        self.lines = Lines(json_game)
        self.link = json_game['link']
        self.delta = None

    def write_game(self, file):
        self.delta = self.lines.last_mod_lines[-1] - self.start_time
        file.write(self.sport + ",")
        file.write(self.game_id + ",")
        file.write(self.a_team + ",")
        file.write(self.h_team + ",")
        self.scores.csv(file)
        file.write(str(self.delta) + ',')
        self.lines.csv(file)
        # file.write(self.link + ",")
        file.write(str(self.start_time) + "\n")

    def info(self):  # displays scores, lines
        print(self.sport, end=' | ')
        print(self.game_id, end=' | ')
        print(self.a_team, end=' | ')
        print(self.h_team, end=' | ')
        self.scores.info()
        print(str(self.delta), end=' | ')
        self.lines.info()
        print(str(self.start_time) + "\n")


class Lines:
    def __init__(self, json):
        self.updated = 0
        self.json = json
        self.jps = []

        [self.query_times, self.last_mod_lines, self.num_markets, self.a_odds_ml, self.h_odds_ml, self.a_deci_ml,
         self.h_deci_ml, self.a_odds_ps, self.h_odds_ps, self.a_deci_ps, self.h_deci_ps, self.a_hcap_ps,
         self.h_hcap_ps, self.a_odds_tot, self.h_odds_tot, self.a_deci_tot, self.h_deci_tot, self.a_hcap_tot,
         self.h_hcap_tot] = ([] for i in range(19))

        self.params = [
                     self.last_mod_lines, self.num_markets, self.a_odds_ml, self.h_odds_ml, self.a_deci_ml,
                     self.h_deci_ml, self.a_odds_ps, self.h_odds_ps, self.a_deci_ps, self.h_deci_ps,
                     self.a_hcap_ps, self.h_hcap_ps, self.a_odds_tot, self.h_odds_tot, self.a_deci_tot,
                     self.h_deci_tot, self.a_hcap_tot, self.h_hcap_tot
                      ]

    def update(self, json):
        self.updated = 0
        self.json = json
        self.jparams()
        i = 0
        for param in self.params:
            if self.jps[i] is None:
                self.jps[i] = "0"
            if len(param) > 1:
                if param[-1] == self.jps[i]:
                    i += 1
                    continue
            # if json_params[i] is 'EVEN':  # this is a jank fix, really need to test for +,- or add field for O, U
            #     json_params[i] = '-100'
            self.params[i].append(self.jps[i])
            self.updated = 1
            i += 1

    def jparams(self):
        j_markets = self.json['displayGroups'][0]['markets']
        data = {"american": 0, "decimal": 0, "handicap": 0}
        data2 = {"american": 0, "decimal": 0, "handicap": 0}
        mkts = []
        ps = Market(data, data2)
        mkts.append(ps)
        ml = Market(data, data2)
        mkts.append(ml)
        tot = Market(data, data2)
        mkts.append(tot)

        for market in j_markets:
            outcomes = market['outcomes']
            desc = market.get('description')

            try:
                away_price = outcomes[0].get('price')
            except IndexError:
                away_price = data
            try:
                home_price = outcomes[1].get('price')
            except IndexError:
                home_price = data2

            if desc is None:
                continue
            elif desc == 'Point Spread':
                ps.update(away_price, home_price)
            elif desc == 'Moneyline':
                ml.update(away_price, home_price)
            elif desc == 'Total':
                tot.update(away_price, home_price)

        self.jps = [self.json['lastModified'], self.json['numMarkets'], mkts[1].a['american'], mkts[1].h['american'],
                    mkts[1].a['decimal'], mkts[1].h['decimal'], mkts[0].a['american'], mkts[0].h['american'],
                    mkts[0].a['decimal'], mkts[0].h['decimal'], mkts[0].a['handicap'], mkts[0].h['handicap'],
                    mkts[2].a['american'], mkts[2].h['american'], mkts[2].a['decimal'], mkts[2].h['decimal'],
                    mkts[2].a['handicap'], mkts[2].h['handicap']]

    def csv(self, file):
        for param in self.params:
            file.write(str(param[-1]))
            file.write(",")

    def info(self):
        for param in self.params:
            print(str(param), end=' | ')


class Score:
    def __init__(self, game_id):
        [self.last_mod_score, self.quarter, self.secs, self.a_pts, self.h_pts,
            self.status, self.dir_isdown, self.num_quarters, self.a_win, self.h_win] = (0 for i in range(10))

        self.data = None
        self.update(game_id)

        self.params = [self.last_mod_score, self.quarter, self.secs, self.a_pts,
                       self.h_pts, self.status, self.a_win, self.h_win]

    def update(self, game_id):
        self.data = req(scores_url + game_id)
        if self.data is None:
            return
        clock = self.data.get('clock')
        if clock is None:
            return
        self.metadata(clock)
        self.get_score()
        self.win_check()
        self.params = [self.last_mod_score, self.quarter, self.secs, self.a_pts,
                       self.h_pts, self.status, self.a_win, self.h_win]

    def metadata(self, clock):
        self.quarter = clock.get('periodNumber')
        self.num_quarters = clock.get('numberOfPeriods')
        self.secs = clock.get('relativeGameTimeInSecs')
        self.last_mod_score = self.data['lastUpdated']
        if self.data['gameStatus'] == "IN_PROGRESS":
            self.status = 1
        else:
            self.status = 0

    def get_score(self):
        score = self.data.get('latestScore')
        self.a_pts = score.get('visitor')
        self.h_pts = score.get('home')

    def win_check(self):
        if self.quarter == 4 and self.secs == 0:  # this only works w games with 4 periods
            print('endgame')
            if self.a_pts > self.h_pts:
                self.a_win = 1
                self.h_win = 0
                print("Away team wins!")
            elif self.h_pts > self.a_pts:
                self.a_win = 0
                self.h_win = 1
                print("Home team wins!")

    def csv(self, file):
        for param in self.params:
            if param is None:
                param = 0
            file.write(str(param) + ',')

    def info(self):
        for param in self.params:
            if param is None:
                param = 0
            print(str(param), end=' | ')

    def score(self):
        print(self.a_team + " " + str(self.a_pts))
        print(self.h_team + " " + str(self.h_pts))


class Market:
    def __init__(self, away, home):
        self.a = away
        self.h = home

    def update(self, away, home):
        self.a = away
        self.h = home


def req(url):
    try:
        r = requests.get(url, headers=headers, timeout=10)
    except ConnectionResetError:
        print('miss')
        return
    except requests.exceptions.Timeout:
        print('miss')
        return
    except requests.exceptions.ConnectionError:
        print('miss')
        return
    return r.json()


def open_file(file_name):
    complete_name = os.path.join(save_path, file_name + ".csv")
    file = open(complete_name, "a", encoding="utf-8")  # line below probably better called in caller or add another arg
    return file


def write_json(file_name, json):
    file = open_file(file_name)
    file.write(json)
    file.write('\n')
    file.close()
