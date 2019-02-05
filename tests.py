import sippy_lines as sl


def test(file_name):
    sip = sl.Sippy(file_name,1,1)
    sip.step()
    game = sip.games[0]
    game.info()
