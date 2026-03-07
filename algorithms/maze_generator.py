import random

def generate_maze(rows, cols):
    # Start with all walls
    grid = [[1] * cols for _ in range(rows)]

    def carve(r, c):
        directions = [(0, 2), (0, -2), (2, 0), (-2, 0)]
        random.shuffle(directions)
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1:
                grid[r + dr // 2][c + dc // 2] = 0
                grid[nr][nc] = 0
                carve(nr, nc)

    # Start from (1,1)
    grid[1][1] = 0
    carve(1, 1)

    # Ensure start and end are open
    start = (1, 1)
    end   = (rows - 2, cols - 2)
    grid[start[0]][start[1]] = 0
    grid[end[0]][end[1]] = 0

    return grid, start, end
