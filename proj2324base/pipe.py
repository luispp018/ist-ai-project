# Grupo 18:
# 103902 Luís Pereira
# 102707 Tomás Correia

import sys
import copy
import numpy as np
from sys import stdin
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
    unique_id = 0

    def __init__(self, layout, moves=[]):
        self.layout = layout
        self.id = PipeManiaState.unique_id
        self.moves = moves
        PipeManiaState.unique_id += 1

    def __lt__(self, other):
        return self.id < other.id

    def __eq__(self, other):
        return self.layout == other.layout and self.moves == other.moves

    def __hash__(self):
        # TODO: Implement a hash function for the PipeManiaState class (is it needed?)
        pass

class Board:

    def __init__(self):
        self.cells = np.array([])  # numpy array of Tile objects
        self.recent_tile = None

    def fetch_tile(self, row: int, col: int):
        return self.cells[row, col]

    def vertical_adjacent_values(self, row: int, col: int):
        """Returns the values immediately above and below the specified cell, respectively."""
        above = self.cells[row-1, col] if row > 0 else None
        below = self.cells[row+1, col] if row < self.cells.shape[0] - 1 else None
        return above, below

    def horizontal_adjacent_values(self, row: int, col: int):
        """Returns the values immediately to the left and right of the specified cell, respectively."""
        left = self.cells[row, col-1] if col > 0 else None
        right = self.cells[row, col+1] if col < self.cells.shape[1] - 1 else None
        return left, right

    def refresh_connections(self, row: int, col: int):

        if not (0 <= row < self.cells.shape[0]) or not (0 <= col < self.cells.shape[1]):
            return

        left_tile, right_tile = self.horizontal_adjacent_values(row, col)
        top_tile, bottom_tile = self.vertical_adjacent_values(row, col)

        tile = self.cells[row, col]
        connections = sum([
            1 if left_tile and tile.is_connected(left_tile, "left") else 0,
            1 if right_tile and tile.is_connected(right_tile, "right") else 0,
            1 if top_tile and tile.is_connected(top_tile, "up") else 0,
            1 if bottom_tile and tile.is_connected(bottom_tile, "down") else 0,
        ])

        tile.connections = connections

    @staticmethod
    def parse_instance():
        """Reads the problem instance from standard input (stdin) and returns a Board instance."""
        input_lines = sys.stdin.read().strip().split('\n')

        board = Board()
        cells = []

        for line in input_lines:
            row_tiles = [Tile(tile_str) for tile_str in line.split()]
            cells.append(row_tiles)

        board.cells = np.array(cells)

        for row_idx in range(board.cells.shape[0]):
            for col_idx in range(board.cells.shape[1]):
                tile = board.cells[row_idx, col_idx]
                if board.verify_locks(row_idx, col_idx, tile.orientation):
                    tile.locked = True

        for row_idx in range(board.cells.shape[0]):
            for col_idx in range(board.cells.shape[1]):
                board.refresh_connections(row_idx, col_idx)

        return board

    def modify_tile_orientation(self, row: int, col: int, orientation: str):
        modified_tile = self.fetch_tile(row, col)
        modified_tile.orientation = orientation
        self.recent_tile = (row, col)

    def compare_boards(self, other):
        """Compares the board with another board passed as an argument."""
        def tiles_are_equal(tile1, tile2):
            return tile1 == tile2 and tile1.locked == tile2.locked

        return np.array_equal(self.cells, other.cells, tiles_are_equal)

    def copy(self):
        duplicate_board = Board()
        duplicate_board.cells = np.copy(self.cells)
        return duplicate_board

    def row_count(self):
        """Return the number of rows in the board."""
        return self.cells.shape[0]

    def column_count(self, row):
        """Return the number of columns in a specific row."""
        return self.cells.shape[1]

    def __str__(self) -> str:
        return '\n'.join(
            '\t'.join(tile.orientation for tile in row)
            for row in self.cells
        )

    def verify_locks(self, row: int, col: int, orientation: str):
        left_tile, right_tile = self.horizontal_adjacent_values(row, col)
        top_tile, bottom_tile = self.vertical_adjacent_values(row, col)

        tile = Tile(orientation)
        zones = self.get_zones(row, col)
        conditions = self.get_conditions(tile, left_tile, right_tile, top_tile, bottom_tile)

        if self.is_corner_or_edge(zones, orientation, conditions):
            return True

        return self.is_center(orientation, conditions, left_tile, right_tile, top_tile, bottom_tile)

    def get_zones(self, row, col):
        max_row, max_col = self.cells.shape[0] - 1, self.cells.shape[1] - 1
        return {
            "leftUpperCorner": (row, col) == (0, 0),
            "rightUpperCorner": (row, col) == (0, max_col),
            "leftLowerCorner": (row, col) == (max_row, 0),
            "rightLowerCorner": (row, col) == (max_row, max_col),
            "upperEdge": row == 0 and 0 < col < max_col,
            "lowerEdge": row == max_row and 0 < col < max_col,
            "leftEdge": col == 0 and 0 < row < max_row,
            "rightEdge": col == max_col and 0 < row < max_row,
        }

    def get_conditions(self, tile, left_tile, right_tile, top_tile, bottom_tile):
        return {
            "upConnects": top_tile and top_tile.locked and tile.connects_with(top_tile, "up"),
            "downConnects": bottom_tile and bottom_tile.locked and tile.connects_with(bottom_tile, "down"),
            "leftConnects": left_tile and left_tile.locked and tile.connects_with(left_tile, "left"),
            "rightConnects": right_tile and right_tile.locked and tile.connects_with(right_tile, "right"),
            "upDoesntConnect": top_tile and top_tile.locked and not tile.connects_with(top_tile, "up"),
            "downDoesntConnect": bottom_tile and bottom_tile.locked and not tile.connects_with(bottom_tile, "down"),
            "leftDoesntConnect": left_tile and left_tile.locked and not tile.connects_with(left_tile, "left"),
            "rightDoesntConnect": right_tile and right_tile.locked and not tile.connects_with(right_tile, "right"),
        }

    def is_corner_or_edge(self, zones, orientation, conditions):
        corner_edge_locks = {
            "leftUpperCorner": self.lock_left_upper_corner,
            "rightUpperCorner": self.lock_right_upper_corner,
            "leftLowerCorner": self.lock_left_lower_corner,
            "rightLowerCorner": self.lock_right_lower_corner,
            "upperEdge": self.lock_upper_edge,
            "lowerEdge": self.lock_lower_edge,
            "leftEdge": self.lock_left_edge,
            "rightEdge": self.lock_right_edge,
        }
        for zone, lock_func in corner_edge_locks.items():
            if zones[zone]:
                return lock_func(orientation, conditions)
        return False

    def lock_left_upper_corner(self, orientation, conditions):
        return {
            "VB": True,
            "FD": conditions["downDoesntConnect"] or conditions["rightConnects"],
            "FB": conditions["downConnects"] or conditions["rightDoesntConnect"],
        }.get(orientation, False)

    def lock_right_upper_corner(self, orientation, conditions):
        return {
            "VE": True,
            "FE": conditions["downDoesntConnect"] or conditions["leftConnects"],
            "FB": conditions["downConnects"] or conditions["leftDoesntConnect"],
        }.get(orientation, False)

    def lock_left_lower_corner(self, orientation, conditions):
        return {
            "VD": True,
            "FD": conditions["upDoesntConnect"] or conditions["rightConnects"],
            "FC": conditions["upConnects"] or conditions["rightDoesntConnect"],
        }.get(orientation, False)

    def lock_right_lower_corner(self, orientation, conditions):
        return {
            "VC": True,
            "FE": conditions["upDoesntConnect"] or conditions["leftConnects"],
            "FC": conditions["upConnects"] or conditions["leftDoesntConnect"],
        }.get(orientation, False)

    def lock_upper_edge(self, orientation, conditions):
        return {
            "FB": conditions["downConnects"] or (conditions["leftDoesntConnect"] and conditions["rightDoesntConnect"]),
            "FD": conditions["rightConnects"] or (conditions["downDoesntConnect"] and conditions["leftDoesntConnect"]),
            "FE": conditions["leftConnects"] or (conditions["downDoesntConnect"] and conditions["rightDoesntConnect"]),
            "BB": True,
            "LH": True,
            "VE": conditions["leftConnects"] or conditions["rightDoesntConnect"],
            "VB": conditions["rightConnects"] or conditions["leftDoesntConnect"],
        }.get(orientation, False)

    def lock_lower_edge(self, orientation, conditions):
        return {
            "FC": conditions["upConnects"] or (conditions["leftDoesntConnect"] and conditions["rightDoesntConnect"]),
            "FD": conditions["rightConnects"] or (conditions["upDoesntConnect"] and conditions["leftDoesntConnect"]),
            "FE": conditions["leftConnects"] or (conditions["upDoesntConnect"] and conditions["rightDoesntConnect"]),
            "BC": True,
            "LH": True,
            "VC": conditions["leftConnects"] or conditions["rightDoesntConnect"],
            "VD": conditions["rightConnects"] or conditions["leftDoesntConnect"],
        }.get(orientation, False)

    def lock_left_edge(self, orientation, conditions):
        return {
            "FD": conditions["rightConnects"] or (conditions["upDoesntConnect"] and conditions["downDoesntConnect"]),
            "FB": conditions["downConnects"] or (conditions["upDoesntConnect"] and conditions["rightDoesntConnect"]),
            "FC": conditions["upConnects"] or (conditions["downDoesntConnect"] and conditions["rightDoesntConnect"]),
            "BD": True,
            "LV": True,
            "VB": conditions["downConnects"] or conditions["upDoesntConnect"],
            "VD": conditions["upConnects"] or conditions["downDoesntConnect"],
        }.get(orientation, False)

    def lock_right_edge(self, orientation, conditions):
        return {
            "FE": conditions["leftConnects"] or (conditions["upDoesntConnect"] and conditions["downDoesntConnect"]),
            "FB": conditions["downConnects"] or (conditions["upDoesntConnect"] and conditions["leftDoesntConnect"]),
            "FC": conditions["upConnects"] or (conditions["downDoesntConnect"] and conditions["leftDoesntConnect"]),
            "BE": True,
            "LV": True,
            "VC": conditions["upConnects"] or conditions["downDoesntConnect"],
            "VE": conditions["downConnects"] or conditions["upDoesntConnect"],
        }.get(orientation, False)

    def is_center(self, orientation, conditions, left_tile, right_tile, top_tile, bottom_tile):
        def check_connections(connect, doesnt_connects, tiles):
            return connect or all(doesnt_connect or (tile and tile.orientation[0] == "F") for doesnt_connect, tile in zip(doesnt_connects, tiles))

        center_conditions = {
            "FB": lambda: check_connections(
                conditions["downConnects"],
                [conditions["upDoesntConnect"], conditions["leftDoesntConnect"], conditions["rightDoesntConnect"]],
                [top_tile, left_tile, right_tile]
            ),
            "FD": lambda: check_connections(
                conditions["rightConnects"],
                [conditions["downDoesntConnect"], conditions["upDoesntConnect"], conditions["leftDoesntConnect"]],
                [bottom_tile, top_tile, left_tile]
            ),
            "FE": lambda: check_connections(
                conditions["leftConnects"],
                [conditions["downDoesntConnect"], conditions["upDoesntConnect"], conditions["rightDoesntConnect"]],
                [bottom_tile, top_tile, right_tile]
            ),
            "FC": lambda: check_connections(
                conditions["upConnects"],
                [conditions["downDoesntConnect"], conditions["leftDoesntConnect"], conditions["rightDoesntConnect"]],
                [bottom_tile, left_tile, right_tile]
            ),
            "LH": lambda: (conditions["leftConnects"] or conditions["rightConnects"]) or (conditions["upDoesntConnect"] or conditions["downDoesntConnect"]),
            "LV": lambda: (conditions["upConnects"] or conditions["downConnects"]) or (conditions["leftDoesntConnect"] or conditions["rightDoesntConnect"]),
            "BB": lambda: conditions["upDoesntConnect"] or (conditions["leftConnects"] and conditions["rightConnects"] and conditions["downConnects"]),
            "BC": lambda: conditions["downDoesntConnect"] or (conditions["leftConnects"] and conditions["rightConnects"] and conditions["upConnects"]),
            "BE": lambda: conditions["rightDoesntConnect"] or (conditions["leftConnects"] and conditions["upConnects"] and conditions["downConnects"]),
            "BD": lambda: conditions["leftDoesntConnect"] or (conditions["rightConnects"] and conditions["upConnects"] and conditions["downConnects"]),
            "VC": lambda: (
                    (conditions["upConnects"] and conditions["leftConnects"]) or
                    (conditions["leftConnects"] and conditions["downDoesntConnect"]) or
                    (conditions["upConnects"] and conditions["rightDoesntConnect"]) or
                    (conditions["downDoesntConnect"] and conditions["rightDoesntConnect"]) or
                    ((conditions["upConnects"] and top_tile and top_tile.orientation[0] == "F") and (right_tile and right_tile.orientation[0] == "F")) or
                    ((conditions["leftConnects"] and left_tile and left_tile.orientation[0] == "F") and (bottom_tile and bottom_tile.orientation[0] == "F"))
            ),
            "VD": lambda: (
                    (conditions["upConnects"] and conditions["rightConnects"]) or
                    (conditions["rightConnects"] and conditions["downDoesntConnect"]) or
                    (conditions["upConnects"] and conditions["leftDoesntConnect"]) or
                    (conditions["downDoesntConnect"] and conditions["leftDoesntConnect"]) or
                    ((conditions["upConnects"] and top_tile and top_tile.orientation[0] == "F") and (left_tile and left_tile.orientation[0] == "F")) or
                    ((conditions["rightConnects"] and right_tile and right_tile.orientation[0] == "F") and (bottom_tile and bottom_tile.orientation[0] == "F"))
            ),
            "VE": lambda: (
                    (conditions["downConnects"] and conditions["leftConnects"]) or
                    (conditions["leftConnects"] and conditions["upDoesntConnect"]) or
                    (conditions["downConnects"] and conditions["rightDoesntConnect"]) or
                    (conditions["upDoesntConnect"] and conditions["rightDoesntConnect"]) or
                    ((conditions["downConnects"] and bottom_tile and bottom_tile.orientation[0] == "F") and (right_tile and right_tile.orientation[0] == "F")) or
                    ((conditions["leftConnects"] and left_tile and left_tile.orientation[0] == "F") and (top_tile and top_tile.orientation[0] == "F"))
            ),
            "VB": lambda: (
                    (conditions["downConnects"] and conditions["rightConnects"]) or
                    (conditions["rightConnects"] and conditions["upDoesntConnect"]) or
                    (conditions["downConnects"] and conditions["leftDoesntConnect"]) or
                    (conditions["upDoesntConnect"] and conditions["leftDoesntConnect"]) or
                    ((conditions["downConnects"] and bottom_tile and bottom_tile.orientation[0] == "F") and (left_tile and left_tile.orientation[0] == "F")) or
                    ((conditions["rightConnects"] and right_tile and right_tile.orientation[0] == "F") and (top_tile and top_tile.orientation[0] == "F"))
            ),
        }

        return center_conditions.get(orientation, lambda: False)()

    def filter_moves(self, moves, row, col, tile, left_tile, right_tile, top_tile, bottom_tile):
        direction_tile_move = [
            ("left", left_tile, "FE"),
            ("right", right_tile, "FD"),
            ("up", top_tile, "FC"),
            ("down", bottom_tile, "FB")
        ]

        for direction, tile_to_check, move_code in direction_tile_move:
            if tile_to_check and ((tile_to_check.locked and not tile.connects_with(tile_to_check, direction)) or tile_to_check.orientation[0] == "F"):
                if (row, col, move_code, False) in moves:
                    moves.remove((row, col, move_code, False))



class Tile:

    direction_mapping = {
        "up": "down",
        "down": "up",
        "left": "right",
        "right": "left"
    }

    open_directions = {
        "BC": ["up", "left", "right"],
        "BE": ["up", "down", "left"],
        "BD": ["up", "down", "right"],
        "VC": ["up", "left"],
        "VD": ["up", "right"],
        "LV": ["up", "down"],
        "FC": ["up"],
        "VB": ["down", "right"],
        "VE": ["down", "left"],
        "FB": ["down"],
        "LH": ["left", "right"],
        "BB": ["down", "right", "left"],
        "FD": ["right"],
        "FE": ["left"],
    }

    def __init__(self, orientation, connections=0, locked=False):
        self.orientation = orientation
        self.connections = connections
        self.locked = locked

    def max_connections(self):
        orientation_type = self.orientation[0]
        if orientation_type == "F":
            return 1
        elif orientation_type == "L":
            return 2
        elif orientation_type == "B":
            return 3
        elif orientation_type == "V":
            return 2

    def is_all_connected(self):
        orientation_type = self.orientation[0]
        if orientation_type == "F":
            return self.connections == 1
        elif orientation_type == "L":
            return self.connections == 2
        elif orientation_type == "B":
            return self.connections == 3
        elif orientation_type == "V":
            return self.connections == 2

    def is_connected(self, tile, direction):
        opposite_direction = Tile.direction_mapping[direction]
        return opposite_direction in Tile.open_directions[tile.orientation] and direction in Tile.open_directions[self.orientation]

    def connects_with(self, tile, direction):
        return Tile.direction_mapping[direction] in Tile.open_directions[tile.orientation]


    def get_locking_orientations(self, tile_type):
        return {
            "F": ["FB", "FD", "FE", "FC"],
            "L": ["LV", "LH"],
            "B": ["BB", "BC", "BD", "BE"],
            "V": ["VB", "VC", "VD", "VE"],
        }.get(tile_type, [])


class PipeMania(Problem):
    def __init__(self, board: Board):
        initial = PipeManiaState(board)
        self.visited_states = []
        super().__init__(initial)



    ### ACTION FUNCTIONS ###
    def actions(self, state: PipeManiaState):
        """Returns a list of actions that can be executed from the given state."""
        if any(visited.compare_boards(board) for visited in self.visited_states):
            return []

        actions = []
        lock_actions = []
        self.find_actions(state, actions, lock_actions)

        if not actions:
            self.find_non_locking_actions(state, actions, lock_actions)

        if lock_actions:
            return lock_actions

        if actions:
            return self.sort_and_filter_actions(actions)

        return actions

    def find_actions(self, state, actions, lock_actions):
        """Identify and collect possible actions on the board."""
        board = state.layout
        for row in range(board.row_count()):
            if self.collect_actions_from_row(board, row, actions):
                break

    def collect_actions_from_row(self, board, row, actions):
        """Collect possible actions from a specific row on the board."""
        for col in range(board.column_count(row)):
            tile = board.fetch_tile(row, col)
            if self.try_lock_tile(board, row, col, tile, actions):
                return True
        return False

    def try_lock_tile(self, board, row, col, tile, actions):
        if board.verify_locks(row, col, tile.orientation):
            tile.locked = True

        if tile.locked:
            return False

        action = self.get_locking_action(board, row, col, tile)
        if action:
            actions.append(action)
            return True

        return False

    def get_locking_action(self, board, row, col, tile):
        locking_orientations = Tile.get_locking_orientations(board, tile.orientation[0])

        for orientation in locking_orientations:
            if board.verify_locks(row, col, orientation):
                return (row, col, orientation, True)

        return None

    def find_non_locking_actions(self, state, actions, lock_actions):
        board = state.layout
        for row in range(board.cells.shape[0]):
            for col in range(board.cells.shape[1]):
                tile = board.fetch_tile(row, col)
                if tile.locked or (row, col) in state.moves:
                    continue

                possible_moves = board.unified_possible_moves(row, col, state.moves)
                self.filter_invalid_moves(possible_moves, tile, actions)

    def filter_invalid_moves(self, possible_moves, tile, actions):
        """Filter out invalid moves based on tile connectivity and update the actions list."""
        for move in possible_moves:
            move_tile = Tile(move[2])
            if tile.connects_with(move_tile, "left"):
                action = (move[0], move[1], move_tile, True)
                if action in actions:
                    actions.remove(action)
                actions.append(move)

    def sort_and_filter_actions(self, actions):
        """Sort and filter actions to prioritize those with the highest locked and connected counts."""
        # Create a dictionary to group actions by their (row, col) positions
        action_dict = {}
        for action in actions:
            position = (action[0], action[1])
            if position not in action_dict:
                action_dict[position] = []
            action_dict[position].append(action)

        # Find the position with the maximum locked count around it
        max_locked_count = -1
        best_position = None
        for position, action_list in action_dict.items():
            locked_count = self.count_locked_around(position[0], position[1])
            if locked_count > max_locked_count:
                max_locked_count = locked_count
                best_position = position

        # Get the actions corresponding to the best position
        best_actions = action_dict[best_position]

        # Sort the best actions by their connection counts
        best_actions.sort(key=lambda x: self.count_connections_around(x[0], x[1], x[2]), reverse=True)

        return best_actions

    def count_locked_around(self, row, col):
        board = self.initial.layout
        adjacent_tiles = board.horizontal_adjacent_values(row, col) + board.vertical_adjacent_values(row, col)

        count = 0
        for tile in adjacent_tiles:
            if tile is not None:
                count += 1 if tile.locked else 0.5 * sum(1 for adj_tile in board.horizontal_adjacent_values(row, col) + board.vertical_adjacent_values(row, col) if adj_tile and adj_tile.locked)

        return count

    def count_connections_around(self, row, col, orientation):
        board = self.initial.layout
        adjacent_tiles = board.horizontal_adjacent_values(row, col) + board.vertical_adjacent_values(row, col)

        count = 0
        for tile in adjacent_tiles:
            if tile is not None and Tile(orientation).is_connected(tile, "left"):
                count += 1
                count += 0.5 * sum(1 for adj_tile in board.horizontal_adjacent_values(row, col) + board.vertical_adjacent_values(row, col) if adj_tile and tile.is_connected(adj_tile, "left") and adj_tile.locked)

        return count

    ### RESULT FUNCTIONS ###

    def update_moved_tiles(self, moves, row, col):
        moved = copy.deepcopy(moves)
        moved.append((row, col))
        return moved

    def modify_board(self, board, row, col, orientation, is_locked):
        board.modify_tile_orientation(row, col, orientation)
        self.refresh_adjacent_connections(board, row, col)
        if is_locked:
            self.lock_tile_and_adjacent(board, row, col)

    def refresh_adjacent_connections(self, board, row, col):
        adjacent_positions = [(row, col), (row + 1, col), (row - 1, col), (row, col + 1), (row, col - 1)]
        for r, c in adjacent_positions:
            if 0 <= r < board.cells.shape[0] and 0 <= c < board.cells.shape[1]:
                board.refresh_connections(r, c)

    def lock_tile_and_adjacent(self, board, row, col):
        board.cells[row, col].locked = True
        adjacent_tiles = {
            (row - 1, col): board.vertical_adjacent_values(row, col)[0],
            (row + 1, col): board.vertical_adjacent_values(row, col)[1],
            (row, col - 1): board.horizontal_adjacent_values(row, col)[0],
            (row, col + 1): board.horizontal_adjacent_values(row, col)[1],
        }

        for (adj_row, adj_col), adj_tile in adjacent_tiles.items():
            if adj_tile is not None and 0 <= adj_row < board.cells.shape[0] and 0 <= adj_col < board.cells.shape[1] and board.verify_locks(adj_row, adj_col, adj_tile.orientation):
                adj_tile.locked = True

    def result(self, state: PipeManiaState, action):
        board = state.layout.copy()
        row, col, orientation, is_locked = action
        moved = self.update_moved_tiles(state.moves, row, col)

        self.modify_board(board, row, col, orientation, is_locked)

        return PipeManiaState(board, moved)

    def goal_test(self, state: PipeManiaState):
        visited_positions = self.initialize_visited_positions(state)

        if not self.all_tiles_fully_connected(state, visited_positions):
            return False

        return self.all_positions_reachable(state, visited_positions)

    def initialize_visited_positions(self, state):
        return np.full(state.layout.cells.shape, False)

    def all_tiles_fully_connected(self, state, visited_positions):
        def is_tile_fully_connected(tile):
            return tile.is_all_connected()

        board = state.layout
        return np.all([is_tile_fully_connected(tile) for tile in board.cells.flat])

    def all_positions_reachable(self, state, visited_positions):
        """Check if all positions on the board are reachable from the starting point."""

        def get_adjacent_positions(row, col, orientation):
            """Get adjacent positions based on the current tile orientation."""
            deltas = direction_offsets.get(orientation, [])
            return [(row + d_row, col + d_col) for d_row, d_col in deltas]

        def calculate_direction_offsets():
            """Calculate direction offsets based on tile orientations."""
            directions = {
                "U": (-1, 0),  # Up
                "D": (1, 0),   # Down
                "L": (0, -1),  # Left
                "R": (0, 1)    # Right
            }

            def get_offsets(orientations):
                return [directions[char] for char in orientations]

            return {
                "FC": get_offsets("U"),
                "FD": get_offsets("R"),
                "FE": get_offsets("L"),
                "FB": get_offsets("D"),
                "VC": get_offsets("UL"),
                "VD": get_offsets("RU"),
                "VE": get_offsets("LD"),
                "VB": get_offsets("DR"),
                "BB": get_offsets("DRL"),
                "BC": get_offsets("LRU"),
                "BD": get_offsets("RUD"),
                "BE": get_offsets("LDU"),
                "LV": get_offsets("UD"),
                "LH": get_offsets("LR")
            }

        # Now you can call the function to get the direction offsets
        direction_offsets = calculate_direction_offsets()

        frontier = [(0, 0)]

        def explore_and_mark(start_pos):
            """Explore and mark all reachable positions from the starting position."""
            def is_within_bounds(r, c):
                """Check if the given position is within the bounds of the board."""
                return 0 <= r < state.layout.cells.shape[0] and 0 <= c < state.layout.cells.shape[1]

            def mark_and_expand_position(row, col):
                """Mark the current position and expand to adjacent positions."""
                if not is_within_bounds(row, col) or visited_positions[row, col]:
                    return
                visited_positions[row, col] = True

                current_tile = state.layout.fetch_tile(row, col)
                adjacent_positions = get_adjacent_positions(row, col, current_tile.orientation)

                for next_row, next_col in adjacent_positions:
                    if is_within_bounds(next_row, next_col) and not visited_positions[next_row, next_col]:
                        frontier.append((next_row, next_col))

            frontier = [start_pos]
            while frontier:
                next_position = frontier.pop()
                mark_and_expand_position(*next_position)

            return np.all(visited_positions)

        start_pos = (0, 0)
        return explore_and_mark(start_pos)

    def h(self, node: Node):
        """Heuristic function used for A* search."""
        pass

if __name__ == "__main__":
    board = Board.parse_instance()
    problem = PipeMania(board)

    goal_node = depth_first_tree_search(problem)

    if goal_node:
        print(goal_node.state.layout)
    else:
        print("No solution found.")