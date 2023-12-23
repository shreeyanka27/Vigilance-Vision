import app
from flask import request


def get_reports():
    try:
        email = request.form['email']
        ps = request.form['password']
        user = app.users_collection.find_one({"email": email, "password": ps})
        if user is not None:
            if user["role"] == "public":
                reports = app.reports_collection.find({})
            else:
                reports = app.reports_collection.find({"email": email})
            result = []
            for report in reports:
                report_id = str(report["_id"])
                del(report["_id"])
                report["id"] = report_id
                result.append(report)
            return {"status": "success", "result: ": result}
        else:
            return "User cannot be found."
    except Exception as error:
        return {"status": "error", "error": str(error)}