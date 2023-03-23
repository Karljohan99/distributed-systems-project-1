import random


class TicTacToe:

    def __init__(self):
        self.board = [''] * 9

    def get_board(self):
        return self.board

    def first_turn(self):
        return random.randint(0, 1)

    def make_move(self, slot, symbol):
        if self.board == '':
            self.board[slot] = symbol
            return True
        return False

    def check_winner(self, mark):
        return ((self.board[0][0] == mark and self.board[0][1] == mark and self.board[0][2] == mark) or  # row 1
                (self.board[1][0] == mark and self.board[1][1] == mark and self.board[1][2] == mark) or  # row 2
                (self.board[2][0] == mark and self.board[2][1] == mark and self.board[2][2] == mark) or  # row 3
                (self.board[0][0] == mark and self.board[1][0] == mark and self.board[2][0] == mark) or  # column 1
                (self.board[0][1] == mark and self.board[1][1] == mark and self.board[2][2] == mark) or  # for Colm 2
                (self.board[0][2] == mark and self.board[1][2] == mark and self.board[2][2] == mark) or  # for colm 3
                (self.board[0][0] == mark and self.board[1][1] == mark and self.board[2][2] == mark) or  # diag 1
                (self.board[0][2] == mark and self.board[1][1] == mark and self.board[2][0] == mark))  # diag 2

