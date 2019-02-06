live_lines is a tracker for bovada for basketball

live_lines.py is deprecated.
sippy_lines.py is current.

The fastest way to run this is to run the following commands:
First start python3

import tests as t
x = t.Test('0000', 1)  # the 1 is for specifying that you are only collecting NBA data
x.run()

now the data will export to /data/0000.csv



Sippy is the main class that drives the scraper and can be used to access data on the live lines fairly easily. 
Format of simple usage of main class:

    sip = Sippy('#FILENAME',#WAIT_TIME, 1 for NBA, 0 for all BASK)

A set of simple commands to get somewhere is to:

    import sippy_lines as sl
    sip = Sippy('nba_data', 5, 1)
    sip.step()
    game = sip.games[0]
    game.teams
    game.scores.a_pts
    game.scores.h_pts

If a_pts and h_pts doesn't work, most likely there are no live games, you can check the odds like this:
    
    game.lines.a_odds_ml
    game.lines.h_odds_ml


If you want to run the tracker, first you'll prob have to change the file path at the top of the program, then:
    
    while True:
        sip.step()
   
This class is supposed to be modeled after Markov decision processes and used in reinforcement learning.
    