live_lines is a tracker for bovada for basketball.
most testing has been done on just nba, but you can specify as one of the arguments to Sippy.

Sippy is the main class that drives the scraper and can be used to access data on the lines fairly easily. 
format of simple usage of main class
sip = Sippy('#FILENAME',#WAIT_TIME, #1 for NBA, 0 for all BASK)

A set of simple commands to get somewhere is to 

import sippy_lines as sl
sip = Sippy('nba_data', 5, 1)
sip.step()
game = sip.games[0]
game.teams
game.scores.a_pts
game.scores.h_pts
