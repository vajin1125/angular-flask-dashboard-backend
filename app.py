from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_socketio import SocketIO, emit

from datetime import datetime  
from datetime import timedelta
import psutil
import shutil
import os
import speedtest
import time
import logging
import pandas as pd
import json


app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:password@localhost:3307/flask-angular-database'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)

# logfile for bandwidth
LOG_FILE = 'bandwidth.log'
# for logview page 
logcounts = 30
# for Dashboard last actives
last_active_counts = 10

class Activity(db.Model):
    __tablename__ = 'activity'
    ActivityId = db.Column(db.Integer, primary_key = True)
    Date = db.Column(db.DateTime())
    UserId = db.Column(db.Integer)
    UserName = db.Column(db.String(1024)) 
    Action = db.Column(db.Integer)
    PrimaryFolderId = db.Column(db.Integer)
    FolderId = db.Column(db.Integer)
    FileId = db.Column(db.Integer)
    Path = db.Column(db.String(1024))
    Information = db.Column(db.String(1024))
    Status = db.Column(db.Integer)

class ActivitySchema(ma.ModelSchema):
    class Meta:
        model = Activity

class User(db.Model):
    __tablename__ = 'users'
    UserId = db.Column(db.Integer, primary_key = True)
    UserName = db.Column(db.String(100))
    Password = db.Column(db.String(32))
    Active = db.Column(db.Integer)
    Locked = db.Column(db.Integer)
    Permissions = db.Column(db.Integer)
    UserType = db.Column(db.Integer)
    UserExpirationDate = db.Column(db.Date())
    PasswordExpirationDate = db.Column(db.Date())
    RestrictionIp = db.Column(db.String(19))
    Country = db.Column(db.String(100))
    Code = db.Column(db.String(10))

class UserSchema(ma.ModelSchema):
    class Meta:
        model = User

##===========================================================================================================##

@app.route("/")
def index():
    return ("Server is running now!")

# for Logview page
@app.route("/activity", methods=['GET'])
def get_activity():
    activity = Activity.query.filter().order_by(Activity.ActivityId.desc()).limit(logcounts)
    activity_schema = ActivitySchema(many=True)
    response_data = activity_schema.dump(activity).data
    return jsonify(response_data)

# for Dashboard 8
@app.route("/last_actives", methods=['GET'])
def get_last_actives():
    activity = Activity.query.filter().order_by(Activity.ActivityId.desc()).limit(last_active_counts)
    activity_schema = ActivitySchema(many=True)
    response_data = activity_schema.dump(activity).data
    return jsonify(response_data)

# for Dashboard 1
@app.route("/total_upload_download_counts", methods=['POST'])
def get_total_upload_download_counts():
    resp = []
    resp = request.json
    now_time = resp['now_time']
    last_time = resp['last_time']
    print(now_time, last_time)
    # test_now_time = '2018-10-17 23:42:1'
    # test_last_time = '2018-10-16 23:42:1'
    total_count = Activity.query.filter(Activity.Date>=last_time, Activity.Date<=now_time, (Activity.Action==26) | (Activity.Action==27)).count()
    upload_counts = Activity.query.filter(Activity.Date>=last_time, Activity.Date<=now_time, Activity.Action==26).count()
    download_counts = Activity.query.filter(Activity.Date>=last_time, Activity.Date<=now_time, Activity.Action==27).count()
    user_counts = User.query.filter(User.Active==0).count()
    print("total_count:", total_count)
    print("upload_count:", upload_counts)
    print("download_count:", download_counts)
    print("user_count:", user_counts)
    respons_data = {"total_count": total_count, "upload_count": upload_counts, "download_count": download_counts, "user_count": user_counts}
    return jsonify(respons_data)

# for Dashboard 2
@app.route("/upload_download_for_graph", methods=['POST'])
def get_upload_download_for_graph():
    result = []
    resp = []
    resp = request.json
    last_time = resp['last_time']
    print("last_time:", last_time)
    # nowTime = datetime.now().replace(microsecond=0)
    # lastTime = datetime(2018, 10, 16, 23, 42, 1)
    lastTime = datetime.strptime(last_time, '%Y-%m-%d %H:%M:%S')
    print("lastTime",lastTime)
    c_time = lastTime
    # print ("haha", nowTime + timedelta(hours=1))
    for interval in range(24):
        to_time = c_time + timedelta(hours=1)
        print("c_time", c_time)
        print("to_time", to_time)

        activity_upload = Activity.query.filter(Activity.Date>=c_time, Activity.Date<=to_time, Activity.Action==26).count()
        activity_download = Activity.query.filter(Activity.Date>=c_time, Activity.Date<=to_time, Activity.Action==27).count()
        show_time_for_graph = datetime.strftime(to_time, '%Y-%m-%d %H:%M:%S')
        sub_result = {"time": show_time_for_graph, "upload": activity_upload, "download": activity_download}
        result.append(sub_result)

        c_time = to_time
    
    # test_now_time = '2018-10-17 23:42:1'
    # test_last_time = '2018-10-16 23:42:1'

    # min_date = db.session.query(db.func.min(Activity.Date)).scalar()
    # max_date = db.session.query(db.func.max(Activity.Date)).scalar()
    # print("-----",min_date, max_date)
    # activity_upload = Activity.query.filter(Activity.Date<=date2, Activity.Action==26).count()
    # activity_download = Activity.query.filter(Activity.Date<=date2, Activity.Action==27).count()
    # response_data = {"result_upload": 1, "result_download": 1}
    return jsonify(result)

# for Dashboard 3
@app.route("/logged_user_list", methods=['GET'])
def get_logged_user_list():
    user_list = User.query.filter(User.Active==0)
    user_schema = UserSchema(many=True)
    response_data = user_schema.dump(user_list).data
    return jsonify(response_data)

# for Dashboard 4
@app.route("/logged_users_counts_per_country", methods=['GET'])
def get_logged_users_counts_per_country():
    result = []
    user_list = db.session.query(User.Code, User.Country, db.func.count(User.Country)).filter(User.Active==0).group_by(User.Country).all()
    for item in user_list:
        data = {
            "code": item[0],
            "name": item[1],
            "value": item[2]
        }
        result.append(data)
    response_data = result
    return jsonify(response_data)

# for Dashboard 5
@app.route("/machine_info", methods=['GET'])
def get_machine_info():
    cpu_percent = psutil.cpu_percent()
    memory_percent = psutil.virtual_memory()[2]
    print("CPU Usage:", cpu_percent)
    print("Memory Usage", memory_percent)

    obj_Disk = psutil.disk_usage('/')
    print (obj_Disk.total / (1024.0 ** 3))
    print (obj_Disk.used / (1024.0 ** 3))
    print (obj_Disk.free / (1024.0 ** 3))
    print (obj_Disk.percent)
    hd_free_percent = round(100 - obj_Disk.percent, 2)
    print("HD free %:", hd_free_percent)

    response_data = {
        "cpu_usage": cpu_percent, 
        "memory_usage": memory_percent, 
        "hd_free_percent": hd_free_percent
    }
    return jsonify(response_data)


@app.route("/bandwidth", methods=['GET'])
def get_bandwidth():
    result = []
    nowTime = datetime.now().replace(microsecond=0)
    lastTime = datetime.strftime(nowTime, '%Y-%m-%d %H:%M:%S')
    # print("lastTime", lastTime)
    upload=psutil.net_io_counters(pernic=True)['Ethernet'].bytes_sent
    download=psutil.net_io_counters(pernic=True)['Ethernet'].bytes_recv
    up_down=(upload,download)
    # print(up_down)
    time.sleep(1)
    upload1=psutil.net_io_counters(pernic=True)['Ethernet'].bytes_sent
    download1=psutil.net_io_counters(pernic=True)['Ethernet'].bytes_recv
    up_down1=(upload1,download1)
    # print(up_down1)
    upload_bw = round((upload1-upload) / 1024, 2)
    download_bw = round((download1-download) / 1024, 2)
    # print("UL: {:0.2f} kB".format(upload_bw), "DL: {:0.2f} kB".format(download_bw))
    response_data = {
        'time': lastTime,
        'upload': upload_bw,
        'download': download_bw
    }

    # df = pd.io.parsers.read_csv(
    #     LOG_FILE,
    #     names='date time upload download'.split(),
    #     header=None,
    #     sep=r'\s+',
    #     parse_dates={'timestamp':[0,1]},
    #     na_values=['TEST','FAILED']
    # )
    # # print (df[-48:]) # return last 48 rows of data (i.e., 24 hours)
    # log_data = df[-48:]
    # log_json = log_data.to_json(orient='records', date_format='iso', lines=False)
    # print("0:", log_json)
    # response_data = [log_json]
    return jsonify(response_data)


# for Dashboard 6
@app.route("/cpu_mem_usage_graph", methods=['GET'])
def get_cpu_mem_usage_graph():
    now = datetime.now().replace(microsecond=0)
    nowTime = datetime.strftime(now, '%Y-%m-%d %H:%M:%S')
    # print("nowtime---", nowTime)
    cpu_percent = psutil.cpu_percent()
    memory_percent = psutil.virtual_memory()[2]
    # print("CPU Usage:", cpu_percent)
    # print("Memory Usage", memory_percent)
    response_data = {
        "time": nowTime,
        "cpu": cpu_percent,
        "memory": memory_percent
    }
    return jsonify(response_data)


# for Dashboard 7
@app.route("/hdd_list", methods=['GET'])
def get_hdd_list():
    drive_result = []
    disk_partitions = psutil.disk_partitions(all=False)
    # print(disk_partitions)
    for partition in disk_partitions:
        if partition.fstype != '':
            usage = psutil.disk_usage(partition.mountpoint)
            device = {
                'device': partition.device,
                'total': usage.total,
                'percent': usage.percent
            }
            drive_result.append(device)
            # print(device)
    drive_result = sorted(drive_result, key=lambda device: device['device'])
    response_data = drive_result
    return jsonify(response_data)


if __name__ == "__main__":
    app.run(debug=True)
    