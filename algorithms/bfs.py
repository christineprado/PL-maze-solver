import time
from collections import deque

def bfs(grid, start, end):
    rows = len(grid)
    cols = len(grid[0])
    visited = set()
    parent = {start: None}
    visited_order = []
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    queue = deque([start])
    visited.add(start)

    t0 = time.perf_counter()

    while queue:
        current = queue.popleft()
        visited_order.append(list(current))

        if current == end:
            break

        r, c = current
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                if grid[nr][nc] == 0 and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    parent[(nr, nc)] = current
                    queue.append((nr, nc))

    t1 = time.perf_counter()
    exec_ms = round((t1 - t0) * 1000, 4)

    # Reconstruct path
    path = []
    if end in visited_order or any(n == list(end) for n in visited_order):
        if end in parent or end in visited:
            node = end
            while node is not None:
                path.append(list(node))
                node = parent.get(node)
            path.reverse()

    return {
        'algorithm': 'BFS',
        'visited': visited_order,
        'path': path,
        'nodes_explored': len(visited_order),
        'path_length': len(path),
        'execution_time_ms': exec_ms,
        'solved': len(path) > 0 and path[0] == list(start) and path[-1] == list(end)
    }