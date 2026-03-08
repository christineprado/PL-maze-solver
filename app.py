from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import psycopg2
import psycopg2.extras
import json, hashlib, re, os
from algorithms.dfs import dfs
from algorithms.bfs import bfs
from algorithms.maze_generator import generate_maze

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'mazesolver_secret_2026')
CORS(app)

def get_db():
    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'), sslmode='require')
        return conn
    except Exception as e:
        print(f"DB Error: {e}")
        return None

def mkc(conn):
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

def hash_password(pw): return hashlib.sha256(pw.encode()).hexdigest()
def current_user(): return session.get('user')

def validate_password(pw):
    if len(pw) < 8: return False, 'Password must be at least 8 characters.'
    if not re.search(r'[A-Z]', pw): return False, 'Password must contain at least one uppercase letter.'
    if not re.search(r'[a-z]', pw): return False, 'Password must contain at least one lowercase letter.'
    if not re.search(r'\d', pw): return False, 'Password must contain at least one number.'
    return True, ''

@app.route('/')
def landing(): return render_template('landing.html', user=current_user())
@app.route('/solver')
def solver(): return render_template('index.html', user=current_user())
@app.route('/history')
def history_page(): return render_template('history.html', user=current_user())
@app.route('/settings')
def settings_page(): return render_template('settings.html', user=current_user())

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username','').strip()
    email = data.get('email','').strip().lower()
    password = data.get('password','')
    if not username or not email or not password:
        return jsonify({'error':'All fields are required.'}), 400
    if len(username) < 3:
        return jsonify({'error':'Username must be at least 3 characters.'}), 400
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return jsonify({'error':'Username can only contain letters, numbers, and underscores.'}), 400
    if not re.match(r'^[a-zA-Z0-9._%+\-]+@gmail\.com$', email):
        return jsonify({'error':'Email must be a valid @gmail.com address.'}), 400
    ok, pw_err = validate_password(password)
    if not ok: return jsonify({'error': pw_err}), 400
    db = get_db()
    if not db: return jsonify({'error':'Could not connect to database.'}), 500
    cur = mkc(db)
    cur.execute("SELECT user_id FROM users WHERE username=%s OR email=%s", (username, email))
    if cur.fetchone():
        cur.close(); db.close()
        return jsonify({'error':'That username or email is already taken.'}), 400
    cur.execute("INSERT INTO users (username, email, password) VALUES (%s,%s,%s) RETURNING user_id",
                (username, email, hash_password(password)))
    user_id = cur.fetchone()['user_id']
    db.commit(); cur.close(); db.close()
    session['user'] = {'id': user_id, 'username': username, 'email': email}
    return jsonify({'status':'ok','username':username})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username','').strip()
    password = data.get('password','')
    if not username or not password:
        return jsonify({'error':'Please enter your username and password.'}), 400
    db = get_db()
    if not db: return jsonify({'error':'Could not connect to database.'}), 500
    cur = mkc(db)
    cur.execute("SELECT user_id, username, email FROM users WHERE (username=%s OR email=%s) AND password=%s",
                (username, username, hash_password(password)))
    user = cur.fetchone()
    cur.close(); db.close()
    if not user: return jsonify({'error':'Incorrect username or password.'}), 401
    session['user'] = {'id': user['user_id'], 'username': user['username'], 'email': user['email']}
    return jsonify({'status':'ok','username':user['username']})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'status':'ok'})

@app.route('/api/me')
def me():
    u = current_user()
    if u: return jsonify({'logged_in':True,'username':u['username'],'email':u['email']})
    return jsonify({'logged_in':False})

@app.route('/api/profile', methods=['PUT'])
def update_profile():
    u = current_user()
    if not u: return jsonify({'error':'You must be logged in.'}), 401
    data = request.get_json()
    new_username = data.get('username','').strip()
    new_email = data.get('email','').strip().lower()
    new_password = data.get('password','').strip()
    cur_password = data.get('current_password','')
    db = get_db()
    if not db: return jsonify({'error':'Could not connect.'}), 500
    cur = mkc(db)
    cur.execute("SELECT password FROM users WHERE user_id=%s", (u['id'],))
    row = cur.fetchone()
    if not row or row['password'] != hash_password(cur_password):
        cur.close(); db.close()
        return jsonify({'error':'Current password is incorrect.'}), 401
    updates = []; params = []
    if new_username and new_username != u['username']:
        if len(new_username) < 3:
            cur.close(); db.close(); return jsonify({'error':'Username must be at least 3 characters.'}), 400
        if not re.match(r'^[a-zA-Z0-9_]+$', new_username):
            cur.close(); db.close(); return jsonify({'error':'Username can only contain letters, numbers, and underscores.'}), 400
        cur.execute("SELECT user_id FROM users WHERE username=%s AND user_id!=%s", (new_username, u['id']))
        if cur.fetchone():
            cur.close(); db.close(); return jsonify({'error':'That username is already taken.'}), 400
        updates.append("username=%s"); params.append(new_username)
    if new_email and new_email != u['email']:
        if not re.match(r'^[a-zA-Z0-9._%+\-]+@gmail\.com$', new_email):
            cur.close(); db.close(); return jsonify({'error':'Email must be a valid @gmail.com address.'}), 400
        cur.execute("SELECT user_id FROM users WHERE email=%s AND user_id!=%s", (new_email, u['id']))
        if cur.fetchone():
            cur.close(); db.close(); return jsonify({'error':'That email is already in use.'}), 400
        updates.append("email=%s"); params.append(new_email)
    if new_password:
        ok, pw_err = validate_password(new_password)
        if not ok:
            cur.close(); db.close(); return jsonify({'error': pw_err}), 400
        updates.append("password=%s"); params.append(hash_password(new_password))
    if not updates:
        cur.close(); db.close(); return jsonify({'error':'No changes detected.'}), 400
    params.append(u['id'])
    cur.execute(f"UPDATE users SET {', '.join(updates)} WHERE user_id=%s", params)
    db.commit()
    cur.execute("SELECT user_id, username, email FROM users WHERE user_id=%s", (u['id'],))
    updated = cur.fetchone()
    cur.close(); db.close()
    session['user'] = {'id': updated['user_id'], 'username': updated['username'], 'email': updated['email']}
    return jsonify({'status':'ok','username':updated['username'],'email':updated['email']})

@app.route('/api/solve', methods=['POST'])
def solve():
    data = request.get_json()
    grid = data['grid']; start = tuple(data['start']); end = tuple(data['end'])
    algorithm = data['algorithm'].upper()
    if algorithm == 'DFS': result = dfs(grid, start, end)
    elif algorithm == 'BFS': result = bfs(grid, start, end)
    else: return jsonify({'error':'Unknown algorithm'}), 400
    return jsonify(result)

@app.route('/api/solve_both', methods=['POST'])
def solve_both():
    data = request.get_json()
    grid = data['grid']; start = tuple(data['start']); end = tuple(data['end'])
    return jsonify({'dfs': dfs(grid, start, end), 'bfs': bfs(grid, start, end)})

@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.get_json()
    rows = int(data.get('rows', 15)); cols = int(data.get('cols', 15))
    grid, start, end = generate_maze(rows, cols)
    return jsonify({'grid': grid, 'start': list(start), 'end': list(end)})

@app.route('/api/save', methods=['POST'])
def save():
    data = request.get_json()
    grid = data['grid']; start = data['start']; end = data['end']
    name = (data.get('name','My Maze') or 'My Maze').strip()
    dfs_r = data.get('dfs'); bfs_r = data.get('bfs')
    user = current_user(); uid = user['id'] if user else None
    db = get_db()
    if not db: return jsonify({'error':'Could not connect.'}), 500
    cur = mkc(db)
    if uid:
        cur.execute("SELECT maze_id FROM mazes WHERE user_id=%s AND maze_name=%s", (uid, name))
    else:
        cur.execute("SELECT maze_id FROM mazes WHERE user_id IS NULL AND maze_name=%s", (name,))
    if cur.fetchone():
        cur.close(); db.close()
        return jsonify({'error': f'You already have a saved maze named "{name}". Please choose a different name.'}), 409
    explanation = data.get('explanation', '')
    cur.execute(
        "INSERT INTO mazes (user_id, maze_name, grid_rows, grid_cols, grid_data, start_row, start_col, end_row, end_col, explanation) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING maze_id",
        (uid, name, len(grid), len(grid[0]), json.dumps(grid), start[0], start[1], end[0], end[1], explanation)
    )
    maze_id = cur.fetchone()['maze_id']
    for result, algo in [(dfs_r,'DFS'), (bfs_r,'BFS')]:
        if result:
            cur.execute(
                "INSERT INTO results (maze_id, algorithm, cells_visited, path_length, execution_time_ms, path_data, visited_data, solved) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (maze_id, algo, result.get('nodes_explored',0), result.get('path_length',0),
                 result.get('execution_time_ms',0), json.dumps(result.get('path',[])),
                 json.dumps(result.get('visited',[])), result.get('solved',False))
            )
    db.commit(); cur.close(); db.close()
    return jsonify({'status':'saved','maze_id':maze_id})

@app.route('/api/history', methods=['GET'])
def history():
    user = current_user(); uid = user['id'] if user else None
    db = get_db()
    if not db: return jsonify({'records':[],'error':'Not connected'})
    cur = mkc(db)
    if uid:
        cur.execute("""SELECT m.maze_id,m.maze_name,m.grid_rows,m.grid_cols,m.created_at,r.algorithm,r.cells_visited,r.path_length,r.execution_time_ms,r.solved FROM mazes m LEFT JOIN results r ON m.maze_id=r.maze_id WHERE m.user_id=%s ORDER BY m.created_at DESC""", (uid,))
    else:
        cur.execute("""SELECT m.maze_id,m.maze_name,m.grid_rows,m.grid_cols,m.created_at,r.algorithm,r.cells_visited,r.path_length,r.execution_time_ms,r.solved FROM mazes m LEFT JOIN results r ON m.maze_id=r.maze_id WHERE m.user_id IS NULL ORDER BY m.created_at DESC""")
    rows = cur.fetchall(); cur.close(); db.close()
    mazes = {}
    for row in rows:
        mid = row['maze_id']
        if mid not in mazes:
            mazes[mid] = {'maze_id':mid,'maze_name':row['maze_name'],'grid_rows':row['grid_rows'],'grid_cols':row['grid_cols'],'created_at':str(row['created_at']),'results':{}}
        if row['algorithm']:
            mazes[mid]['results'][row['algorithm']] = {'cells_visited':row['cells_visited'],'path_length':row['path_length'],'execution_time_ms':float(row['execution_time_ms']) if row['execution_time_ms'] else None,'solved':bool(row['solved'])}
    return jsonify({'records': list(mazes.values())})

@app.route('/api/maze/<int:maze_id>', methods=['GET'])
def get_maze(maze_id):
    db = get_db()
    if not db: return jsonify({'error':'Not connected'}), 500
    cur = mkc(db)
    cur.execute("SELECT * FROM mazes WHERE maze_id=%s", (maze_id,))
    maze = cur.fetchone()
    if not maze: cur.close(); db.close(); return jsonify({'error':'Not found'}), 404
    cur.execute("SELECT * FROM results WHERE maze_id=%s", (maze_id,))
    results = cur.fetchall(); cur.close(); db.close()
    maze = dict(maze)
    maze['grid_data'] = json.loads(maze['grid_data'])
    maze['explanation'] = maze.get('explanation', '')
    maze['created_at'] = str(maze['created_at'])
    res_dict = {}
    for r in results:
        res_dict[r['algorithm']] = {'cells_visited':r['cells_visited'],'path_length':r['path_length'],'execution_time_ms':float(r['execution_time_ms']) if r['execution_time_ms'] else None,'solved':bool(r['solved']),'path':json.loads(r['path_data']) if r['path_data'] else [],'visited':json.loads(r['visited_data']) if r['visited_data'] else []}
    return jsonify({'maze':maze,'results':res_dict})

@app.route('/api/maze/<int:maze_id>', methods=['PUT'])
def update_maze(maze_id):
    data = request.get_json()
    name = (data.get('name','') or '').strip()
    if not name: return jsonify({'error':'Name cannot be empty.'}), 400
    db = get_db()
    if not db: return jsonify({'error':'Not connected'}), 500
    cur = mkc(db)
    user = current_user(); uid = user['id'] if user else None

    if data.get('full_update'):
        grid = data['grid']; start = data['start']; end = data['end']
        dfs_r = data.get('dfs'); bfs_r = data.get('bfs')
        explanation = data.get('explanation','')
        cur.execute(
            "UPDATE mazes SET maze_name=%s, grid_rows=%s, grid_cols=%s, grid_data=%s, start_row=%s, start_col=%s, end_row=%s, end_col=%s, explanation=%s WHERE maze_id=%s",
            (name, len(grid), len(grid[0]), json.dumps(grid), start[0], start[1], end[0], end[1], explanation, maze_id)
        )
        cur.execute("DELETE FROM results WHERE maze_id=%s", (maze_id,))
        for result, algo in [(dfs_r,'DFS'),(bfs_r,'BFS')]:
            if result:
                cur.execute(
                    "INSERT INTO results (maze_id, algorithm, cells_visited, path_length, execution_time_ms, path_data, visited_data, solved) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                    (maze_id, algo, result.get('nodes_explored',0), result.get('path_length',0),
                     result.get('execution_time_ms',0), json.dumps(result.get('path',[])),
                     json.dumps(result.get('visited',[])), result.get('solved',False))
                )
        db.commit(); cur.close(); db.close()
        return jsonify({'status':'updated','maze_id':maze_id})

    if uid:
        cur.execute("SELECT maze_id FROM mazes WHERE user_id=%s AND maze_name=%s AND maze_id!=%s", (uid, name, maze_id))
    else:
        cur.execute("SELECT maze_id FROM mazes WHERE user_id IS NULL AND maze_name=%s AND maze_id!=%s", (name, maze_id))
    if cur.fetchone():
        cur.close(); db.close()
        return jsonify({'error': f'You already have a maze named "{name}".'}), 409
    cur.execute("UPDATE mazes SET maze_name=%s WHERE maze_id=%s", (name, maze_id))
    db.commit(); cur.close(); db.close()
    return jsonify({'status':'updated'})

@app.route('/api/maze/<int:maze_id>', methods=['DELETE'])
def delete_maze(maze_id):
    db = get_db()
    if not db: return jsonify({'error':'Not connected'}), 500
    cur = mkc(db)
    cur.execute("DELETE FROM mazes WHERE maze_id=%s", (maze_id,))
    db.commit(); cur.close(); db.close()
    return jsonify({'status':'deleted'})

@app.route('/api/account', methods=['DELETE'])
def delete_account():
    u = current_user()
    if not u: return jsonify({'error':'You must be logged in.'}), 401
    data = request.get_json()
    cur_password = data.get('current_password','')
    if not cur_password: return jsonify({'error':'Password is required.'}), 400
    db = get_db()
    if not db: return jsonify({'error':'Could not connect.'}), 500
    cur = mkc(db)
    cur.execute("SELECT password FROM users WHERE user_id=%s", (u['id'],))
    row = cur.fetchone()
    if not row or row['password'] != hash_password(cur_password):
        cur.close(); db.close()
        return jsonify({'error':'Incorrect password.'}), 401
    cur.execute("DELETE FROM users WHERE user_id=%s", (u['id'],))
    db.commit(); cur.close(); db.close()
    session.clear()
    return jsonify({'status':'deleted'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
