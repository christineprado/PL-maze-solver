import time
from collections import deque

def dfs(grid, start, end):
    rows = len(grid)
    cols = len(grid[0])
    visited = set()
    parent = {start: None}
    visited_order = []
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    stack = [start]

    t0 = time.perf_counter()

    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        visited_order.append(list(current))

        if current == end:
            break

        r, c = current
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                if grid[nr][nc] == 0 and (nr, nc) not in visited:
                    if (nr, nc) not in parent:
                        parent[(nr, nc)] = current
                    stack.append((nr, nc))

    t1 = time.perf_counter()
    exec_ms = round((t1 - t0) * 1000, 4)

    # Reconstruct path
    path = []
    if end in visited:
        node = end
        while node is not None:
            path.append(list(node))
            node = parent.get(node)
        path.reverse()

    return {
        'algorithm': 'DFS',
        'visited': visited_order,
        'path': path,
        'nodes_explored': len(visited_order),
        'path_length': len(path),
        'execution_time_ms': exec_ms,
        'solved': len(path) > 0 and path[0] == list(start) and path[-1] == list(end)
    }