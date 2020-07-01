"""
Tic Tac Toe Player
"""

import math
import copy
import sys

X = "X"
O = "O"
EMPTY = None


def initial_state():
    """
    Returns starting state of the board.
    """
    return [[EMPTY, EMPTY, EMPTY],
            [EMPTY, EMPTY, EMPTY],
            [EMPTY, EMPTY, EMPTY]]


def player(board):
    """
    Returns player who has the next turn on a board.
    """
    x_count = 0
    o_count = 0
    for i in range(0, len(board)):
        for j in range(0, len(board)):
            if board[i][j] == X:
                x_count += 1
            elif board[i][j] == O:
                o_count += 1
    if x_count == 0 and o_count == 0:
        return X
    elif x_count > o_count:
        return O
    return X


def actions(board):
    """
    Returns set of all possible actions (i, j) available on the board.
    """
    actions = set()
    for i in range(0, len(board)):
        for j in range(0, len(board)):
            if board[i][j] == EMPTY:
                actions.add((i,j))
    return actions


def result(board, action):
    """
    Returns the board that results from making move (i, j) on the board.
    """
    new_board = copy.deepcopy(board)
    try:
        if new_board[action[0]][action[1]] == EMPTY:
            new_board[action[0]][action[1]] = player(new_board)
        return new_board
    except:
        raise Exception("This action is invalid")


def winner(board):
    """
    Returns the winner of the game, if there is one.
    """
    tmp_board = copy.deepcopy(board)
    tmp_board = [j for sub in tmp_board for j in sub]
    for i in range(0, len(board) * 3, 3):
        if checkline(i, i + 1, i + 2, tmp_board, X):
            return X
        elif checkline(i, i + 1, i + 2, tmp_board, O):
            return O
    for i in range(0, len(board)):
        if checkline(i, i + 3, i + 6, tmp_board,  X):
            return X
        elif checkline(i, i + 3, i + 6, tmp_board, O):
            return O
    if checkline(0, 4, 8, tmp_board, X):
        return X
    if checkline(0, 4, 8, tmp_board, O):
        return O
    if checkline(2, 4, 6, tmp_board, X):
        return X
    if checkline(2, 4, 6, tmp_board, O):
        return O
    return None
    

def checkline(a, b , c, tmp_board, player):
    return tmp_board[a] == tmp_board[b] and \
        tmp_board[b] == tmp_board[c] and \
            tmp_board[a] == player


def terminal(board):
    """
    Returns True if game is over, False otherwise.
    """
    if winner(board):
        return True
    for row in board:
        for val in row:
            if not val:
                return False
    return True


def utility(board):
    """
    Returns 1 if X has won the game, -1 if O has won, 0 otherwise.
    """
    if winner(board) == X:
        return 1
    elif winner(board) == O:
        return -1
    return 0


def minimax(board):
    """
    Returns the optimal action for the current player on the board.
    """
    if terminal(board):
        return None
    if player(board) == X:
        score = -math.inf
        best_action = None
        for action in actions(board):
            v = minvalue(result(board, action))
            if v > score:
                score = v
                best_action = action
        return best_action
    elif player(board) == O:
        score = math.inf
        best_action = None
        for action in actions(board):
            v = maxvalue(result(board, action))
            if v < score:
                score = v
                best_action = action
        return best_action
        

def maxvalue(board):
    if terminal(board):
        return utility(board)
    v = -math.inf
    for action in actions(board):
        v = max(v, minvalue(result(board, action)))
    return v

def minvalue(board):
    if terminal(board):
        return utility(board)
    v = math.inf
    for action in actions(board):
        v = min(v, maxvalue(result(board, action)))
    return v