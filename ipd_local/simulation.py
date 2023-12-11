"""Submodule that actually simulates the IPD game."""

import random
from tqdm import tqdm

from typing import List, Callable, Any, Tuple, NewType, Dict, Optional

from .game_specs import *
from .output_locations import *
import types
from loguru import logger

from contextlib import contextmanager
import sys, os

import multiprocessing
import marshal
import itertools
from collections import defaultdict

#dynamic custom game:
if len(sys.argv)==3:
    NOISE = sys.argv[1]
    NOISE_LEVEL = sys.argv[2]

@contextmanager
def suppress_stdout():
    """
    Suppresses any writes to stdout.

    Example:
    ```py
    print("Suppressing!")
    with suppress_stdout():
        # code to suppress
        strategy() # will not print anything even if it has print statements
    print("Back to normal!")
    ```
    """
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout


def pack_functions(functions: Tuple[Callable[..., Any], Callable[..., Any]]) -> Tuple[bytes, bytes]:
    """Packs a tuple of two functions into a tuple of their bytecode.
    Note:
    - If the function references globals, it will not work!
    - This loses the function name information.
    """
    return (marshal.dumps(functions[0].__code__), marshal.dumps(functions[1].__code__))


def unpack_functions(bytecodes: Tuple[bytes, bytes]) -> Tuple[Callable[..., Any], Callable[..., Any]]:
    """Unpacks a tuple of two bytecode sequences into a tuple of functions.
    Default function names are "p1" and "p2".
    """
    return (
        types.FunctionType(marshal.loads(bytecodes[0]), globals(), "p1"),
        types.FunctionType(marshal.loads(bytecodes[1]), globals(), "p2")
    )


def get_scores(
    player1_moves: List[bool],
    player2_moves: List[bool],
    both_rat: int = POINTS_BOTH_RAT,
    both_coop: int = POINTS_BOTH_COOPERATE,
    loser: int = POINTS_DIFFERENT_LOSER,
    winner: int = POINTS_DIFFERENT_WINNER
) -> List[float]:
    """
    Calculates the points each player has given their set of moves.

    Note: `player1_moves` and `player2_moves` are assumed to be equal length!

    Arguments:
    - `player1_moves`: the list of moves player 1 made
    - `player2_moves`: the list of moves player 2 made
    - `both_rat`: the points received if both players rat.
    - `both_coop`: the points received if both players cooperate.
    - `loser`: the points received by the cooperating player if the other one rats
    - `winner`: the points received by the rat player if the other one cooperates

    `both_rat`, `both_coop`, `loser`, and `winner` all default to the values set in `game_specs.py`

    Returns: a 2-element list of the points of player 1 and player 2.
    """
    # NOTE This should really return a tuple instead of a list.
    results = [0.0,0.0]
    for i in range(len(player1_moves)):
        if player1_moves[i]:
            if player2_moves[i]:
                results[0]+=both_rat
                results[1]+=both_rat
            else:
                results[0]+=loser
                results[1]+=winner #THESE WERE SWITCHED IN ANNLI'S CODE
        else:
            if player2_moves[i]:
                results[0]+=winner #THESE WERE SWITCHED IN ANNLI's CODE
                results[1]+=loser
            else:
                results[0]+=both_coop
                results[1]+=both_coop
    return results


def play_match(
    bytecode: Tuple[bytes, bytes],
    noise: bool = NOISE,
    rounds: int = ROUNDS,
    num_games: int = NOISE_GAMES_TILL_AVG
) -> Optional[List[float]]:
    """
    Plays a match of Iterated Prisoner's Dilemma between two players.

    Arguments:
    - `bytecode`: a tuple of the bytecode representations of the two players.
    - `noise`: whether or not noise is enabled.
    - `rounds`: the number of rounds for the game.
    - `num_games`: the number of games to play before averaging results if noise is on.

    `noise`, `rounds`, and `num_games` all default to the values specified in `game_specs.py`

    Returns: a 2-element list of their scores.
    """
    player1, player2 = unpack_functions(bytecode)
    games = []
    for _g in range(num_games if noise else 1):
        player1moves = []
        player2moves = []

        for i in range(rounds):
            # handle perceived moves (for noise)
            p1_moves = player1moves.copy()
            p2_moves = player2moves.copy()
            if noise:
                if random.random()<NOISE_LEVEL and len(player1moves) > 0:
                    p1_moves[-1] = not(player1moves[-1])
                if random.random()<NOISE_LEVEL and len(player2moves) > 0:
                    p2_moves[-1] = not(player2moves[-1])

            try:
                with suppress_stdout():
                    player1move = player1(p1_moves, p2_moves, i)
                    if not isinstance(player1move, bool):
                        raise Exception("Strategy returned invalid response!")
            except Exception as e:
                return None

            try:
                with suppress_stdout():
                    player2move = player2(p2_moves, p1_moves, i)
                    if not isinstance(player2move, bool):
                        raise Exception("Strategy returned invalid response!")                    
            except Exception as e:
                return None

            player1moves.append(player1move)
            player2moves.append(player2move)

        if len(player1moves) != rounds or len(player2moves) != rounds:
            return None

        games.append(get_scores(player1moves, player2moves))

    return [
        sum([g[0] for g in games])/(num_games if noise else 1),
        sum([g[1] for g in games])/(num_games if noise else 1),
    ]

Strategy = NewType("Strategy", Callable[[List[bool], List[bool], int], bool]) # FIXME redundant def

def run_simulation(strats: List[Strategy], noise: bool = NOISE) -> Dict[str, Dict[str, List[int]]]:
    """
    Runs the full IPD simulation.

    Takes a list  `strats` of strategies to be run.
    Optionally, whether noise is on is specified with the `noise` argument. Defaults to value in `game_specs.py`
    )
    Returns a nested dictionary that maps matchups to results.
    Example:
    ```
    out = run_simulation([SteveFunc, QuackaryFunc, JackaryFunc])
    print(out["SteveFunc"]["QuackaryFunc"]) # gives results of Steve vs. Quackary
    ```
    """
    matchups = []
    print(len(strats))
    for i,p1 in enumerate(strats):
        for j,p2 in enumerate(strats):
            if j <= i:
                continue
            matchups.append((p1, p2))
    with multiprocessing.Pool(16) as p:
        res = list(tqdm(p.imap( # NOTE imap() may be the source of the slowness...?
            play_match,
            [pack_functions(x) for x in matchups],
        ), total=len(matchups)))
    output = defaultdict(dict)
    for i,x in enumerate(matchups):
        match_res = res[i]
        if match_res == None:
            continue
        output[x[0].__name__][x[1].__name__] = match_res
        output[x[1].__name__][x[0].__name__] = list(reversed(match_res))
    return output
