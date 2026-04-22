from flask import Flask, jsonify, request, g
from flask_cors import CORS
import mysql.connector

app = Flask(__name__)
CORS(app)

DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "root123",
    "database": "hostel_mess",
}

# ─── NEW CONNECTION PER REQUEST ───────────────────────────────
# This completely avoids all connection timeout / cursor drop issues.
# A fresh connection is made at the start of every request and
# closed automatically when the request finishes.

def get_db():
    if "db" not in g:
        g.db = mysql.connector.connect(**DB_CONFIG)
    return g.db

def get_cursor():
    return get_db().cursor(dictionary=True)

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop("db", None)
    if db is not None and db.is_connected():
        db.close()


# ─── MENU (STUDENT) ───────────────────────────────────────────

@app.route("/menu")
def get_menu():
    cur = get_cursor()
    cur.execute("""
        SELECT menu.menu_id, mealtypes.meal_name, fooditems.food_name
        FROM menu
        JOIN mealtypes ON menu.meal_type_id = mealtypes.meal_type_id
        JOIN fooditems ON menu.food_id = fooditems.food_id
        WHERE menu.menu_date = CURDATE()
        ORDER BY mealtypes.meal_type_id, fooditems.food_name
    """)
    return jsonify(cur.fetchall())


# ─── STUDENT LOGIN ────────────────────────────────────────────

@app.route("/login/student", methods=["POST"])
def student_login():
    data       = request.get_json()
    student_id = data.get("student_id")
    password   = data.get("password")

    if not student_id or not password:
        return jsonify({"message": "student_id and password are required"}), 400

    cur = get_cursor()
    cur.execute(
        "SELECT student_id, name, hostel_block FROM students WHERE student_id = %s AND password = %s",
        (student_id, password)
    )
    student = cur.fetchone()
    if student:
        return jsonify(student)
    return jsonify({"message": "Invalid Student ID or password"}), 401


# ─── STUDENT REGISTER ─────────────────────────────────────────

@app.route("/register/student", methods=["POST"])
def student_register():
    data         = request.get_json()
    student_id   = data.get("student_id")
    name         = data.get("name")
    hostel_block = data.get("hostel_block")
    password     = data.get("password")

    if not all([student_id, name, hostel_block, password]):
        return jsonify({"message": "All fields are required"}), 400

    cur = get_cursor()
    cur.execute("SELECT student_id FROM students WHERE student_id = %s", (student_id,))
    if cur.fetchone():
        return jsonify({"message": "Student ID already exists"}), 409

    try:
        cur.execute(
            "INSERT INTO students (student_id, name, hostel_block, password) VALUES (%s, %s, %s, %s)",
            (student_id, name, hostel_block, password)
        )
        get_db().commit()
        return jsonify({"message": "Student registered successfully"})
    except Exception as e:
        get_db().rollback()
        return jsonify({"message": "Database error: " + str(e)}), 500


# ─── ADMIN LOGIN ──────────────────────────────────────────────

@app.route("/login/admin", methods=["POST"])
def admin_login():
    data     = request.get_json()
    admin_id = data.get("admin_id")
    password = data.get("password")

    if not admin_id or not password:
        return jsonify({"message": "admin_id and password are required"}), 400

    cur = get_cursor()
    cur.execute(
        "SELECT admin_id, name FROM admins WHERE admin_id = %s AND password = %s",
        (admin_id, password)
    )
    admin = cur.fetchone()
    if admin:
        return jsonify(admin)
    return jsonify({"message": "Invalid Admin ID or password"}), 401


# ─── ADMIN REGISTER ───────────────────────────────────────────

@app.route("/register/admin", methods=["POST"])
def admin_register():
    data     = request.get_json()
    admin_id = data.get("admin_id")
    name     = data.get("name")
    password = data.get("password")

    if not all([admin_id, name, password]):
        return jsonify({"message": "All fields are required"}), 400

    cur = get_cursor()
    cur.execute("SELECT admin_id FROM admins WHERE admin_id = %s", (admin_id,))
    if cur.fetchone():
        return jsonify({"message": "Admin ID already exists"}), 409

    try:
        cur.execute(
            "INSERT INTO admins (admin_id, name, password) VALUES (%s, %s, %s)",
            (admin_id, name, password)
        )
        get_db().commit()
        return jsonify({"message": "Admin registered successfully"})
    except Exception as e:
        get_db().rollback()
        return jsonify({"message": "Database error: " + str(e)}), 500


# ─── SUBMIT FEEDBACK ──────────────────────────────────────────

@app.route("/feedback", methods=["POST"])
def submit_feedback():
    data              = request.get_json()
    student_id        = data.get("student_id")
    menu_id           = data.get("menu_id")
    complaint_type_id = data.get("complaint_type_id")
    rating            = data.get("rating")
    feedback_type     = data.get("feedback_type", "complaint")
    comment           = data.get("comment", "")

    if not all([student_id, menu_id, complaint_type_id, rating]):
        return jsonify({"message": "student_id, menu_id, complaint_type_id and rating are required"}), 400

    if not (1 <= int(rating) <= 5):
        return jsonify({"message": "Rating must be between 1 and 5"}), 400

    cur = get_cursor()
    try:
        cur.execute("""
            INSERT INTO feedback (student_id, menu_id, complaint_type_id, rating, comment, feedback_type)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (student_id, menu_id, complaint_type_id, rating, comment, feedback_type))
        get_db().commit()
        return jsonify({"message": "Feedback submitted successfully"})
    except Exception as e:
        get_db().rollback()
        return jsonify({"message": "Database error: " + str(e)}), 500


# ─── ADMIN: ALL FEEDBACK ──────────────────────────────────────

@app.route("/admin/feedback")
def get_all_feedback():
    cur = get_cursor()
    cur.execute("""
        SELECT f.feedback_id, f.student_id, fi.food_name, mt.meal_name,
               ct.type_name AS complaint_type, f.rating, f.feedback_type, f.comment,
               DATE_FORMAT(m.menu_date, '%Y-%m-%d') AS feedback_date
        FROM feedback f
        JOIN menu           m  ON f.menu_id          = m.menu_id
        JOIN fooditems      fi ON m.food_id           = fi.food_id
        JOIN mealtypes      mt ON m.meal_type_id      = mt.meal_type_id
        JOIN complainttypes ct ON f.complaint_type_id = ct.complaint_type_id
        ORDER BY f.feedback_id DESC
    """)
    return jsonify(cur.fetchall())


# ─── ADMIN: FOOD ITEMS ────────────────────────────────────────

@app.route("/admin/food-items")
def get_food_items():
    cur = get_cursor()
    cur.execute("SELECT food_id, food_name FROM fooditems ORDER BY food_name")
    return jsonify(cur.fetchall())


# ─── ADMIN: MEAL TYPES ────────────────────────────────────────

@app.route("/admin/meal-types")
def get_meal_types():
    cur = get_cursor()
    cur.execute("SELECT meal_type_id, meal_name FROM mealtypes ORDER BY meal_type_id")
    return jsonify(cur.fetchall())


# ─── ADMIN: GET MENU BY DATE ──────────────────────────────────

@app.route("/admin/menu", methods=["GET"])
def get_menu_by_date():
    date = request.args.get("date")
    if not date:
        return jsonify({"message": "date parameter is required"}), 400

    cur = get_cursor()
    cur.execute("""
        SELECT menu.menu_id, mealtypes.meal_name, fooditems.food_name
        FROM menu
        JOIN mealtypes ON menu.meal_type_id = mealtypes.meal_type_id
        JOIN fooditems ON menu.food_id      = fooditems.food_id
        WHERE menu.menu_date = %s
        ORDER BY mealtypes.meal_type_id, fooditems.food_name
    """, (date,))
    return jsonify(cur.fetchall())


# ─── ADMIN: ADD MENU ITEMS ────────────────────────────────────

@app.route("/admin/menu", methods=["POST"])
def add_menu_items():
    data  = request.get_json()
    date  = data.get("date")
    items = data.get("items", [])

    if not date:
        return jsonify({"message": "date is required"}), 400
    if not items:
        return jsonify({"message": "items list is required"}), 400

    cur = get_cursor()
    try:
        inserted = 0
        for item in items:
            meal_type_id = item.get("meal_type_id")
            food_id      = item.get("food_id")
            if not meal_type_id or not food_id:
                continue
            cur.execute("""
                SELECT menu_id FROM menu
                WHERE menu_date = %s AND meal_type_id = %s AND food_id = %s
            """, (date, meal_type_id, food_id))
            if not cur.fetchone():
                cur.execute("""
                    INSERT INTO menu (menu_date, meal_type_id, food_id)
                    VALUES (%s, %s, %s)
                """, (date, meal_type_id, food_id))
                inserted += 1

        get_db().commit()
        return jsonify({"message": "Menu saved successfully", "inserted": inserted})
    except Exception as e:
        get_db().rollback()
        return jsonify({"message": "Database error: " + str(e)}), 500


# ─── ADMIN: DELETE MENU ITEM ──────────────────────────────────

@app.route("/admin/menu/<int:menu_id>", methods=["DELETE"])
def delete_menu_item(menu_id):
    cur = get_cursor()
    try:
        cur.execute("DELETE FROM feedback WHERE menu_id = %s", (menu_id,))
        cur.execute("DELETE FROM menu WHERE menu_id = %s", (menu_id,))
        get_db().commit()
        if cur.rowcount == 0:
            return jsonify({"message": "Menu item not found"}), 404
        return jsonify({"message": "Menu item deleted successfully"})
    except Exception as e:
        get_db().rollback()
        return jsonify({"message": "Database error: " + str(e)}), 500


# ─── RUN ──────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=False)