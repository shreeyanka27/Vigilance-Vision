import app
from flask import request


def insert_user(email: str, phone_no: str, role: str, password: str):
    user = app.users_collection.insert_one({
        "email": email,
        "phone_no": phone_no,
        "role": role,
        "password": password
    })
    user_id = str(user.inserted_id)
    print("Inserted: " + str(user_id))
    return user_id


def register_user():
    try:
        user_id = insert_user(request.form['email'], request.form['phone_no'], request.form['role'],
                              request.form['password'])
        return {"status": "success", "user_id": user_id}
    except Exception as error:
        return {"status": "error", "error": str(error)}


def login():
    try:
        user = app.users_collection.find_one({"email": request.form['email'], "password": request.form['password']})
        return {"status": "success", "user_email": user["email"], "user_phone_no": user["phone_no"], "user_role": user["role"]}
    except Exception as error:
        return {"status": "error", "error": str(error)}
