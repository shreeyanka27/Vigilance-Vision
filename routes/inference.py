import app
import time
from flask import request
from werkzeug.utils import secure_filename
from fastai.vision.all import *

import os
import cv2
from glob import glob
from PIL import Image

import pathlib
temp = pathlib.PosixPath
pathlib.PosixPath = pathlib.WindowsPath

import os
from twilio.rest import Client

account_sid = "AC11f849e9972cf83ec7c56bc1d96db02b"
auth_token = "1536e15dc3df0a676c402bbe7bef16c7"
client = Client(account_sid, auth_token)

model = load_learner('./model.pkl')


def get_nature_from_model(path: str):
    return model.predict(path)[0]


def create_dir(path):
    try:
        if not os.path.exists(path):
            os.makedirs(path)
    except OSError:
        print(f"ERROR: creating directory with name {path}")


def save_frame(video_path, save_dir, gap=10):
    name = video_path.split("/")[-1].split(".")[0]
    save_path = os.path.join(save_dir, name)
    create_dir(save_path)

    cap = cv2.VideoCapture(video_path)
    idx = 0

    while True:
        ret, frame = cap.read()

        if ret == False:
            cap.release()
            break

        if idx == 0:
            cv2.imwrite(f"{save_path}/{idx}.png", frame)
            img = Image.open(f'{save_path}/{idx}.png')
            img = img.resize((64, 64), Image.ANTIALIAS)
            img.save(f'{save_path}/{idx}.png')
        else:
            if idx % gap == 0:
                cv2.imwrite(f"{save_path}/{idx}.png", frame)
                img = Image.open(f'{save_path}/{idx}.png')
                img = img.resize((64, 64), Image.ANTIALIAS)
                img.save(f'{save_path}/{idx}.png')

        idx += 1


def insert_report(nature: str, location: str, alert_level: str, email: str = ""):
    report = app.reports_collection.insert_one({
        "nature": nature,
        "location": location,
        "time": int(time.time()),
        "alert_level": alert_level,
        "email": email,
        "clip_location": ""
    })
    report_id = str(report.inserted_id)
    print("Inserted: " + str(report_id))
    return report_id


def get_alert_level_from_nature(nature: str):
    low = ["vandalism", "shoplifting", "fighting", "arrest"]
    mid = ["assault", "abuse", "burglary", "stealing"]
    high = ["explosion", "shooting", "arson", "roadaccidents", "robbery"]
    if nature.lower() in low:
        return "low"
    elif nature.lower() in mid:
        return "mid"
    elif nature.lower() in high:
        return "high"
    else:
        return "normal"


def send_sms(nature):
    body = """Vigilance Vision\n{nature} detected at {location}\nTake required measures. Stay Safe.\nHelpline: +919480805448\n"""
    body = body.replace("{nature}", nature)
    body = body.replace("{location}", "Library Building, MIT")

    message = client.messages.create(
        body=body,
        from_="+15855132725",
        to="+919766014952"
    )
    print("SMS Sent")


def run_inference():
    try:
        f = request.files['file']
        f.save(secure_filename(f.filename))
        video_paths = glob(secure_filename(f.filename))
        save_dir = "x"
        for path in video_paths:
            save_frame(path, save_dir, gap=10)
        print("Frames done")
        nature = get_nature_from_model("x/" + secure_filename(f.filename)[:-4] + "/1010.png")
        print(nature)
        if nature != "NormalVideos":
            report_id = insert_report(nature, "Manipal", get_alert_level_from_nature(nature), request.form['email'])
            app.reports_collection.update_one({"_id": report_id},
                                              {"$set": {"clip_location": "./video_data/" + secure_filename(
                                                  report_id) + ".mp4"}})
            f.save("video_data/" + secure_filename(report_id) + ".mp4")
            send_sms(nature)
            return """
            <html>
               <body>
                  <h1>Crime Found</h1>
                  <h2>Nature: {0}</h2>
                  <h2>Location: {1}</h2>
               </body>
            </html>
            """.format(nature, "Library Building, MIT")
        else:
            return """
                <html>
               <body>
                  <h1>No Crime Found</h1>
               </body>
            </html>
            """
    except Exception as error:
        return {"status": "error", "error": str(error)}

def get_nature_from_frame():
    try:
        f = request.files['file']
        f.save("./frames/" + secure_filename(f.filename))
        nature = get_nature_from_model("./frames/" + secure_filename(f.filename))
        return {"status": "success", "nature": nature}
    except Exception as error:
        return {"status": "error", "error": str(error)}