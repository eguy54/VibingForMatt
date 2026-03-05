import random
from collections import deque

import streamlit as st
from PIL import Image, ImageDraw

N, S, E, W = 1, 2, 4, 8
DIRS = {
    N: (0, -1),
    S: (0, 1),
    E: (1, 0),
    W: (-1, 0),
}
OPPOSITE = {N: S, S: N, E: W, W: E}


def create_walls(width: int, height: int) -> list[list[int]]:
    return [[N | S | E | W for _ in range(width)] for _ in range(height)]


def carve(walls: list[list[int]], x: int, y: int, direction: int) -> None:
    width = len(walls[0])
    height = len(walls)
    dx, dy = DIRS[direction]
    nx, ny = x + dx, y + dy
    if not (0 <= nx < width and 0 <= ny < height):
        return
    walls[y][x] &= ~direction
    walls[ny][nx] &= ~OPPOSITE[direction]


def generate_perfect_maze(width: int, height: int, rng: random.Random) -> list[list[int]]:
    walls = create_walls(width, height)
    stack = [(0, 0)]
    visited = {(0, 0)}

    while stack:
        x, y = stack[-1]
        candidates = []
        for direction, (dx, dy) in DIRS.items():
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in visited:
                candidates.append((direction, nx, ny))

        if not candidates:
            stack.pop()
            continue

        direction, nx, ny = rng.choice(candidates)
        carve(walls, x, y, direction)
        visited.add((nx, ny))
        stack.append((nx, ny))

    return walls


def add_loops(walls: list[list[int]], density: float, rng: random.Random) -> None:
    if density <= 0:
        return

    width = len(walls[0])
    height = len(walls)
    candidates: list[tuple[int, int, int]] = []

    for y in range(height):
        for x in range(width):
            if x + 1 < width and (walls[y][x] & E):
                candidates.append((x, y, E))
            if y + 1 < height and (walls[y][x] & S):
                candidates.append((x, y, S))

    if not candidates:
        return

    target = max(1, int(len(candidates) * density))
    for x, y, direction in rng.sample(candidates, min(target, len(candidates))):
        if walls[y][x] & direction:
            carve(walls, x, y, direction)


def add_rooms(walls: list[list[int]], attempts: int, max_room_size: int, rng: random.Random) -> None:
    if attempts <= 0:
        return

    width = len(walls[0])
    height = len(walls)
    if width < 3 or height < 3:
        return

    max_w = max(2, min(max_room_size, width))
    max_h = max(2, min(max_room_size, height))

    for _ in range(attempts):
        room_w = rng.randint(2, max_w)
        room_h = rng.randint(2, max_h)
        x0 = rng.randint(0, width - room_w)
        y0 = rng.randint(0, height - room_h)

        for y in range(y0, y0 + room_h):
            for x in range(x0, x0 + room_w):
                if x + 1 < x0 + room_w:
                    carve(walls, x, y, E)
                if y + 1 < y0 + room_h:
                    carve(walls, x, y, S)


def build_from_edges(width: int, height: int, edges: set[tuple[tuple[int, int], tuple[int, int]]]) -> list[list[int]]:
    walls = create_walls(width, height)
    for (ax, ay), (bx, by) in edges:
        if ax == bx and abs(ay - by) == 1:
            carve(walls, ax, min(ay, by), S)
        elif ay == by and abs(ax - bx) == 1:
            carve(walls, min(ax, bx), ay, E)
    return walls


def mirror_to_full_width(half_walls: list[list[int]], full_width: int, rng: random.Random) -> list[list[int]]:
    half_width = len(half_walls[0])
    height = len(half_walls)
    edges: set[tuple[tuple[int, int], tuple[int, int]]] = set()

    def add_edge(a: tuple[int, int], b: tuple[int, int]) -> None:
        if a > b:
            a, b = b, a
        edges.add((a, b))

    for y in range(height):
        for x in range(half_width):
            if x + 1 < half_width and not (half_walls[y][x] & E):
                add_edge((x, y), (x + 1, y))
            if y + 1 < height and not (half_walls[y][x] & S):
                add_edge((x, y), (x, y + 1))

    def mirror_x(x: int) -> int:
        return full_width - 1 - x

    mirrored_edges: set[tuple[tuple[int, int], tuple[int, int]]] = set()
    for (ax, ay), (bx, by) in edges:
        add_edge((ax, ay), (bx, by))
        mx1, mx2 = mirror_x(ax), mirror_x(bx)
        if (0 <= mx1 < full_width) and (0 <= mx2 < full_width):
            a = (mx1, ay)
            b = (mx2, by)
            if a > b:
                a, b = b, a
            mirrored_edges.add((a, b))

    edges |= mirrored_edges

    if full_width % 2 == 0:
        left = half_width - 1
        right = half_width
        bridge_rows = [y for y in range(height) if rng.random() < 0.6]
        if not bridge_rows:
            bridge_rows = [rng.randrange(height)]
        for y in bridge_rows:
            add_edge((left, y), (right, y))

    return build_from_edges(full_width, height, edges)


def difficulty_settings(level: str) -> dict[str, float | int]:
    settings = {
        "Easy": {"loop_density": 0.12, "room_attempts": 3, "max_room_size": 5},
        "Medium": {"loop_density": 0.07, "room_attempts": 2, "max_room_size": 4},
        "Hard": {"loop_density": 0.03, "room_attempts": 1, "max_room_size": 3},
    }
    return settings[level]


def generate_maze(
    width: int,
    height: int,
    difficulty: str,
    allow_loops: bool,
    add_room_areas: bool,
    vertical_symmetry: bool,
    multiple_exits: bool,
    seed: int | None,
) -> dict:
    rng = random.Random(seed)
    settings = difficulty_settings(difficulty)

    if vertical_symmetry:
        half_width = (width + 1) // 2
        half = generate_perfect_maze(half_width, height, rng)
        if allow_loops:
            add_loops(half, float(settings["loop_density"]), rng)
        if add_room_areas:
            add_rooms(half, int(settings["room_attempts"]), int(settings["max_room_size"]), rng)
        walls = mirror_to_full_width(half, width, rng)
    else:
        walls = generate_perfect_maze(width, height, rng)
        if allow_loops:
            add_loops(walls, float(settings["loop_density"]), rng)
        if add_room_areas:
            add_rooms(walls, int(settings["room_attempts"]), int(settings["max_room_size"]), rng)

    start = (0, 0)
    exits = [(width - 1, height - 1)]

    walls[start[1]][start[0]] &= ~N
    walls[height - 1][width - 1] &= ~S

    if multiple_exits:
        extra = (0, height - 1)
        if extra not in exits:
            exits.append(extra)
            walls[extra[1]][extra[0]] &= ~S

    return {"walls": walls, "start": start, "exits": exits}


def orthogonal_neighbors(walls: list[list[int]], x: int, y: int) -> list[tuple[int, int]]:
    width = len(walls[0])
    height = len(walls)
    results: list[tuple[int, int]] = []

    for direction, (dx, dy) in DIRS.items():
        nx, ny = x + dx, y + dy
        if 0 <= nx < width and 0 <= ny < height and not (walls[y][x] & direction):
            results.append((nx, ny))

    return results


def can_move(walls: list[list[int]], x: int, y: int, direction: int) -> bool:
    width = len(walls[0])
    height = len(walls)
    dx, dy = DIRS[direction]
    nx, ny = x + dx, y + dy
    return 0 <= nx < width and 0 <= ny < height and not (walls[y][x] & direction)


def all_neighbors(
    walls: list[list[int]], x: int, y: int, allow_diagonal: bool
) -> list[tuple[int, int]]:
    neighbors = orthogonal_neighbors(walls, x, y)
    if not allow_diagonal:
        return neighbors

    diagonals = [
        (1, 1, E, S),
        (1, -1, E, N),
        (-1, 1, W, S),
        (-1, -1, W, N),
    ]

    width = len(walls[0])
    height = len(walls)

    for dx, dy, d1, d2 in diagonals:
        nx, ny = x + dx, y + dy
        if not (0 <= nx < width and 0 <= ny < height):
            continue
        # Allow diagonal motion only if both adjacent orthogonal corridors are open.
        if can_move(walls, x, y, d1) and can_move(walls, x, y, d2):
            neighbors.append((nx, ny))

    return neighbors


def solve_maze(
    walls: list[list[int]], start: tuple[int, int], exits: list[tuple[int, int]], allow_diagonal: bool
) -> list[tuple[int, int]]:
    exit_set = set(exits)
    queue = deque([start])
    prev: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    target = None

    while queue:
        current = queue.popleft()
        if current in exit_set:
            target = current
            break
        for nxt in all_neighbors(walls, current[0], current[1], allow_diagonal):
            if nxt not in prev:
                prev[nxt] = current
                queue.append(nxt)

    if target is None:
        return []

    path = []
    node = target
    while node is not None:
        path.append(node)
        node = prev[node]
    path.reverse()
    return path


def render_maze(
    walls: list[list[int]],
    start: tuple[int, int],
    exits: list[tuple[int, int]],
    path: list[tuple[int, int]] | None = None,
    cell_size: int = 20,
) -> Image.Image:
    width = len(walls[0])
    height = len(walls)

    img = Image.new("RGB", (width * cell_size + 1, height * cell_size + 1), "white")
    draw = ImageDraw.Draw(img)

    for y in range(height):
        for x in range(width):
            px = x * cell_size
            py = y * cell_size
            cell = walls[y][x]
            if cell & N:
                draw.line([(px, py), (px + cell_size, py)], fill="black", width=2)
            if cell & W:
                draw.line([(px, py), (px, py + cell_size)], fill="black", width=2)
            if cell & E:
                draw.line([(px + cell_size, py), (px + cell_size, py + cell_size)], fill="black", width=2)
            if cell & S:
                draw.line([(px, py + cell_size), (px + cell_size, py + cell_size)], fill="black", width=2)

    if path:
        points = [
            (x * cell_size + cell_size // 2, y * cell_size + cell_size // 2)
            for x, y in path
        ]
        draw.line(points, fill="#1f77b4", width=max(2, cell_size // 4))

    radius = max(3, cell_size // 5)
    sx, sy = start
    sxp = sx * cell_size + cell_size // 2
    syp = sy * cell_size + cell_size // 2
    draw.ellipse((sxp - radius, syp - radius, sxp + radius, syp + radius), fill="#2ca02c")

    for ex, ey in exits:
        exp = ex * cell_size + cell_size // 2
        eyp = ey * cell_size + cell_size // 2
        draw.ellipse((exp - radius, eyp - radius, exp + radius, eyp + radius), fill="#d62728")

    return img


def estimate_cell_size(width: int, height: int) -> int:
    longest_side = max(width, height)
    if longest_side <= 20:
        return 24
    if longest_side <= 35:
        return 18
    return 14


st.set_page_config(page_title="Maze Builder", layout="wide")
st.title("Maze Builder")
st.caption("Generate mazes with toggles and reveal the solved path on demand.")

controls_left, controls_right = st.columns(2)

with controls_left:
    difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"], index=1)
    width = st.slider("Width", min_value=8, max_value=60, value=24, step=1)
    height = st.slider("Height", min_value=8, max_value=60, value=24, step=1)
    seed_input = st.number_input(
        "Seed (0 = random)", min_value=0, max_value=999999, value=0, step=1
    )

with controls_right:
    allow_loops = st.checkbox("Allow loops", value=True)
    add_room_areas = st.checkbox("Add room areas", value=False)
    vertical_symmetry = st.checkbox("Vertical symmetry", value=False)
    multiple_exits = st.checkbox("Multiple exits", value=False)
    allow_diagonal_solve = st.checkbox("Allow diagonal solve moves", value=False)

button_col1, button_col2 = st.columns(2)
with button_col1:
    generate_clicked = st.button("Generate Maze", use_container_width=True)
with button_col2:
    solve_clicked = st.button("Solve", use_container_width=True)

if "maze_state" not in st.session_state:
    st.session_state.maze_state = None

if "solution_path" not in st.session_state:
    st.session_state.solution_path = None

seed = None if int(seed_input) == 0 else int(seed_input)

if generate_clicked or st.session_state.maze_state is None:
    st.session_state.maze_state = generate_maze(
        width=width,
        height=height,
        difficulty=difficulty,
        allow_loops=allow_loops,
        add_room_areas=add_room_areas,
        vertical_symmetry=vertical_symmetry,
        multiple_exits=multiple_exits,
        seed=seed,
    )
    st.session_state.solution_path = None

maze_state = st.session_state.maze_state

if solve_clicked:
    st.session_state.solution_path = solve_maze(
        walls=maze_state["walls"],
        start=maze_state["start"],
        exits=maze_state["exits"],
        allow_diagonal=allow_diagonal_solve,
    )

path = st.session_state.solution_path

cell_size = estimate_cell_size(len(maze_state["walls"][0]), len(maze_state["walls"]))
maze_image = render_maze(
    walls=maze_state["walls"],
    start=maze_state["start"],
    exits=maze_state["exits"],
    path=path,
    cell_size=cell_size,
)

st.image(maze_image, caption="Green = start, Red = exit, Blue = solved path", use_container_width=False)

if path:
    st.success(f"Solved in {len(path) - 1} steps.")
else:
    st.info("Click Solve to display the path.")
