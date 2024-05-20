# pipe.py: Template para implementação do projeto de Inteligência Artificial 2023/2024.
# Devem alterar as classes e funções neste ficheiro de acordo com as instruções do enunciado.
# Além das funções e classes sugeridas, podem acrescentar outras que considerem pertinentes.

# Grupo 18:
# 102707 Tomás Correia
# 103902 Luís Pereira

import sys
from search import (
    Problem,
    Node,
    astar_search,
    breadth_first_tree_search,
    depth_first_tree_search,
    greedy_search,
    recursive_best_first_search,
)

class PipeManiaState:
    state_id = 0

    def __init__(self, board, position=None):
        self.board = board
        self.position = position if position is not None else (0, 0)
        self.id = PipeManiaState.state_id
        PipeManiaState.state_id += 1

    def __lt__(self, other):
        return self.id < other.id

    def __eq__(self, other):
        return self.board == other.board and self.position == other.position

    def __hash__(self):
        # Convert each row from list to tuple, and the board to a tuple of tuples
        tuple_board = tuple(tuple(row) for row in self.board.board)
        return hash((tuple_board, tuple(self.position)))


    # Add a method to print the board for debugging
    def print_board(self):
        for row in self.board.board:
            print('\t'.join(row))

class Board:
    """Representação interna de um tabuleiro de PipeMania."""

    pieces = {
        "Fecho": {
            "FC",
            "FB",
            "FE",
            "FD"
        },
        "Bifurcacao": {
            "BC",
            "BB",
            "BE",
            "BD"
        },
        "Volta": {
            "VC",
            "VB",
            "VE",
            "VD"
        },
        "Ligacao": {
            "LH",
            "LV"
        }
    }

    rotate_directions = ['clockwise', 'counterclockwise']
    directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]

    def __init__(self, board, rows, cols):
        self.board = [list(row) for row in board]  # This should be a list of lists for internal manipulation
        self.rows = rows
        self.cols = cols
        self.impossible_pieces = [[] for _ in range(rows * cols)]
        self.connection_counts = [0] * (rows * cols)
        self.init_board()

    def init_board(self):
        for row in range(self.rows):
            for col in range(self.cols):
                self.correct_corners(row, col)
        for row in range(self.rows):
            for col in range(self.cols):
                self.correct_margins(row, col)
        self.board = tuple(tuple(row) for row in self.board)  # Ensure it is converted to a tuple of tuples

    def get_value(self, row: int, col: int) -> str:
        """Devolve o valor na respetiva posição do tabuleiro."""
        if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
            return None
        else:
            return self.board[row][col]

    def set_value(self, row: int, col: int, value: str):
        """Define o valor na respetiva posição do tabuleiro."""
        self.board = [list(row) for row in self.board]  # Convert to list of lists for manipulation
        self.board[row][col] = value

    # Funcoes de verificaçao de posiçoes de peças

    def adjacent_vertical_values(self, row: int, col: int) -> (str, str):
        """Devolve os valores imediatamente acima e abaixo,
        respectivamente."""
        row_above = None
        row_below = None
        if row > 0:
            row_above = self.get_value(row - 1, col)
        if row < self.rows - 1:
            row_below = self.get_value(row + 1, col)
        return row_above, row_below

    def adjacent_horizontal_values(self, row: int, col: int) -> (str, str):
        """Devolve os valores imediatamente à esquerda e à direita,
        respectivamente."""
        left_col = None
        right_col = None
        if col > 0:
            left_col = self.get_value(row, col - 1)
        if col < self.cols - 1:
            right_col = self.get_value(row, col + 1)
        return left_col, right_col

    def on_corner(self, row: int, col: int) -> bool:
        """Verifica se a peça na posição (row, col) está num canto."""
        if (row == 0 or row == self.rows - 1) and (col == 0 or col == self.cols - 1):
            return True
        return False

    def on_margin(self, row: int, col: int) -> bool:
        """Verifica se a peça na posição (row, col) está uma margem."""
        if row == 0 or row == self.rows - 1 or col == 0 or col == self.cols - 1:
            return True
        return False

    def add_impossible_piece(self, row, col, piece_type):
        """Adiciona uma peça impossível à lista de peças impossíveis."""
        position_index = row * self.cols + col
        self.impossible_pieces[position_index].append(piece_type)

    def get_impossible_pieces(self, row, col):
        """Devolve a lista de peças impossiveis para a posiçao pedida."""
        position_index = row * self.cols + col
        return self.impossible_pieces[position_index]

    def possible_connections(self, row: int, col: int):
        """ Devolve o numero de conexoes possiveis dependendo do tipo de peça."""
        piece = self.get_value(row, col)
        if piece in ["FC", "FD", "FB", "FE"]:
            return 1
        elif piece in ["VC", "VD", "VB", "VE"]:
            return 2
        elif piece in ["BC", "BD", "BB", "BE"]:
            return 3
        elif piece in ["LH", "LV"]:
            return 2
        return 0


    def is_piece_connected(self, row: int, col: int) -> bool:
        """ Verifica se a peça na posição (row, col) está conectada."""
        piece = self.get_value(row, col)
        position_index = row * self.cols + col
        if piece in ["FC", "FD", "FB", "FE"]:
            return self.connection_counts[position_index] == 1
        elif piece in ["VC", "VD", "VB", "VE"]:
            if self.connection_counts[position_index] == 2:
                #    print("PIECE CONNECTED!")
                return True
        elif piece in ["BC", "BD", "BB", "BE"]:
            return self.connection_counts[position_index] == 3
        elif piece in ["LH", "LV"]:
            return self.connection_counts[position_index] == 2
        return False

    def count_board_connections(self):
        """Conta o numero de conexões no tabuleiro."""

        count = 0
        for row in range(self.rows):
            for col in range(self.cols):
                position_index = row * self.cols + col
                #print("ROW: ", row, "COL: ", col, "COUNT: ", self.connection_counts[position_index])
                count += self.connection_counts[position_index]
        #    print("COUNT: ", count)
        return count


    def correct_corners(self, row: int, col: int):
        """ Coloca as peças dos cantos corretamente."""
        current_value = self.get_value(row, col)
        if row == 0 and col == 0:
            if current_value in self.pieces["Fecho"]:
                self.add_impossible_piece(row, col, "FC")
                self.add_impossible_piece(row, col, "FE")
                if current_value == "FC" or current_value == "FE":
                    self.set_value(row, col, "FB")
            elif current_value in self.pieces["Volta"]:
                self.add_impossible_piece(row, col, "VC")
                self.add_impossible_piece(row, col, "VD")
                self.add_impossible_piece(row, col, "VE")
                self.set_value(row, col, "VB")

        if row == 0 and col == self.cols - 1:
            if current_value in self.pieces["Fecho"]:
                self.add_impossible_piece(row, col, "FC")
                self.add_impossible_piece(row, col, "FD")
                if current_value == "FC" or current_value == "FD":
                    self.set_value(row, col, "FB")
            elif current_value in self.pieces["Volta"]:
                self.add_impossible_piece(row, col, "VC")
                self.add_impossible_piece(row, col, "VD")
                self.add_impossible_piece(row, col, "VB")
                self.set_value(row, col, "VE")

        if row == self.rows - 1 and col == 0:
            if current_value in self.pieces["Fecho"]:
                self.add_impossible_piece(row, col, "FB")
                self.add_impossible_piece(row, col, "FE")
                if current_value == "FB" or current_value == "FE":
                    self.set_value(row, col, "FC")
            elif current_value in self.pieces["Volta"]:
                self.add_impossible_piece(row, col, "VB")
                self.add_impossible_piece(row, col, "VC")
                self.add_impossible_piece(row, col, "VE")
                self.set_value(row, col, "VD")

        if row == self.rows - 1 and col == self.cols - 1:
            if current_value in self.pieces["Fecho"]:
                self.add_impossible_piece(row, col, "FB")
                self.add_impossible_piece(row, col, "FD")
                if current_value == "FB" or current_value == "FD":
                    self.set_value(row, col, "FC")
            elif current_value in self.pieces["Volta"]:
                self.add_impossible_piece(row, col, "VB")
                self.add_impossible_piece(row, col, "VD")
                self.add_impossible_piece(row, col, "VE")
                self.set_value(row, col, "VC")

    def correct_margins(self, row: int, col: int):
        """ Coloca as peças das margens corretamente."""
        current_value = self.get_value(row, col)
        if row == 0 and col != 0 and col != self.cols - 1:
            if current_value in self.pieces["Fecho"]:
                self.add_impossible_piece(row, col, "FC")
                if current_value == "FC":
                    self.set_value(row, col, "FE")
            elif current_value in self.pieces["Volta"]:
                self.add_impossible_piece(row, col, "VC")
                self.add_impossible_piece(row, col, "VD")
                if current_value == "VC" or current_value == "VD":
                    self.set_value(row, col, "VE")
            elif current_value in self.pieces["Ligacao"]:
                self.add_impossible_piece(row, col, "LV")
                self.set_value(row, col, "LH")
            elif current_value in self.pieces["Bifurcacao"]:
                self.add_impossible_piece(row, col, "BC")
                self.add_impossible_piece(row, col, "BD")
                self.add_impossible_piece(row, col, "BE")
                self.set_value(row, col, "BB")

        if row == self.rows - 1 and col != 0 and col != self.cols - 1:
            if current_value in self.pieces["Fecho"]:
                self.add_impossible_piece(row, col, "FB")
                if current_value == "FB":
                    self.set_value(row, col, "FD")
            elif current_value in self.pieces["Volta"]:
                self.add_impossible_piece(row, col, "VB")
                self.add_impossible_piece(row, col, "VE")
                if current_value == "VB" or current_value == "VE":
                    self.set_value(row, col, "VC")
            elif current_value in self.pieces["Bifurcacao"]:
                self.add_impossible_piece(row, col, "BB")
                self.add_impossible_piece(row, col, "BD")
                self.add_impossible_piece(row, col, "BE")
                self.set_value(row, col, "BC")
            elif current_value in self.pieces["Ligacao"]:
                self.add_impossible_piece(row, col, "LV")
                self.set_value(row, col, "LH")

        if col == 0 and row != 0 and row != self.rows - 1:
            if current_value in self.pieces["Fecho"]:
                self.add_impossible_piece(row, col, "FE")
                if current_value == "FE":
                    self.set_value(row, col, "FB")
            elif current_value in self.pieces["Volta"]:
                self.add_impossible_piece(row, col, "VE")
                self.add_impossible_piece(row, col, "VC")
                if current_value == "VE" or current_value == "VC":
                    self.set_value(row, col, "VD")
            elif current_value in self.pieces["Bifurcacao"]:
                self.add_impossible_piece(row, col, "BE")
                self.add_impossible_piece(row, col, "BB")
                self.add_impossible_piece(row, col, "BC")
                self.set_value(row, col, "BD")
            elif current_value in self.pieces["Ligacao"]:
                self.add_impossible_piece(row, col, "LH")
                self.set_value(row, col, "LV")

        if col == self.cols - 1 and row != 0 and row != self.rows - 1:
            if current_value in self.pieces["Fecho"]:
                self.add_impossible_piece(row, col, "FD")
                if current_value == "FD":
                    self.set_value(row, col, "FB")
            elif current_value in self.pieces["Volta"]:
                self.add_impossible_piece(row, col, "VD")
                self.add_impossible_piece(row, col, "VB")
                if current_value == "VD" or current_value == "VB":
                    self.set_value(row, col, "VE")
            elif current_value in self.pieces["Bifurcacao"]:
                self.add_impossible_piece(row, col, "BD")
                self.add_impossible_piece(row, col, "BB")
                self.add_impossible_piece(row, col, "BC")
                self.set_value(row, col, "BE")
            elif current_value in self.pieces["Ligacao"]:
                self.add_impossible_piece(row, col, "LH")
                self.set_value(row, col, "LV")



    def is_connected(self, pos1: tuple, pos2: tuple) -> bool:
        row1, col1 = pos1
        row2, col2 = pos2
        position_index1 = row1 * self.cols + col1

        # Check if the positions are adjacent
        if abs(row1 - row2) + abs(col1 - col2) != 1:
            return False

        # Check if the pieces are connected based on their types
        piece1 = self.get_value(row1, col1)
        piece2 = self.get_value(row2, col2)
        #    print("PIECE1: ", piece1, "PIECE2: ", piece2, "COL1:", col1, "COL2:", col2)

        # Ensure piece1 is always the piece on the left or above
        """if row1 > row2 or col1 > col2:
            row1, col1, row2, col2 = row2, col2, row1, col1
            piece1, piece2 = piece2, piece1
            position_index1 = row1 * self.cols + col1"""
        #print(self.get_impossible_pieces(row1, col1), row1, col1, piece1)
        if row1 == row2:  # Horizontal connection
            if col1 < col2:  # piece1 is right-oriented
                if piece1 == "FD" and piece2 in ["BC", "BB", "BE", "VC", "VE", "LH"]:
                    self.connection_counts[position_index1] += 1
                    return True
                if piece1 in ["VB", "BD", "BB", "BC", "VD", "LH"] and piece2 in ["BC", "BB", "BE", "VC", "VE", "LH", "FE"]:
                    self.connection_counts[position_index1] += 1
                    #    print(f"Connection Counts {piece1}", self.connection_counts[position_index1])
                    return True
                if piece1 == "FD" and piece2 in self.pieces["Fecho"]:
                    self.add_impossible_piece(row1, col1, "FD")

            if col1 > col2:  # piece1 is left-oriented
                if piece1 == "FE" and piece2 in ["BC", "BB", "BD", "VB", "VD", "LH"]:
                    self.connection_counts[position_index1] += 1
                    return True
                if piece1 in ["VE", "BE", "BB", "BC", "VC", "LH"] and piece2 in ["BC", "BB", "BD", "VB", "VD", "LH", "FD"]:
                    #    print(f"Connection Counts {piece1}", self.connection_counts[position_index1])
                    self.connection_counts[position_index1] += 1
                    return True
                if piece1 == "FE" and piece2 in self.pieces["Fecho"]:
                    self.add_impossible_piece(row1, col1, "FE")
            return False


        elif col1 == col2:  # Vertical connection

            #    print("Equal col, row1:", row1, "row2:", row2, "piece1:", piece1, "piece2:", piece2)
            if row1 > row2:  # piece1 is top-oriented
                if piece1 in ["BE", "BD", "BC", "VC", "VD", "LV"] and piece2 in ["BD", "BB", "BE", "VB", "VE", "LV", "FB"]:
                    self.connection_counts[position_index1] += 1
                    return True
                if piece1 == "FC" and piece2 in ["BB", "BE", "BD", "VB", "VE", "LV"]:
                    self.connection_counts[position_index1] += 1
                    return True
                if piece1 == "FC" and piece2 in self.pieces["Fecho"]:
                    self.add_impossible_piece(row1, col1, "FC")

            if row1 < row2:  # piece1 is bottom-oriented
                if piece1 in ["BE", "BD", "BB", "VB", "VE", "LV"] and piece2 in ["BD", "BE", "BC", "VC", "VD", "LV", "FC"]:
                    self.connection_counts[position_index1] += 1
                    return True
                if piece1 == "FB" and piece2 in ["BC", "BE", "BD", "VC", "VD", "LV"]:
                    self.connection_counts[position_index1] += 1
                    return True
                if piece1 == "FB" and piece2 in self.pieces["Fecho"]:
                    self.add_impossible_piece(row1, col1, "FB")
            return False

    #    print("RETURN FALSE")

    def valid_board(self):
        """ Verifica se um tabuleiro é valido ou não."""
        for row in range(self.rows):
            for col in range(self.cols):
                piece = self.get_value(row, col)
                #print("PIECE: ", piece, "Connection Counts: ", self.connection_counts[row * self.cols + col])
                if piece == " ":
                    continue
                position_index = row * self.cols + col
                if piece in ["VC", "VD", "VB", "VE"]:
                    if self.connection_counts[position_index] == 2:
                        continue
                    return False
                elif piece in ["BC", "BD", "BB", "BE"]:
                    if self.connection_counts[position_index] == 3:
                        continue
                    return False
                elif piece in ["LH", "LV"]:
                    if self.connection_counts[position_index] == 2:
                        continue
                    return False
                elif piece in ["FC", "FD", "FB", "FE"]:
                    if self.connection_counts[position_index] == 1:
                        continue
                    return False
        return True


    @staticmethod
    def parse_instance():
        """Lê o test do standard input (stdin) que é passado como argumento
        e retorna uma instância da classe Board."""
        line = sys.stdin.readline().strip().split()
        boardList = [line]
        for line in sys.stdin:
            boardList.append(line.strip().split())

        rows = len(boardList)
        cols = len(boardList[0])
        return Board(boardList, rows, cols)


class PipeMania(Problem):
    """Classe que representa o problema do Pipe Mania."""

    def __init__(self, initial, goal=None):
        """O estado inicial é uma lista de listas que representam o tabuleiro."""
        self.initial = PipeManiaState(initial)
        self.goal = goal

    def actions(self, state):
        """Retorna uma lista de ações possíveis a partir do estado atual."""
        actions = []
        for row in range(state.board.rows):
            for col in range(state.board.cols):
                current_value = state.board.get_value(row, col)
                for direction in Board.rotate_directions:
                    new_value = self.rotate_piece(row, col, direction)
                    if new_value != current_value:
                        actions.append((row, col, direction))
        return actions

    def result(self, state, action):
        """Retorna o estado resultante após executar a ação no estado atual."""
        row, col, direction = action
        new_board = [list(row) for row in state.board.board]
        new_board_obj = Board(new_board, state.board.rows, state.board.cols)
        current_value = new_board_obj.get_value(row, col)
        new_value = self.rotate_piece(row, col, direction)
        new_board_obj.set_value(row, col, new_value)
        """print("\n")
        print("--------------------")
        for row in new_board:
            print('\t'.join(row))
        print("--------------------")"""

        return PipeManiaState(new_board_obj, (row, col))


    def goal_test(self, state: PipeManiaState):
        connected_positions = set()
        for row in range(state.board.rows):
            for col in range(state.board.cols):
                for drow, dcol in state.board.directions:
                    adj_row, adj_col = row + drow, col + dcol
                    if 0 <= adj_row < state.board.rows and 0 <= adj_col < state.board.cols and state.board.is_connected((row, col), (adj_row, adj_col)):
                        connected_positions.add((row, col))
                        connected_positions.add((adj_row, adj_col))
                    #    print("connected", row, col, adj_row, adj_col)


        return state.board.valid_board()

    def h(self, node):
        """Função heurística que estima a distância do estado atual ao estado objetivo."""
        connections = node.state.board.count_board_connections()
        return node.state.board.rows * node.state.board.cols - (connections / 2)

    def rotate_piece(self, row, col, direction):
        """Gira uma peça no sentido horário ou anti-horário."""
        piece = self.initial.board.get_value(row, col)
        new_piece = ""
        if piece in Board.pieces["Fecho"]:
            if direction == 'clockwise':
                new_piece = {'FC': 'FD', 'FD': 'FB', 'FB': 'FE', 'FE': 'FC'}[piece]
            else:
                new_piece = {'FC': 'FE', 'FE': 'FB', 'FB': 'FD', 'FD': 'FC'}[piece]
        elif piece in Board.pieces["Bifurcacao"]:
            if direction == 'clockwise':
                new_piece = {'BC': 'BD', 'BD': 'BB', 'BB': 'BE', 'BE': 'BC'}[piece]
            else:
                new_piece = {'BC': 'BE', 'BE': 'BB', 'BB': 'BD', 'BD': 'BC'}[piece]
        elif piece in Board.pieces["Volta"]:
            if direction == 'clockwise':
                new_piece = {'VC': 'VD', 'VD': 'VB', 'VB': 'VE', 'VE': 'VC'}[piece]
            else:
                new_piece = {'VC': 'VE', 'VE': 'VB', 'VB': 'VD', 'VD': 'VC'}[piece]
        elif piece in Board.pieces["Ligacao"]:
            if piece == 'LH':
                new_piece = 'LV'
            else:
                new_piece = 'LH'
        if new_piece in board.get_impossible_pieces(row,col):
            return piece
        return new_piece


if __name__ == "__main__":
    board = Board.parse_instance()
    problem = PipeMania(board)
    goal_node = breadth_first_tree_search(problem)
    if goal_node is not None:
        #    print("Is goal?", problem.goal_test(goal_node.state))
        #    print("Solution:")
        goal_node.state.print_board()
    else:
        print("No solution found")




