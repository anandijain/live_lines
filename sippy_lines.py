import time
import os.path
import requests
import argparse

save_path = 'data'
root_url = 'https://www.bovada.lv'
scores_url = "https://services.bovada.lv/services/sports/results/api/v1/scores/"
headers = {'User-Agent': 'Mozilla/5.0'}

# TODO convert last_mod_score to epoch
# TODO add restart/timeout
# TODO 'EVEN' fix
# TODO fix scores class so that it stores a list of scores.
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
        access_time = time.time()
        self.json_events()
        self.cur_games(access_time)
        time.sleep(1)
        print("self.counter: " + str(self.counter) + " time: " + str(time.localtime()))
        self.counter += 1

        if self.counter % 20 == 1:
            print(str(len(self.games)))
            self.file.flush()

        for game in self.games:
                if game.lines.updated == 1 or game.score.new == 1:
                    game.write_game(self.file)
                    game.lines.updated = 0
                    try:
                        if game.score.a_win[-1] != 0 or game.score.h_win[-1] != 0:
                            self.games.remove(game)
                    except IndexError:
                        pass

    def cur_games(self, access_time):
        for event in self.events:
            exists = 0
            for game in self.games:
                if event['id'] == game.game_id:
                    game.lines.update(event)
                    game.score.update()
                    exists = 1
                    break
            if exists == 0:
                self.new_game(event, access_time)

    def json_events(self):
        pages = []
        events = []
        for link in self.links:
            pages.append(req(link))
        for page in pages:
            for league in page:
                events += league.get('events')
        self.events = events

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

    def write_header(self):
        self.file.write("sport,game_id,a_team,h_team,")
        self.file.write("last_mod_score,quarter,secs,a_pts,h_pts,status,a_win,h_win,last_mod_to_start,")
        self.file.write("last_mod_lines,num_markets,a_odds_ml,h_odds_ml,a_deci_ml,h_deci_ml,")
        self.file.write("a_odds_ps,h_odds_ps,a_deci_ps,h_deci_ps,a_hcap_ps,h_hcap_ps,a_odds_tot,")
        self.file.write("h_odds_tot,a_deci_tot,h_deci_tot,a_hcap_tot,h_hcap_tot,")
        self.file.write("game_start_time\n")

    def info(self, verbose):  # 1 for verbose, else for abridged
        print(str(len(self.games)))
        for game in self.games:
            if verbose == 1:
                game.info()
            else:
                game.quick()

    def new_game(self, game, access_time):
        x = Game(game, access_time)
        self.games.insert(0, x)

    def init_games(self, access_time):
        for event in self.events:
            self.new_game(event, access_time)

    def run(self):
        while True:
            self.step()


class Game:
    def __init__(self, json_game, access_time):
        self.init_time = access_time
        self.sport = json_game['sport']
        self.game_id = json_game['id']
        self.desc = json_game['description']
        self.a_team = self.desc.split('@')[0]
        self.a_team = self.a_team[:-1]
        self.h_team = self.desc.split('@')[1]
        self.h_team = self.h_team[1:]
        self.teams = [self.a_team, self.h_team]
        self.start_time = json_game['startTime']
        self.score = Score(self.game_id)
        self.lines = Lines(json_game)
        self.link = json_game['link']
        self.delta = None

    def write_game(self, file):
        self.time_diff()
        file.write(self.sport + ",")
        file.write(self.game_id + ",")
        file.write(self.a_team + ",")
        file.write(self.h_team + ",")
        self.score.csv(file)
        file.write(str(self.delta) + ',')
        self.lines.csv(file)
        # file.write(self.link + ",")
        file.write(str(self.start_time) + "\n")

    def info(self):  # displays scores, lines
        print('\n' + self.desc + '\n')
        print(self.sport, end='|')
        print(self.game_id, end='|')
        print(self.a_team, end='|')
        print(self.h_team, end='|')
        print('\nScores info: ')
        self.score.info()
        print('Game line info: ')
        print(str(self.delta), end='|')
        self.lines.info()
        print(str(self.start_time) + "\n")

    def quick(self):
        print(str(self.lines.last_mod_lines))
        print(self.a_team, end=': ')
        print(str(self.score.a_pts) + ' ' + str(self.lines.a_odds_ml))
        print(self.h_team, end=': ')
        print(str(self.score.h_pts) + ' ' + str(self.lines.h_odds_ml))

    def score(self):
        print(self.a_team + " " + str(self.score.a_pts))
        print(self.h_team + " " + str(self.score.h_pts))

    def odds(self):
        print(self.a_team + " " + str(self.lines.odds()))
        print(self.h_team + " " + str(self.lines.odds()))

    def time_diff(self):
        if len(self.lines.last_mod_lines) > 0:
            self.delta = (self.lines.last_mod_lines[-1] - self.start_time) / 1000
        else:
            self.delta = '0'


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

        if len(self.params[0]) > 0:
            if self.jps[0] == self.params[0][-1]:
                self.updated = 0
                return

        i = 0
        for param in self.params:
            if self.jps[i] is None:
                self.jps[i] = "0"
            if len(param) > 0:
                if param[-1] == self.jps[i]:
                    i += 1
                    continue
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
            if len(param) > 0:
                file.write(str(param[-1]))
                file.write(",")
            else:
                file.write(str(0))
                file.write(',')

    def info(self):
        for param in self.params:
            try:
                print(str(param[-1]), end='|')
            except IndexError:
                print('None', end='|')

    def odds(self):
        for elt in [self.last_mod_lines, self.a_odds_ml, self.h_odds_ml]:
            print(str(elt), end='|')


class Score:
    def __init__(self, game_id):
        self.new = 1
        self.game_id = game_id
        self.num_quarters = 0
        self.dir_isdown = 0
        self.jps = []
        self.data = None
        self.clock = None
        self.json()
        self.jparams()

        [self.last_mod_score, self.quarter, self.secs, self.a_pts, self.h_pts,
            self.status, self.a_win, self.h_win] = ([] for i in range(8))

        self.params = [self.last_mod_score, self.quarter, self.secs, self.a_pts,
                       self.h_pts, self.status, self.a_win, self.h_win]

    def update(self):
        self.new = 0
        self.json()
        if self.data is None:
            return
        self.clock = self.data.get('clock')
        if self.clock is None:
            return
        self.metadata()
        self.get_score()
        self.win_check()

    def json(self):
        self.data = req(scores_url + self.game_id)

    def jparams(self):
        if self.data is None:
            return
        self.clock = self.data.get('clock')
        if self.clock is None:
            return
        stat = 0
        if self.data['gameStatus'] == "IN_PROGRESS":
            stat = 1

        score = self.data.get('latestScore')

        self.jps = [self.data['lastUpdated'], self.clock.get('periodNumber'), self.clock.get('relativeGameTimeInSecs'),
                    score.get('visitor'), score.get('home'), stat]

        self.num_quarters = self.clock.get('numberOfPeriods')
        self.dir_isdown = self.clock.get('direction')

    def metadata(self):
        last_updated = self.data['lastUpdated']
        if len(self.last_mod_score) > 0:
            if self.last_mod_score[-1] == last_updated:
                self.new = 0
                return

        self.jparams()
        i = 0
        for jp in self.jps:
            if len(self.params[i]) > 0:
                if self.params[i][-1] == self.jps[i]:
                    i += 1
                    continue
            self.params[i].append(jp)
            self.new = 1
            i += 1

    def get_score(self):
        if self.new == 1:
            score = self.data.get('latestScore')
            self.a_pts.append(score.get('visitor'))
            self.h_pts.append(score.get('home'))

    def win_check(self):
        if self.num_quarters == 0:
            self.num_quarters = 4
        if self.quarter[-1] == self.num_quarters and self.secs[-1] == 0:
            if self.a_pts[-1] > self.h_pts[-1]:
                self.a_win.append(1)
                self.h_win.append(0)
                print("Away team wins!")

            elif self.h_pts[-1] > self.a_pts[-1]:
                self.a_win.append(0)
                self.h_win.append(1)
                print("Home team wins!")

    def csv(self, file):
        for param in self.params:
            if len(param) > 0:
                if param is None:
                    param = ''
                file.write(str(param[-1]) + ',')
            else:
                file.write('0' + ',')

    def info(self):
        for param in self.params:
            if param is None:
                param = 0
            print(str(param), end='|')
        print('\n')


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
        print('connection reset error')
        time.sleep(2)
        return
    except requests.exceptions.Timeout:
        print('requests.exceptions timeout error')
        time.sleep(2)
        return
    except requests.exceptions.ConnectionError:
        print('connectionerror')
        time.sleep(2)
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
