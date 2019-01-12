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
#pre_url = "https://www.bovada.lv/services/sports/event/v2/events/A/" \
#           "description/basketball?marketFilterId=def&preMatchOnly=true&eventsLimit=50&lang=en"


scores_url = "https://services.bovada.lv/services/sports/results/api/v1/scores/"

all_games = []
headers = {'User-Agent': 'Mozilla/5.0'}


# data[0]['events'][0]['displayGroups'][0]['markets']
# TODO live_marker, get_scores
# add field: 1 for live, 0 for not live
# get_scores: separate Score class with its own update times,


class Lines:
    def __init__(self, json_game, access_time):
        self.updated = 0
        [self.query_times, self.num_markets, self.last_modified,
         self.ps_a_hcap, self.ps_a_amer, self.ps_a_deci, self.ps_a_frac,
         self.ps_h_hcap, self.ps_h_amer, self.ps_h_deci, self.ps_h_frac,
         self.ml_a_amer, self.ml_a_deci, self.ml_a_frac, self.ml_h_amer,
         self.ml_h_deci, self.ml_h_frac, self.tot_a_hcap, self.tot_a_amer,
         self.tot_a_deci, self.tot_a_frac, self.tot_h_hcap, self.tot_h_amer,
         self.tot_h_deci, self.tot_h_frac] = ([] for i in range(25))

        self.param_list = \
            [
                # self.query_times,
                self.num_markets, self.last_modified, self.ps_a_hcap, self.ps_a_amer,
                self.ps_a_deci, self.ps_a_frac, self.ps_h_hcap, self.ps_h_amer, self.ps_h_deci, self.ps_h_frac,
                self.ml_a_amer, self.ml_a_deci, self.ml_a_frac, self.ml_h_amer, self.ml_h_deci, self.ml_h_frac,
                self.tot_a_hcap, self.tot_a_amer, self.tot_a_deci, self.tot_a_frac, self.tot_h_hcap,
                self.tot_h_amer, self.tot_h_deci, self.tot_h_frac]

    def market_grab(self, markets):
        market_list = []

        for market in markets:

            for i in range(3):
                outcomes = market['outcomes']
            if len(outcomes) == 2:
                away = outcomes[0]['price']
                home = outcomes[1]['price']

            elif len(outcomes) == 1:
                away = outcomes[0]['price']

                if i == 1:
                    home = {"american": 0, "decimal": 0, "fractional": 0}
                else:
                    home = {"handicap": 0, "american": 0, "decimal": 0, "fractional": 0}

            else:

                if i == 1:
                    away = {"american": 0, "decimal": 0, "fractional": 0}
                    home = away
                else:
                    away = {"handicap": 0, "american": 0, "decimal": 0, "fractional": 0}
                    home = away
            m = Market(away, home)
            market_list.append(m)

        return market_list

    def update(self, json_game, access_time):
        # right now this has risk of writing data for the wrong team, because if only one of the
        # fields is filled, even if it is for the home team, it will be interpretted as ps[0], for example
        self.updated = 0
        json_markets = json_game['displayGroups'][0]['markets']

        markets = self.market_grab(json_markets)

        json_param_list = [json_game['numMarkets'], json_game['lastModified']]

        flist = ['handicap', 'american', 'decimal', 'fractional']
        ml_list = ['american', 'decimal', 'fractional']

        ps_a = markets[0].away
        ps_h = markets[0].home

        for i in range(4):
            try:
                json_param_list.append(ps_a[flist[i]])
            except:
                ps_a[flist[i]] = 0
                json_param_list.append(ps_a[flist[i]])
        for i in range(4):
            try:
                json_param_list.append(ps_h[flist[i]])
            except:
                ps_h[flist[i]] = 0
                json_param_list.append(ps_h[flist[i]])

        ml_a = markets[1].away
        ml_h = markets[1].home

        for i in range(3):
            try:
                json_param_list.append(ml_a[ml_list[i]])
            except:
                ml_a[ml_list[i]] = 0
                json_param_list.append(ml_a[ml_list[i]])
        for i in range(3):
            try:
                json_param_list.append(ml_h[ml_list[i]])
            except:
                ml_h[ml_list[i]] = 0
                json_param_list.append(ml_h[ml_list[i]])

        tot_a = markets[2].away
        tot_h = markets[2].home

        for i in range(4):
            try:
                json_param_list.append(tot_a[flist[i]])
            except:
                tot_a[flist[i]] = 0
                json_param_list.append(tot_a[flist[i]])
        for i in range(4):
            try:
                json_param_list.append(tot_h[flist[i]])
            except:
                tot_h[flist[i]] = 0
                json_param_list.append(tot_h[flist[i]])

        for i in range(len(self.param_list)):
            param = self.param_list[i]
            if len(param) > 1:
                if param[-1] == json_param_list[i]:
                    continue
            if json_param_list[i] is None:
                json_param_list[i] = 0
            self.param_list[i].append(json_param_list[i])
            self.updated = 1

    def write_params(self, file):
        for param in self.param_list:
            file.write(str(param[-1]))
            file.write(",")
        print("write_params called")
        file.write("\n")


class Game:
    def __init__(self, json_game, access_time):
        self.id = json_game['id']
        self.sport = json_game['sport']
        self.link = json_game['link']
        self.away_team = json_game['description'].split('@')[0]
        self.home_team = json_game['description'].split('@')[1]
        self.start_time = json_game['startTime']
        self.live = live_check(json_game)
        self.scores = Score(self.id)
        self.lines = Lines(json_game, access_time)

    def write_game(self, file):

        file.write(self.id + ",")
        file.write(self.sport + ",")
        file.write(self.link + ",")
        file.write(self.away_team + ",")
        file.write(self.home_team + ",")
        file.write(str(self.start_time) + ",")
        file.write(str(self.live) + ",")
        self.scores.write_scores(file)
        self.lines.write_params(file)


def live_check(event):
    try:
        if event['gameStatus'] == "IN_PROGRESS":
            return 1
    except:
        return 0
    return 0


class Market:
    def __init__(self, away, home):
        self.away = away
        self.home = home


class Score:
    def __init__(self, game_id):

        page = get_json(scores_url + game_id)

        [self.quarter, self.num_quarters, self.secs, self.is_ticking,
            self.status, self.dir_isdown, self.last_updated,
         self.away_score, self.home_score] = (0 for i in range(9))

        self.update_scores(page)

        self.params = [self.quarter, self.num_quarters, self.secs, self.is_ticking,
                        self.status, self.dir_isdown, self.last_updated, self.away_score, self.home_score]

    def update_scores(self, page):
        data = page
        clock = data['clock']

        self.quarter = clock['periodNumber']
        self.num_quarters = clock['numberOfPeriods']
        self.secs = clock['relativeGameTimeInSecs']

        if clock['isTicking'] == 'true':
            self.is_ticking = 1
        else:
            self.is_ticking = 0

        if clock['direction'] == 'down':
            self.dir_isdown = 1
        else: 
            self.dir_isdown = 0

        self.last_updated = data['lastUpdated']

        self.away_score = data['latestScore']['visitor']
        self.home_score = data['latestScore']['home']

    def write_scores(self, file):
        for param in self.params:
            print(str(param))
            file.write(str(param) + ',')


def cur_games(json_games, access_time):
    for event in json_games:
        exists = 0
        for game in all_games:
            if event['id'] == game.id:
                Lines.update(game.lines, event, access_time)
                exists = 1
                break
        if exists == 0:
            new_game(event, access_time)


def update_games_list(json_games):
    in_json = 0
    for game in all_games:
        game_id = game.id
        for event in json_games:
            if game_id == event['id']:
                in_json = 1
                break
        if in_json == 0:
            all_games.remove(game)


def get_json(url):
    try:
        r = requests.get(url, headers=headers)
        data = r.json()
    except:
        return data
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


def main(wait_time, file_name):
    counter = 0

    file = open_file(file_name)

    access_time = time.time()
    json_games = json_events()

    init_games(json_games, access_time)

    while True:
        access_time = time.time()
        events = json_events()

        cur_games(events, access_time)
        time.sleep(wait_time)

        print("counter: " + str(counter))
        counter += 1

        if counter % 20 == 1:

            print("before" + str(len(all_games)))

            update_games_list(events)

            print("after" + str(len(all_games)))

        for game in all_games:

            if game.lines.updated == 1:

                game.write_game(file)


main(1, "nba_scores")
