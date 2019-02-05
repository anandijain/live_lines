import sippy_lines as sl


class Test:
    def __init__(self, file_name):
        self.fn = file_name
        self.sip = sl.Sippy(self.fn, 1, 1)
        self.sip.step()
        self.game = self.sip.games[0]
        # self.game.info()

