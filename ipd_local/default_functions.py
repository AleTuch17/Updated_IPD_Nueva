# all default functions of the simulation can be found here. 
# presumably written by ian lum '22

import random

def rat(mymoves: [bool], othermoves: [bool], currentRound: int) -> bool:
    # Always Rats (returns true)
    assert len(mymoves) == currentRound
    assert len(othermoves) == currentRound

    return True

def silent(mymoves, othermoves, currentRound) -> bool:
    # Always stays silent
    assert len(mymoves) == currentRound
    assert len(othermoves) == currentRound

    return False

def rand(mymoves, othermoves, currentRound) -> bool:
    # Choose completely randomly 50-50
    return bool(random.getrandbits(1))

def kindaRandom(mymoves, othermoves, currentRound) -> bool:
    # Chooses kinda randomly. Change the variable below to tell it how often to rat. For example, if randomness is set to 0.9, this player will rat 90% of the time
    randomness = 0.9
    
    randNumber = random.random()
    if randNumber < randomness:
        return True
    return False

def titFortat(mymoves, othermoves, currentRound) -> bool:
    # Stays silent until the other player rats. If the other player's last move is rat this player only rats for this round. 
    if len(othermoves) == 0:
        return False
    if othermoves[-1]:
        return True
    return False

def titForTwotats(mymoves, othermoves, currentRound) -> bool:
    # Stays silent until the other player rats twice in a row. If the other player's last 2 moves is rat this player only rats for this round. 
    if len(othermoves) < 2:
        return False
    if othermoves[-1] and othermoves[-2]:
        return True
    else:
        return False

def nukeFortat(mymoves, othermoves, currentRound) -> bool:
    # Stays silent until the other player rats. If the other player's rats this player rats forever. 
    if len(othermoves) == 0:
        return False
    if True in othermoves:
        return True
    return False

def nukeForTwotats(mymoves, othermoves, currentRound) -> bool:
    # Stays silent until the other player rats twice. If the other player's rats twice this player rats forever. 
    if len(othermoves) < 2:
        return False
    indices = [i for i, x in enumerate(othermoves) if x == True]
    for i in range(len(indices)-1):
        if indices[i] == indices[i+1]-1:
            return True
    return False

all_default_functions = [rat, silent, rand, kindaRandom, titFortat, titForTwotats, nukeFortat, nukeForTwotats]
