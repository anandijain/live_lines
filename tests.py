import sippy_lines as sl


class Test:
    def __init__(self, file_name, nba, header, run):
        self.fn = file_name
        self.league = nba
        self.header = header
        self.sip = sl.Sippy(self.fn, header, nba)
        self.sip.step()
        print('num_games: ' + str(len(self.sip.games)))
        if len(self.sip.games) > 0:
            self.game = self.sip.games[0]
        if run != 0:
            self.run()
        # self.game.info()

    def run(self):
        self.sip.run()
