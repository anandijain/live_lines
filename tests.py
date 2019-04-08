import sippy_lines as sl
import matplotlib.pyplot as plt 
import threading
import time

class Test:
    def __init__(self, fn='nba2', header=0, game_type=1, run=1):
        self.fn = fn
        self.gt = game_type
        self.header = header
        self.sip = sl.Sippy(fn=self.fn, header=self.header, league=self.gt)
        self.sip.step()
        print('num_games: ' + str(len(self.sip.games)))
        if len(self.sip.games) > 0:
            self.game = self.sip.games[0]
        if run != 0:
            self.run()
        # self.game.info()

    def run(self):
        self.sip.run()


# unit test

# t = threading.Thread(target = Test, name = 'Sippy1',
#                     args = ('nba2_test', 0, 1, 1))
# t.start()


# x = input()

# print(x)

