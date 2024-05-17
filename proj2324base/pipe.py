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
        return hash((tuple(map(tuple, self.board.board)), self.position))

    # Add a method to print the board for debugging
    def print_board(self):
        for row in self.board.board:
            print(' '.join(row))
        print()


class Board:
    """Representação interna de um tabuleiro de PipeMania."""

    pieces = {
        "Fecho": {
            "Cima": "FC",
            "Baixo": "FB",
            "Esquerda": "FE",
            "Direita": "FD"
        },
        "Bifurcacao": {
            "Cima": "BC",
            "Baixo": "BB",
            "Esquerda": "BE",
            "Direita": "BD"
        },
        "Volta": {
            "Cima": "VC",
            "Baixo": "VB",
            "Esquerda": "VE",
            "Direita": "VD"
        },
        "Ligacao": {
            "Horizontal": "LH",
            "Vertical": "LV"
        }
    }

    rotate_directions = ['clockwise', 'counterclockwise']
    directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]

    def __init__(self, boardList, rows, cols):
        self.board = boardList
        self.rows = rows
        self.cols = cols

    def get_value(self, row: int, col: int) -> str:
        """Devolve o valor na respetiva posição do tabuleiro."""
        if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
            return None
        else:
            return self.board[row][col]

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

    def is_corner(self, row: int, col: int, piece: str) -> bool:
        """Verifica se a peça na posição (row, col) está num canto e, se estiver, invalida posiçoes incorretas."""
        if piece not in self.pieces or piece in self.pieces["Bifurcacao"].values() or piece in self.pieces["Ligacao"].values():
            return False
        if self.on_corner(row, col) is False:
            return False
        if piece in self.pieces["Fecho"].values():
            if row == 0 and col == 0:
                if piece in ["FC", "FE"]:
                    return False
            elif row == 0 and col != 0:
                if value in ["FB", "FE"]:
                    return False
            elif row != 0 and col == 0:
                if value in ["FC", "FD"]:
                    return False
            elif row != 0 and col != 0:
                if value in ["FB", "FD"]:
                    return False
        elif piece in self.pieces["Volta"].values():
            if row == 0 and col == 0:
                if piece in ["VC", "VE", "VD"]:
                    return False
            elif row == 0 and col != 0:
                if piece in ["VB", "VE", "VC"]:
                    return False
            elif row != 0 and col == 0:
                if piece in ["VC", "VD", "VB"]:
                    return False
            elif row != 0 and col != 0:
                if piece in ["VB", "VD", "VC"]:
                    return False
        return True


    def is_connected(self, pos1: tuple, pos2: tuple) -> bool:
        row1, col1 = pos1
        row2, col2 = pos2
        # print(row1, col1, row2, col2)

        # Check if the positions are adjacent
        if abs(row1 - row2) + abs(col1 - col2) != 1:
            return False

        # Check if the pieces are connected based on their types
        piece1 = self.get_value(row1, col1)
        piece2 = self.get_value(row2, col2)
        #make sure that piece1 is always the piece on the left or above
        if row1 > row2 or col1 > col2:
            row1, col1, row2, col2 = row2, col2, row1, col1
            piece1, piece2 = piece2, piece1

        if row1 == row2:  # Horizontal connection, piece1 is right-oriented
            if col1 < col2:
                if piece1 in ["FD"] and piece2 in ["BC", "BB", "BE", "VC", "VE", "LH"]:
                    return True
                elif piece1 in ["VB"] and piece2 in ["BC", "BB", "BE", "VC", "VE", "LH", "FE"]:
                    return True
                elif piece1 in ["BD"] and piece2 in ["BC", "BB", "BE", "VC", "VE", "LH", "FE"]:
                    return True
                elif piece1 in ["BB"] and piece2 in ["BC", "BB", "BE", "VC", "VE", "LH", "FE"]:
                    return True
                elif piece1 in ["BC"] and piece2 in ["BC", "BB", "BE", "VC", "VE", "LH", "FE"]:
                   return True
                elif piece1 in ["VD"] and piece2 in ["BC", "BB", "BE", "VC", "VE", "LH", "FE"]:
                    return True
                elif piece1 in ["LH"] and piece2 in ["BC", "BB", "BE", "VC", "VE", "LH", "FE"]:
                    return True
            if col1 > col2:  # Horizontal connection, piece1 is left-oriented
                if piece1 in ["FE"] and piece2 in ["BC", "BB", "BD", "VB", "VD", "LH"]:
                    return True
                elif piece1 in ["VE"] and piece2 in ["BC", "BB", "BD", "VB", "VD", "LH", "FD"]:
                    return True
                elif piece1 in ["BE"] and piece2 in ["BC", "BB", "BD", "VB", "VD", "LH", "FD"]:
                    return True
                elif piece1 in ["BB"] and piece2 in ["BC", "BB", "BD", "VB", "VD", "LH", "FD"]:
                    return True
                elif piece1 in ["BC"] and piece2 in ["BC", "BB", "BD", "VB", "VD", "LH", "FD"]:
                    return True
                elif piece1 in ["VC"] and piece2 in ["BC", "BB", "BD", "VB", "VD", "LH", "FD"]:
                    return True
                elif piece1 in ["LH"] and piece2 in ["BC", "BB", "BD", "VB", "VD", "LH", "FD"]:
                    return True

        elif col1 == col2:  # Vertical connection
            if row1 < row2:
                if piece1 in ["BE", "BD", "BC", "VC", "VD", "LV" ] and piece2 in ["BD", "BB", "BE", "VB", "VE", "LV", "FB"]:
                    return True
                elif piece1 in ["FB"] and piece2 in ["BC", "BE", "BD", "VC", "VD", "LV"]:
                    return True
            if row1 > row2:
                if piece1 in ["BE", "BD", "BB", "VB", "VE", "LV"] and piece2 in ["BD", "BE", "BC", "VC", "VD", "LV", "FC"]:
                    return True
                elif piece1 in ["FC"] and piece2 in ["BB", "BE", "BD", "VB", "VE", "LV"]:
                    return True

        return False



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
    def __init__(self, board):
        """O construtor especifica o estado inicial."""
        self.initial = PipeManiaState(board, None)

    def actions(self, state: PipeManiaState):
        """Retorna uma lista de ações que podem ser executadas a
        partir do estado passado como argumento."""
        actions = []
        for row in range(state.board.rows):
            for col in range(state.board.cols):
                for direction in state.board.rotate_directions:
                    actions.append((row, col, direction))
        print (actions)
        return actions



    def result(self, state: PipeManiaState, action):
        # deep copy the board, check if a rotation is valid, and if it is, return the new state
        row, col, direction = action
        piece = state.board.get_value(row, col)
        new_board = [list(row) for row in state.board.board]  # Deep copy the board

        # rotate the piece
        if direction == 'clockwise':
            new_board[row][col] = self.rotate_clockwise(row, col, state)
        elif direction == 'counterclockwise':
            new_board[row][col] = self.rotate_counterclockwise(row, col, state)

        new_state = PipeManiaState(Board(new_board, state.board.rows, state.board.cols), (row, col))
        return new_state


    def goal_test(self, state: PipeManiaState):
        connected_positions = set()
        for row in range(state.board.rows):
            for col in range(state.board.cols):
                for drow, dcol in state.board.directions:
                    adj_row, adj_col = row + drow, col + dcol
                    if 0 <= adj_row < state.board.rows and 0 <= adj_col < state.board.cols:
                        connected_positions.add((row, col))
                        connected_positions.add((adj_row, adj_col))
                    #     print("connected", row, col, adj_row, adj_col)

        return len(connected_positions) == state.board.rows * state.board.cols

    def h(self, node: Node):
        state = node.state
        correct_connections = 0
        for row in range(state.board.rows):
            for col in range(state.board.cols):
                for drow, dcol in state.board.directions:
                    adj_row, adj_col = row + drow, col + dcol
                    if 0 <= adj_row < state.board.rows and 0 <= adj_col < state.board.cols and state.board.is_connected((row, col), (adj_row, adj_col)):
                        correct_connections += 1
        return -(correct_connections // 2)  # Divide by 2 to account for each connection being counted twice

    def rotate_clockwise(self, row, col, state: PipeManiaState):
        # check if the rotation is valid
        piece = self.initial.board.get_value(row, col)

        if piece == 'FC':
            if state.board.is_corner(row, col, 'FD'):
                return 'FD'
            return piece
        elif piece == 'FD':
            if state.board.is_corner(row, col, 'FB'):
                return 'FB'
            return piece
        elif piece == 'FB':
            if state.board.is_corner(row, col, 'FE'):
                return 'FE'
            return piece
        elif piece == 'FE':
            if state.board.is_corner(row, col, 'FC'):
                return 'FC'
            return piece
        elif piece == 'VC':
            if state.board.is_corner(row, col, 'VD'):
                return 'VD'
            return piece
        elif piece == 'VD':
            if state.board.is_corner(row, col, 'VB'):
                return 'VB'
            return piece
        elif piece == 'VB':
            if state.board.is_corner(row, col, 'VE'):
                return 'VE'
            return piece
        elif piece == 'VE':
            if state.board.is_corner(row, col, 'VC'):
                return 'VB'
            return piece
        elif piece == 'BC':
            return 'BD'
        elif piece == 'BD':
            return 'BB'
        elif piece == 'BB':
            return 'BE'
        elif piece == 'BE':
            return 'BC'
        elif piece == 'LH':
            return 'LV'
        elif piece == 'LV':
            return 'LH'

    def rotate_counterclockwise(self, row, col, state: PipeManiaState):

        piece = self.initial.board.get_value(row, col)

        if piece == 'FC':
            if state.board.is_corner(row, col, 'FE'):
                return 'FE'
            return piece
        elif piece == 'FE':
            if state.board.is_corner(row, col, 'FB'):
                return 'FB'
            return piece
        elif piece == 'FB':
            if state.board.is_corner(row,col, 'FD'):
                return 'FD'
            return piece
        elif piece == 'FD':
            if state.board.is_corner(row, col, 'FC'):
                return 'FC'
            return piece
        elif piece == 'VC':
            if state.board.is_corner(row, col, 'VE'):
                return 'VE'
            return piece
        elif piece == 'VE':
            if state.board.is_corner(row, col, 'VB'):
                return 'VB'
            return piece
        elif piece == 'VB':
            if state.board.is_corner(row, col, 'VD'):
                return 'VD'
            return piece
        elif piece == 'VD':
            if state.board.is_corner(row, col, 'VC'):
                return 'VC'
            return piece
        elif piece == 'BC':
            return 'BE'
        elif piece == 'BE':
            return 'BB'
        elif piece == 'BB':
            return 'BD'
        elif piece == 'BD':
            return 'BC'
        elif piece == 'LH':
            return 'LV'
        elif piece == 'LV':
            return 'LH'

if __name__ == "__main__":
    board = Board.parse_instance()
    problem = PipeMania(board)
    goal_node = astar_search(problem)
    if goal_node is not None:
        print("Is goal?", problem.goal_test(goal_node.state))
        print("Solution:")
        goal_node.state.print_board()
    else:
        print("No solution found")





