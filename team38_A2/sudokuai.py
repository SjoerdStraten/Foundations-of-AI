#  (C) Copyright Wieger Wesselink 2021. Distributed under the GPL-3.0-or-later
#  Software License, (See accompanying file LICENSE or copy at
#  https://www.gnu.org/licenses/gpl-3.0.txt)

import random
# import time
from competitive_sudoku.sudoku import GameState, Move, SudokuBoard, TabooMove, print_board
import competitive_sudoku.sudokuai

# Extra packages:
import numpy as np
import math
from copy import deepcopy

class SudokuAI(competitive_sudoku.sudokuai.SudokuAI):
    """
    Sudoku AI that computes a move for a given sudoku configuration, based on minimax algo.
    """
    def __init__(self):
        super().__init__()

    def compute_best_move(self, game_state: GameState) -> None:

        N = game_state.board.N
        N_empty_squares = game_state.board.squares.count(0)
        N_total_squares = N*N
        fraction_filled = 1 - N_empty_squares/N_total_squares
        print('Filled:', fraction_filled, '\n')

        #HEURISTIC 1: MOVE BASED ON THE FRACTION THAT IS FILLED
        if fraction_filled >=0 and fraction_filled <0.2:
            print('RANDOM MOVE\n')

            # Determine if a certain move is non-taboo in a certain gamestate
            def non_taboo(i, j, value):
                """Checks if the move is non-taboo.
                @param i: index for the row of the move
                @param j: index for the column of the move
                @param value: the value of the move
                """
                return game_state.board.get(i, j) == SudokuBoard.empty \
                    and not Move(i, j, value) in game_state.taboo_moves
        
            # Create a list of the gamestate board's rows and a list of its columns (used in legal function)
            board_str = game_state.board.squares
            rows = []
            for i in range(N):
                rows.append(board_str[i*N : (i+1)*N])
            columns = np.transpose(rows)

            # Determine if action is legal (not already present in section, row or column)
            def legalMove(i: int, j: int, value: int, data: list):
                """Checks if the move is legal
                @param i: index for the row of the move
                @param j: index for the column of the move
                @param value: the value of the move
                @param data: the current state in a list 
                """

                size_row = math.floor(np.sqrt(len(data)))
                size_col = math.ceil(np.sqrt(len(data)))
                row = math.floor(i/size_row)
                col = math.floor(j/size_col)
                y= np.vstack([xi for xi in data])
                return not value in np.array(y[row*size_row:row*size_row+size_row,col*size_col \
                    :col*size_col+size_col]).reshape(-1,).tolist() and not value in rows[i] and not value in columns[j]
    
            # Generate a list of all possible moves (legal AND non-taboo)
            possible_moves = []
            for i in range(N):
                for j in range(N):
                    for value in range(1, N+1):
                        if non_taboo(i, j, value):
                            if legalMove(i, j, value, rows):
                                possible_moves.append(Move(i, j, value))

            self.propose_move(possible_moves[0])

        # If board is partly filled but far from totally filled, use best Last Possible Number move:
        if fraction_filled >=0.2 and fraction_filled <0.4:
            print('LAST POSSIBLE NUMBER HEURISTIC\n')

            # Define the rows, columns and sections of the current board
            board = game_state.board
            board_str = board.squares
            rows = []
            N = game_state.board.N
            for i in range(N):
                rows.append(board_str[i*N : (i+1)*N])
            columns = list(np.transpose(rows))
            sections = np.vstack([xi for xi in rows])

            def scoreFunction(move, game_state):
                """Calculates a score for a given move.
                @param move: the given move
                @param game_state: the current gamestate
                """

                # Make copies of the board's rows, columns and sections
                columns = np.transpose(rows)
                current_rows = deepcopy(rows)
                current_columns = deepcopy(columns)

                # Check if current rows and columns are already completed
                current_row_complete = not 0 in current_rows[move.i]
                current_column_complete = not 0 in current_columns[move.j]

                # Fill in the move and define the new rows and columns
                new_rows = deepcopy(current_rows)
                new_rows[move.i][move.j] = move.value
                new_columns = np.transpose(new_rows)

                # Check if the new rows and columns are completed
                new_row_complete = not 0 in new_rows[move.i]
                new_column_complete = not 0 in new_columns[move.j]
                
                # Check if a row and/or column has been completed by the current move
                count = 0
                if new_row_complete and not current_row_complete:
                    count += 1
                if new_column_complete and not current_column_complete: 
                    count += 1

                # Define the move's sections
                root_row = np.sqrt(len(current_rows))
                size_row = int(root_row // 1)
                root_col = np.sqrt(len(current_rows))
                size_col = int(-1 * root_col // 1 * -1)
                prep_row = move.i/size_row
                row = int(prep_row // 1)
                prep_col = move.j/size_col
                col = int(prep_col // 1)
                y= np.vstack([xi for xi in current_rows])           
                current_section = np.array(y[row*size_row:row*size_row+size_row,col*size_col:col*size_col+size_col]).reshape(-1,).tolist()
                
                # Check if the move completes a section
                if current_section.count(0) == 1:
                    count += 1
                
                # Appoint a score to the move and return an integer
                score = 0

                if count == 0:
                    score = 0
                elif count == 1:
                    score = 1
                elif count == 2:
                    score = 3
                elif count == 3:
                    score = 7
                return int(score)

            def not_possible(i, j):
                """For a given square check what numbers can not be filled in.
                @param i: the index of the row
                @param j: the index of the column
                """

                # Define the row and column of the square
                row_i = set(rows[i])
                col_j = set(columns[j])

                # Define the section of the square
                root_row = np.sqrt(len(rows))
                size_row = int(root_row // 1)
                root_col = np.sqrt(len(rows))
                size_col = int(-1 * root_col // 1 * -1)
                prep_row = i/size_row
                row = int(prep_row // 1)
                prep_col = j/size_col
                col = int(prep_col // 1)

                section = set(np.array(sections[row*size_row:row*size_row+size_row,col*size_col:col*size_col+size_col]).reshape(-1,).tolist())

                # Define the total set of numbers that are not possible and return it
                total_set = row_i.union(col_j)
                total_set = total_set.union(section)
                total_set.remove(0)

                return total_set

            # For all empty squares check if there is only a single possible move 
            # and if so, add it to the list single_possibility_moves

            single_possibility_moves = []
            for i in range(N):
                for j in range(N):
                    if game_state.board.get(i, j) == SudokuBoard.empty:
                        if len(not_possible(i,j)) == N-1:
                            set_possible_values = set()
                            for number in range(1,N+1):
                                set_possible_values.add(number)
                            move_value = set_possible_values - not_possible(i,j)
                            move_value = list(move_value)[0]
                            print('Coordinates:', f'({i},{j})')
                            print('Not possible values:', not_possible(i,j))
                            print('Remaining value:', move_value)
                            move = Move(i, j, move_value)
                            score = scoreFunction(move, game_state)
                            print(move, 'Score', score,'\n')
                            single_possibility_moves.append((move, score))
                            # print('We got a single possibility! Proposed move:', move)
            
            # Propose the single possibility move that gets the highest reward
            max_score = 0
            best_move = Move(0, 0, 0)
            for move in single_possibility_moves:
                if move[1] >= max_score:
                    max_score = move[1]
                    best_move = move[0]
            self.propose_move(best_move)

            # If no single possibility move has been found, propose the first possible move

            def non_taboo(i, j, value):
                return game_state.board.get(i, j) == SudokuBoard.empty \
                    and not Move(i, j, value) in game_state.taboo_moves
            
            def legal(i,j,value,data):
                
                root_row = np.sqrt(len(data))
                size_row = int(root_row // 1)
                root_col = np.sqrt(len(data))
                size_col = int(-1 * root_col // 1 * -1)
                prep_row = i/size_row
                row = int(prep_row // 1)
                prep_col = j/size_col
                col = int(prep_col // 1)

                y= np.vstack([xi for xi in data])
                return not value in np.array(y[row*size_row:row*size_row+size_row,col*size_col \
                    :col*size_col+size_col]).reshape(-1,).tolist() and not value in rows[i] and not value in columns[j]

            if best_move.value == 0:
                print('No single possibility! Picking first possible move')
                for i in range(N):
                    for j in range(N):
                        for value in range(1, N+1):
                            if non_taboo(i, j, value):
                                if legal(i, j, value, rows):
                                    move = Move(i, j, value)
                                    self.propose_move(move)

        # # If board is over x% filled, use Minimax with depth=2:
        if fraction_filled >= 0.4:
            print('MINIMAX DEPTH=2\n')

            def compute_possible_moves(game_state):
                # Determine if a certain move is non-taboo in a certain gamestate
                def non_taboo(i, j, value):
                    return game_state.board.get(i, j) == SudokuBoard.empty \
                        and not Move(i, j, value) in game_state.taboo_moves

                # Create a list of the gamestate board's rows and a list of its columns (used in legal function)
                board_str = game_state.board.squares
                rows = []
                N = game_state.board.N
                for i in range(N):
                    rows.append(board_str[i*N : (i+1)*N])
                columns = np.transpose(rows)
                
                # Determine if action is legal (not already present in section, row or column)
                def legal(i,j,value,data):
                    
                    root_row = np.sqrt(len(data))
                    size_row = int(root_row // 1)
                    root_col = np.sqrt(len(data))
                    size_col = int(-1 * root_col // 1 * -1)
                    prep_row = i/size_row
                    row = int(prep_row // 1)
                    prep_col = j/size_col
                    col = int(prep_col // 1)
                    y= np.vstack([xi for xi in data])
                    return not value in np.array(y[row*size_row:row*size_row+size_row,col*size_col \
                        :col*size_col+size_col]).reshape(-1,).tolist() and not value in rows[i] and not value in columns[j]
            
                # Generate a list of all possible moves (legal AND non-taboo)
                possible_moves = []

                for i in range(N):
                    for j in range(N):
                        for value in range(1, N+1):
                            if non_taboo(i, j, value):
                                if legal(i, j, value, rows):
                                    possible_moves.append(Move(i, j, value))

                # Create copies of the current board's rows and columns, for use in the for loop below
                current_rows = deepcopy(rows)
                current_columns = deepcopy(columns)

                possible_moves_scores = []

                # Select the move that leads to the maximal score
                for move in possible_moves:

                    # Check if a row, column, or both are completed by a certain move
                    # and if so: add 1 to the counter
                    current_row_complete = not 0 in current_rows[move.i]
                    current_column_complete = not 0 in current_columns[move.j]

                    new_rows = deepcopy(current_rows)
                    new_rows[move.i][move.j] = move.value
                    new_columns = np.transpose(new_rows)

                    new_row_complete = not 0 in new_rows[move.i]
                    new_column_complete = not 0 in new_columns[move.j]
                        
                    count = 0
                    if new_row_complete and not current_row_complete:
                        count += 1
                    if new_column_complete and not current_column_complete: 
                        count += 1

                    # Check if a section is completed, and if so add 1 to the counter
                    root_row = np.sqrt(len(current_rows))
                    size_row = int(root_row // 1)
                    root_col = np.sqrt(len(current_rows))
                    size_col = int(-1 * root_col // 1 * -1)
                    prep_row = move.i/size_row
                    row = int(prep_row // 1)
                    prep_col = move.j/size_col
                    col = int(prep_col // 1)

                    y= np.vstack([xi for xi in current_rows])           
                    current_section = np.array(y[row*size_row:row*size_row+size_row,col*size_col:col*size_col+size_col]).reshape(-1,).tolist()
                                
                    if current_section.count(0) == 1:
                        count += 1

                    # Create a list containing tuples of moves and their score counts
                    if count == 0:
                        possible_moves_scores.append((move, 0))
                    if count == 1:
                        possible_moves_scores.append((move, 1))
                    if count == 2:
                        possible_moves_scores.append((move, 3))
                    if count == 3:
                        possible_moves_scores.append((move, 7))

                return [possible_moves, possible_moves_scores]

            current_game_state = deepcopy(game_state)
            possible_moves_scores = compute_possible_moves(current_game_state)
            possible_moves_scores = possible_moves_scores[1]

            # Select first possible move
            self.propose_move(possible_moves_scores[0][0])

            possible_moves_new_scores = []
            for move in possible_moves_scores:
                print('\nPLAYER 1 MOVE:', move[0], 'Score:', move[1])
               
                new_game_state = deepcopy(current_game_state)
                new_game_state.board.put(move[0].i, move[0].j, move[0].value)

                # Compute possible moves for opponent based on new board
                opp_possible_moves_scores = compute_possible_moves(new_game_state)
                opp_possible_moves_scores = opp_possible_moves_scores[1]

                max_opp_score = 0
                for opp_move in opp_possible_moves_scores:
                    print('Player 2 possible move:', f'({opp_move[0].i},{opp_move[0].j}) -> {opp_move[0].value}', 'Score:', opp_move[1])
                    if opp_move[1] > max_opp_score:
                        max_opp_score = opp_move[1]
                
                move = list(move)
                move[1] = move[1] - max_opp_score
                possible_moves_new_scores.append(tuple(move))
                print('New score:', move[1])

            # Select the move with the highest score difference
            best_score = -math.inf
            for move in possible_moves_new_scores:
                score = move[1]
                if score > best_score:
                    best_score = score
                    self.propose_move(move[0])
            print('\nBest new score:', best_score)