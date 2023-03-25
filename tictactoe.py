import random


class TicTacToe:

    def __init__(self, player1, player2, game_id):
        self.board = [''] * 9
        self.move = 'X'
        self.player1 = player1
        self.player2 = player2
        self.game_id = game_id
        
        
    def next_move(self):
        if self.move == 'X':
            self.move = 'O'
        else:
            self.move = 'X'
        return self.move

    def get_board(self):
        return self.board

    def set_board(self, board):
        self.board = board
        
    def get_players(self):
        return (self.player1, self.player2)

    def first_turn(self):
        return random.randint(0, 1)

    def make_move(self, slot, symbol):
        if self.board[slot] == '':
            self.board[slot] = symbol
            return True
        return False

    def check_winner_old(self):
        return ((self.board[0] == self.board[1] == self.board[2] != '') or  # row 1
                (self.board[3] == self.board[4] == self.board[5] != '') or  # row 2
                (self.board[6] == self.board[7] == self.board[8] != '') or  # row 3
                (self.board[0] == self.board[3] == self.board[6] != '') or  # column 1
                (self.board[1] == self.board[4] == self.board[7] != '') or  # for Colm 2
                (self.board[3] == self.board[5] == self.board[8] != '') or  # for colm 3
                (self.board[0] == self.board[4] == self.board[8] != '') or  # diag 1
                (self.board[2] == self.board[4] == self.board[6] != ''))  # diag 2

    def check_winner(self, mark):
        return ((self.board[0] == mark and self.board[1] == mark and self.board[2] == mark) or  # row 1
                (self.board[3] == mark and self.board[4] == mark and self.board[5] == mark) or  # row 2
                (self.board[6] == mark and self.board[7] == mark and self.board[8] == mark) or  # row 3
                (self.board[0] == mark and self.board[3] == mark and self.board[6] == mark) or  # column 1
                (self.board[1] == mark and self.board[4] == mark and self.board[7] == mark) or  # for Colm 2
                (self.board[3] == mark and self.board[5] == mark and self.board[8] == mark) or  # for colm 3
                (self.board[0] == mark and self.board[4] == mark and self.board[8] == mark) or  # diag 1
                (self.board[2] == mark and self.board[4] == mark and self.board[6] == mark))  # diag 2