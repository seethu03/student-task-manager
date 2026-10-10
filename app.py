from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from pathlib import Path

app = Flask(__name__)

# Store the database inside the project folder
BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "tasks.db"


# Connect to SQLite database
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# Create the tasks table automatically
def init_db():
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                priority TEXT NOT NULL DEFAULT 'Medium',
                due_date TEXT,
                completed INTEGER NOT NULL DEFAULT 0
            )
        """)


# Home page: display all tasks
@app.route("/")
def index():
    with get_db_connection() as conn:
        tasks = conn.execute(
            "SELECT * FROM tasks ORDER BY id DESC"
        ).fetchall()

    return render_template("index.html", tasks=tasks)


# Add a new task
@app.route("/add", methods=["POST"])
def add_task():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    priority = request.form.get("priority", "Medium")
    due_date = request.form.get("due_date", "")

    if not title:
        return "Task title is required.", 400

    if priority not in ("Low", "Medium", "High"):
        return "Invalid priority.", 400

    with get_db_connection() as conn:
        conn.execute(
            """
            INSERT INTO tasks
                (title, description, priority, due_date)
            VALUES (?, ?, ?, ?)
            """,
            (title, description, priority, due_date)
        )

    return redirect(url_for("index"))


# Mark a task as completed or pending
@app.route("/toggle/<int:task_id>", methods=["POST"])
def toggle_task(task_id):
    with get_db_connection() as conn:
        conn.execute(
            """
            UPDATE tasks
            SET completed = CASE
                WHEN completed = 0 THEN 1
                ELSE 0
            END
            WHERE id = ?
            """,
            (task_id,)
        )

    return redirect(url_for("index"))


# Delete a task
@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    with get_db_connection() as conn:
        conn.execute(
            "DELETE FROM tasks WHERE id = ?",
            (task_id,)
        )

    return redirect(url_for("index"))


# Edit a task
@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    with get_db_connection() as conn:
        task = conn.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,)
        ).fetchone()

        if task is None:
            return "Task not found.", 404

        if request.method == "POST":
            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()
            priority = request.form.get("priority", "Medium")
            due_date = request.form.get("due_date", "")

            if not title:
                return "Task title is required.", 400

            if priority not in ("Low", "Medium", "High"):
                return "Invalid priority.", 400

            conn.execute(
                """
                UPDATE tasks
                SET title = ?, description = ?,
                    priority = ?, due_date = ?
                WHERE id = ?
                """,
                (title, description, priority, due_date, task_id)
            )

            return redirect(url_for("index"))

    return render_template("edit.html", task=task)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
