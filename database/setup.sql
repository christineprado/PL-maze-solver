DROP TABLE IF EXISTS results;
DROP TABLE IF EXISTS mazes;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    user_id    SERIAL PRIMARY KEY,
    username   VARCHAR(50) NOT NULL UNIQUE,
    email      VARCHAR(100) NOT NULL UNIQUE,
    password   VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE mazes (
    maze_id     SERIAL PRIMARY KEY,
    user_id     INT DEFAULT NULL,
    maze_name   VARCHAR(100) DEFAULT 'My Maze',
    grid_rows   INT NOT NULL,
    grid_cols   INT NOT NULL,
    grid_data   TEXT NOT NULL,
    start_row   INT NOT NULL,
    start_col   INT NOT NULL,
    end_row     INT NOT NULL,
    end_col     INT NOT NULL,
    explanation TEXT DEFAULT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

CREATE TABLE results (
    result_id         SERIAL PRIMARY KEY,
    maze_id           INT,
    algorithm         VARCHAR(3) NOT NULL,
    cells_visited     INT,
    path_length       INT,
    execution_time_ms FLOAT,
    path_data         TEXT,
    visited_data      TEXT,
    solved            BOOLEAN,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (maze_id) REFERENCES mazes(maze_id) ON DELETE CASCADE
);
