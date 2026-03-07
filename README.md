# MazeSolver v2.0
### ITP 11 | Baliuag University | 2026
#### Prado, Christine Joyce G. | Sebastian, Ralph Jieian I.

---

## What's New in v2.0
- Beautiful light theme (with dark mode toggle)
- Landing/home page before the solver
- User accounts (register, login, logout) — optional
- Settings page (theme, speed, maze size, confirmations)
- History page shows maze preview with paths drawn
- Click any history record to open full detail view
- Edit (rename) or delete any saved result
- Confirmation messages before destructive actions
- "Add Border Walls" button
- Friendlier language throughout (no technical jargon)

---

## Setup

### 1. Install dependencies
```
py -m pip install flask flask-cors mysql-connector-python
```

### 2. Set up the database
- Open XAMPP, start MySQL
- Open phpMyAdmin → create database `maze_solver_db`
- Click the database → SQL tab → paste contents of `database/setup.sql` → Go

### 3. Run
```
py app.py
```

### 4. Open
Go to: http://localhost:5000

---

## Project Structure
```
maze_solver_v2/
├── app.py                    ← Flask server
├── requirements.txt
├── algorithms/
│   ├── dfs.py
│   ├── bfs.py
│   └── maze_generator.py
├── database/
│   └── setup.sql             ← Run this in phpMyAdmin
└── templates/
    ├── landing.html          ← Home/landing page
    ├── index.html            ← Maze solver
    ├── history.html          ← Saved results
    └── settings.html         ← Settings
```
