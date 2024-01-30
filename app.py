import ast
import base64
import io
import json
import os
import random
import re
import time
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib
import matplotlib.pylab as plt
import mysql.connector
import numpy as np
import requests
from PIL import Image
from flask import Flask, request, send_file, render_template, Response, make_response

with open("config.json", "r") as file:
    config = json.load(file)
with open("bannedIP", "r") as file:
    banned: list = ast.literal_eval(file.read())
app = Flask(__name__)
matplotlib.use('Agg')
mydb_pool = mysql.connector.pooling.MySQLConnectionPool(pool_name="mypool", pool_size=25, host="10.3.1.19",
                                                        username=config["dbuser"],
                                                        password=config["dbpswd"], database="tidy_trac")


class HandleOTP:
    def __init__(self):
        self.tries = 0
        self.otp = random.randint(111111, 999999)
        self.firstTime = 0
        self.deleteTime = int(time.time()) + (config["otpLimit"]["banTime"] * 60 * 60)
        self.nextSendTime = 0

    def canSendOtp(self) -> bool:
        global config
        if self.nextSendTime < time.time():
            return True
        return False

    def sendOTP(self) -> int:
        self.tries += 1
        if self.tries == 5:
            self.nextSendTime = int(time.time()) + (config["otpLimit"]["banTime"] * 60 * 60)
        else:
            self.nextSendTime = int(time.time()) + (config["otpLimit"]["rateLimitTime"] * 60)
        return self.otp


# TODO - schedule deleting objects
handleOTPobj: dict[int, HandleOTP] = {}
# TODO - add hard reset at start of day
rateLimitSubmit = {}


@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == "GET":
        return render_template("index.html")
    if banned.__contains__(request.remote_addr):
        return Response(status=403)
    global rateLimitSubmit

    data = request.data.decode("utf-8")
    data = json.loads(data)
    if not verifyToken(data["token"]):
        return Response(status=403)

    sch_no = getUserFromToken(data["token"])
    if rateLimitSubmit.get(sch_no) is None:
        rateLimitSubmit[sch_no] = 0
    if rateLimitSubmit[sch_no] == 3:
        return Response("Try again next day.", status=429)
    rateLimitSubmit[sch_no] += 1

    time_rn = int(time.time())
    localpath = f"""test-{time_rn}.png"""
    imgpath = Path.home().joinpath("img").joinpath(localpath)

    with mydb_pool.get_connection() as mydb:
        cur = mydb.cursor()
        cur.execute("""
        INSERT INTO main (feedback,imgpath,rating,locationcode,time,schno) VALUES (%s,%s,%s,%s,%s,%s);
        """, (
            re.sub(r'[^\x00-\x20\x2C\x2E\x30-\x39\x41-\x5A\x61-\x7A]', ' ', data["name"]), localpath, data["rad"],
            re.sub(r'[^\x00-\x20\x2C\x2E\x30-\x39\x41-\x5A\x61-\x7A]', ' ', data["washroom"]),
            int(time.time()), sch_no))
        mydb.commit()
        cur.close()
        Image.open(io.BytesIO(base64.b64decode(data["img"].replace("\\n", "").replace("\\", "")))).save(imgpath)
    return Response(status=200)


@app.route("/chart", methods=["POST"])
def create_chart():
    if not verifyToken(request.headers.get("Authorization")):
        return Response(status=403)

    from_date = float(request.args.get("fromDate"))
    to_date = float(request.args.get("toDate"))
    washroom_code = request.args.get("washroomCode")

    if from_date is None or to_date is None or from_date == "NaN" or to_date == "NaN":
        return Response(status=400)

    with mydb_pool.get_connection() as mydb:
        cur = mydb.cursor()
        if washroom_code is None:
            cur.execute("""
                                    SELECT * FROM main WHERE (time BETWEEN %s AND %s);
                                    """, (from_date, to_date))
        else:
            cur.execute("""
                        SELECT * FROM main WHERE (locationcode=%s) and (time BETWEEN %s AND %s);
                        """, (washroom_code, from_date, to_date))
        results = cur.fetchall()
        cur.close()

    dates = []
    clean = []
    somewhat_clean = []
    somewhat_dirty = []
    dirty = []

    i = 0
    switch = True
    while switch:
        temp_date = str((datetime.fromtimestamp(from_date) + timedelta(days=i)).date())
        dates.append(temp_date)
        i = i + 1
        clean.append(0)
        somewhat_clean.append(0)
        somewhat_dirty.append(0)
        dirty.append(0)
        if temp_date == str(datetime.fromtimestamp(to_date).date()):
            switch = False

    for result in results:
        index_result = dates.index(str(datetime.fromtimestamp(result[4]).date()))
        if int(result[2]) == -1:
            clean.insert(index_result, clean[index_result] + 1)
            clean.pop(index_result + 1)
        if int(result[2]) == 1:
            somewhat_clean.insert(index_result, somewhat_clean[index_result] + 1)
            somewhat_clean.pop(index_result + 1)
        if int(result[2]) == 2:
            somewhat_dirty.insert(index_result, somewhat_dirty[index_result] + 1)
            somewhat_dirty.pop(index_result + 1)
        if int(result[2]) == 3:
            dirty.insert(index_result, dirty[index_result] + 1)
            dirty.pop(index_result + 1)

    x_axis = np.arange(len(dates))

    plt.clf()
    plt.bar(x_axis - 0.15, clean, width=0.1, label="Very Clean")
    plt.bar(x_axis - 0.05, somewhat_clean, width=0.1, label="Somewhat Clean")
    plt.bar(x_axis + 0.05, somewhat_dirty, width=0.1, label="Somewhat Dirty")
    plt.bar(x_axis + 0.15, dirty, width=0.1, label="Very Dirty")
    plt.xticks(x_axis, dates, rotation=45)
    plt.legend()

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


@app.route("/admin/login")
def adminLoginPageServe():
    return render_template("adminlogin.html")


@app.route("/admin/verify", methods=["POST"])
def adminLogin():
    data = list(request.form.keys())[0]
    data = json.loads(data)
    user = data["user"]
    pswd = data["pswd"]

    with mydb_pool.get_connection() as mydb:
        cur = mydb.cursor()
        cur.execute('SELECT * FROM admin WHERE user=%s;', (user,))
        result = cur.fetchone()
        cur.close()

    if pswd == result[1]:
        session_token = genToken()
        saveToken(session_token, 86400, user)

        resp = make_response(session_token)
        resp.set_cookie("auth", session_token, 86400)
        return resp
    else:
        return Response(status=401)


# TODO - testing whole admin panel and chaning to cookies
# TODO - add secret client thingy
@app.route("/admin", methods=["GET"])
def admin():
    try:
        if not verifyToken(request.cookies["auth"]):
            return Response(status=403)
        return render_template("admin.html")
    except KeyError:
        return Response(status=400)


@app.route("/get/locations", methods=["GET", "POST"])
def getLocations():
    return send_file("locations", mimetype="file/json")


# TODO - adding reload button on the page
@app.route("/reload", methods=["POST"])
def reload():
    if not verifyToken(request.headers.get("Authorization")):
        return Response(status=403)
    global config
    with open("config.json", "r") as configfile:
        config = json.load(configfile)
    return Response(status=200)


@app.route("/get/table", methods=["POST"])
def getTable():
    if not verifyToken(request.headers.get("Authorization")):
        return Response(status=403)

    from_date = request.args.get("fromDate")
    to_date = request.args.get("toDate")

    with mydb_pool.get_connection() as mydb:
        cur = mydb.cursor()
        cur.execute("SELECT * FROM tidy_track.main WHERE time BETWEEN %s AND %s ORDER BY time;",
                    (from_date, to_date))
        results = cur.fetchall()
        cur.close()

    processed_list = []
    for result in results:
        inner_list = []
        for ele in result:
            inner_list.append(ele)
        processed_list.append(inner_list)
    return json.dumps(processed_list)


@app.route("/img/<path>", methods=["GET"])
def getIMG(path):
    if not verifyToken(request.cookies["auth"]):
        return Response(status=403)

    return send_file(os.getcwd() + "\\img\\" + path, mimetype="image/png")


def verifyToken(token) -> bool:
    with mydb_pool.get_connection() as mydb:
        cur = mydb.cursor()
        cur.execute('SELECT * FROM tidy_track.tokens WHERE idtokens=%s;', (token,))
        result = cur.fetchone()
        if result is None:
            cur.close()
            return False
        if result[1] < time.time():
            cur.execute('DELETE FROM tidy_track.tokens WHERE `idtokens`=%s;', (token,))
            mydb.commit()
            cur.close()
            return False
        cur.close()
        return True


def genToken() -> str:
    create_from = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    session_token = ""
    for i in range(0, 100):
        session_token += create_from[random.randint(0, len(create_from) - 1)]
    return session_token


def saveToken(token, valid, userid) -> None:
    with mydb_pool.get_connection() as mydb:
        cur = mydb.cursor()
        cur.execute("SELECT * FROM tidy_track.tokens WHERE user=%s", (userid,))
        result = cur.fetchall()
        if len(result) > 0:
            cur.execute("DELETE FROM tidy_track.tokens WHERE user=%s", (userid,))
        cur.execute("INSERT into tidy_track.tokens (time,idtokens,user) VALUES(%s,%s,%s);",
                    (int(time.time()) + valid, token, userid))
        mydb.commit()
        cur.close()


def getNOFromUser(user: int) -> int:
    with mydb_pool.get_connection() as mydb:
        cur = mydb.cursor()
        cur.execute("SELECT phone from tidy_track.userbase WHERE schno=%s", user)
        return cur.fetchone()[0]


def getUserFromToken(token) -> int:
    with mydb_pool.get_connection() as mydb:
        cur = mydb.cursor()
        cur.execute("SELECT user FROM tidy_track.tokens WHERE idtokens=%s", (token,))
        result = cur.fetchone()
        cur.close()
        return int(result[0])


@app.route("/otp/send", methods=["POST"])
def sendOTP():
    data = request.data.decode("utf-8")
    data = json.loads(data)
    sch_no = data["sch_no"]
    debug = data["debug"]

    try:
        phone_number = getNOFromUser(int(sch_no))
    except:
        name = data["stud_name"]
        phone_number = data["phone_no"]
        with mydb_pool.get_connection() as mydb:
            cur = mydb.cursor()
            cur.execute("INSERT INTO tidy_track.userbase (name, schno, phone) VALUES (%s,%s,%s)",(name,sch_no,phone_number))

    if handleOTPobj.get(sch_no) is None:
        handleOTPobj[sch_no] = HandleOTP()

    if not handleOTPobj.get(sch_no).canSendOtp():
        return Response(status=429)

    otp: int = handleOTPobj.get(sch_no).sendOTP()

    url = "https://bulksms.bsnl.in:5010/api/Send_SMS"

    if debug == "true":
        return Response(f"OTP has been sent to {phone_number}. If you wish to change the phone number, contact admins",
                        status=200)

    response = requests.post(url, headers={
        "Authorization": f"Bearer {config['auth']}",
        "Content-Type": "application/json;charset=utf-8"
    }, data=json.dumps({
        "Header": "NITBPL",
        "Target": phone_number,
        "Is_Unicode": "0",
        "Is_Flash": "0",
        "Message_Type": "SI",
        "Entity_Id": config["Entity_Id"],
        "Content_Template_Id": config["templateID"],
        "Template_Keys_and_Values": [{
            "Key": "var",
            "Value": otp
        }]
    }))
    return Response(f"OTP has been sent to {phone_number}. If you wish to change the phone number, contact admins",
                    status=response.status_code)


@app.route("/otp/verify", methods=["POST"])
def verifyOTP():
    data = request.data.decode("utf-8")
    data = json.loads(data)
    debug = data["debug"]
    if debug == "true":
        handleOTPobj.get(int(data["sch_no"])).otp = 111111
    if int(data["otp"]) == handleOTPobj.get(int(data["sch_no"])).otp:
        token = genToken()
        saveToken(token, 31556926, data["sch_no"])
        return Response(token, status=200)
    return Response(status=401)


@app.route("/update", methods=["POST"])
def updateJson():
    version = request.args.get("version")
    if version != config["currentVersion"]:
        return Response(status=200)
    else:
        return Response(status=100)


if __name__ == "__main__":
    app.run(port=5000, debug=True)
