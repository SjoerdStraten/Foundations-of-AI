#  (C) Copyright Wieger Wesselink 2021. Distributed under the GPL-3.0-or-later
#  Software License, (See accompanying file LICENSE or copy at
#  https://www.gnu.org/licenses/gpl-3.0.txt)
#  python simulate_game.py --first=greedy_player --second=team38_A3 --board=boards/easy-2x2.txt --time=1.0
#  python simulate_game.py --first=greedy_player --second=team38_A3 --board=boards/empty-2x2.txt --time=5.0
#  python simulate_game.py --first=greedy_player --second=team38_A3 --board=boards/random-3x3.txt --time=1.0
#  python simulate_game.py --first=team38_A1 --second=team38_A3 --board=boards/random-3x3.txt --time=1.0

import random
from competitive_sudoku.sudoku import GameState, Move, SudokuBoard, TabooMove, print_board
import competitive_sudoku.sudokuai

# Extra packages:
import numpy as np
from copy import deepcopy

class SudokuAI(competitive_sudoku.sudokuai.SudokuAI):
    """
    Sudoku AI that computes a move for a given sudoku configuration,
    based on fraction of the board that is filled.
    """

    def __init__(self):
        super().__init__()

    def compute_best_move(self, game_state: GameState) -> None:

        N = game_state.board.N
        N_empty_squares = game_state.board.squares.count(0)
        N_total_squares = N*N
        fraction_filled = 1 - N_empty_squares/N_total_squares
        print('Filled:', fraction_filled, '\n')
        N = game_state.board.N
        range_N = range(N)

        if fraction_filled < 0.2:
        # If board is partly filled but far from totally filled, use best Last Possible Number move:
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

        else:
            def emptyList(board):
                """Returns a list with all the empty squares
                @param board: the board with N**2 entries.
                """

                board = game_state.board
                empty_list = []
                for a in range(N**2):
                    i,j = SudokuBoard.f2rc(board, a)
                    if board.get(i,j) == SudokuBoard.empty:
                        empty_list.append([i,j])
                return empty_list    
                
            def extractPossibleMoves(game_state: GameState):
                """Returns the possible moves for a certain game state.
                @param game_state: the current game state 
                """

                def possible(i,j,value):
                    """Checks the move for the columns, rows and regions.
                    @param i: the row index
                    @param j: the column index
                    @param value: the value of the move
                    """
                    
                    def checkColumn(i, j,value):
                        """Checks if the column already contains the value.
                        @param i: the row index
                        @param j: the column index
                        @param value: the value of the move
                        """
                        for element_col in range_N:
                            if game_state.board.get(element_col, j) == value:
                                return False
                        return True

                    def checkRow(i, j, value):
                        """Checks if the row already contains the value.
                        @param i: the row index
                        @param j: the column index
                        @param value: the value of the move
                        """
                        for element_row in range_N:
                            if game_state.board.get(i, element_row) == value:
                                return False
                        return True
                
                    def checkRegion(i,j,value):
                        """Checks if the region already contains the value.
                        @param i: the row index
                        @param j: the column index
                        @param value: the value of the move
                        """
                        x = i - (i % game_state.board.m)
                        y = j - (j % game_state.board.n)

                        for element_col in range(game_state.board.m):
                            for element_row in range(game_state.board.n):
                                if game_state.board.get(x+element_col, y+element_row) == value:
                                    return False
                        return True

                    return not TabooMove(i,j,value) in (game_state.taboo_moves) \
                        and checkColumn(i,j,value) and checkRow(i,j,value) and checkRegion(i,j,value)


                return [Move(a[0], a[1], value) for a in emptyList(game_state) for value in range(1, N+1) if possible(a[0], a[1], value)]         

            def countFunction(move, state):
                """
                Calculates a score for each possible move.
                    @param move: an object with a position and value 
                """
                
                def colFill(i,j):
                    """Checks if the column is completed.
                    """
                    for element_col in range_N:
                        if state.board.get(element_col, j) == SudokuBoard.empty and element_col!=i:
                            return False
                    return True
                
                def rowFill(i,j):
                    """Checks if the row is completed.
                    """
                    for element_row in range_N:
                        if state.board.get(i, element_row) == SudokuBoard.empty and element_row!=j:
                            return False
                    return True
                
                def regionFill(i,j):
                    """Checks if the region is completed.
                    """
                    x = i - (i % state.board.m)
                    y = j - (j % state.board.n)

                    for a in range(state.board.m):
                        for b in range(state.board.n):
                            if state.board.get(x+a, y+b) == SudokuBoard.empty and \
                                (x+a !=i or y+b !=j):
                                return False
                    return True

                partsFilled = colFill(move.i, move.j) + rowFill(move.i, move.j) + regionFill(move.i, move.j)

                
                if partsFilled == 0:
                    return int(0)
                elif partsFilled == 1:
                    return int(1)
                elif partsFilled == 2:
                    return int(3)
                elif partsFilled == 3:
                    return int(7)

            def getChildren(state):
                """Returns for each move the new board, score and the move itself. 
                Additionally, stores outcomes to stored_scores to avoid recomputation once
                iterative deepening progresses.
                @param state: 
                """
                ls = []
                if state in stored_scores:
                    ls = stored_scores[state]

                else:
                    for move in extractPossibleMoves(state):
                        child_board = deepcopy(state)
                        child_board.board.put(move.i, move.j, move.value)
                        cnt_score = countFunction(move, state)
                        list = (child_board, cnt_score, move)
                        ls.append(list)
                    stored_scores[state] = ls

                ls.sort(key = lambda a:a[1], reverse = True)
                return ls
                
            def minimax(game_state, depth: int, isMaximisingPlayer: bool, score: int, alpha: float, beta: float):
                """Creates a tree with a given depth and returns a move.
                    @param state: the current state of the sudoku
                    @param depth: an integer indicating the depth of the tree
                    @param isMaximisingPlayer: a boolean that returns True if it is the maximising player
                    @param score: an integer that is used to continiously calculate the score
                    @param alpha: a float used for inplementing A-B Pruning
                    @param beta: a float used for inplementing A-B Pruning
                """ 
                if len(extractPossibleMoves(game_state)) == 0 or depth == 0:
                    return score, None

                children = getChildren(game_state)
                if isMaximisingPlayer:
                    maxEval = float('-inf')
                    for pairs in children:
                        score += pairs[1]
                        eval, _ = minimax(pairs[0], depth-1, False, score, alpha, beta)
                        if maxEval < eval:
                            maxEval = eval
                            end_move = pairs[2]
                        alpha = max(alpha, eval)
                        #print("eval: ", eval, "alpha: ", alpha, "beta: ", beta)
                        if beta <= alpha:
                            #print("prune")
                            break
                        score -= pairs[1]
                    print("maxEval: ", maxEval, "end_move: ", end_move, "depth: ", depth)
                    return maxEval, end_move
                
                else:
                    minEval = float('inf')
                    for pairs in children:
                        score += (pairs[1] * -1)
                        eval, _ = minimax(pairs[0], depth-1, True, score, alpha, beta)
                        if minEval > eval:
                            minEval = eval
                            end_move = pairs[2]
                        beta = min(beta, eval)
                        #print("eval: ", eval, "alpha: ", alpha, "beta: ", beta)
                        if beta <= alpha:
                            #print("prune")
                            break
                        score -= pairs[1]
                    print("minEval: ", minEval, "end_move: ", end_move, "depth: ", depth)
                    return minEval, end_move

            #initially proposing random move 
            self.propose_move(random.choice(extractPossibleMoves(game_state)))
            
            stored_scores = {}
            for d in range(1, game_state.board.squares.count(SudokuBoard.empty)+1):
                _, do_move = minimax(game_state, d, True, 0, float('-inf'), float('inf'))
                #print('iteration: ', d)
                self.propose_move(do_move)