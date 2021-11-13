
# Import modules

import cv2
import datetime
import time
import socket
from tkinter import *
from flask import Flask, render_template, Response, redirect, url_for
import numpy as np
import os

# OpenCV class

class Camera:
    
    def __init__(self):
        self.frames = 0
        self.root = Tk()
        self.screen = (round(self.root.winfo_screenwidth()/1.5), round(self.root.winfo_screenheight()/1.5))
        self.camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.codec = 0x47504A4D
        self.camera.set(cv2.CAP_PROP_FOURCC, self.codec)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.screen[0])
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.screen[1])
        self.previous = None
        self.get = []
        self.types = {}
        self.different_types = []
        self.start_time = time.time()
        self.resolution = (int(self.camera.get(3)), int(self.camera.get(4)))
        self.recording = False
        self.records = []
        self.open = True

    def convert(self, frame):
        self.frame = frame
        self.frames += 1
        self.gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
        self.gray = cv2.GaussianBlur(self.gray, (21, 21), 0)
        if self.previous is None:
            self.previous = self.gray
        self.subtraction = cv2.absdiff(self.previous, self.gray)
        self.threshold = cv2.threshold(self.subtraction, 25, 255, cv2.THRESH_BINARY)[1]
        self.threshold = cv2.dilate(self.threshold, None, iterations=2)
        self.contourimg = self.threshold.copy()
        self.outlines, self.hierarchy = cv2.findContours(self.contourimg, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        self.found = []
        for self.c in self.outlines:
            if cv2.contourArea(self.c) > 2500:
                if self.detection_overlay == True:
                    (self.x, self.y, self.w, self.h) = cv2.boundingRect(self.c)
                    cv2.rectangle(self.frame, (self.x, self.y), (self.x + self.w, self.y + self.h), (0, 255, 0), 2)
                self.found.append(self.c)
        self.previous = self.gray
        if len(self.found) > 0:
            self.motion = True
        else:
            self.motion = False
        return (self.frame, self.motion)

    def get_frame(self, overlay=True, detection_overlay=False):
        self.success, self.frame = self.camera.read(0)
        self.detection_overlay = detection_overlay
        if self.success == True:
            self.frame, self.motion = self.convert(self.frame)
            if overlay == True:
                self.today = datetime.datetime.today()
                self.second = str(self.today.second)
                if len(self.second) < 2:
                    self.second = "0" + self.second
            if self.recording == False:
                if (time.time() - self.start_time) > 2:
                    for self.item in self.get:
                        self.item = str(self.item)
                        if self.item not in self.different_types:
                            self.different_types.append(self.item)
                            self.types[self.item] = 0
                        self.types[self.item] += 1
                    if len(self.different_types) < 2:
                        for self.item in ["True", "False"]:
                            try:
                                self.types[self.item]
                            except:
                                self.types[self.item] = 0
                    try:
                        self.percent = (self.types["True"]/(self.types["True"] + self.types["False"]))*100
                        if self.percent > 50:
                            self.video_start = time.time()
                            self.records.append(cv2.VideoWriter('{}{}{}({}).avi'.format(self.today.day, self.today.month, self.today.year, self.getNumber()), cv2.VideoWriter_fourcc('M','J','P','G'), 10, (self.resolution[0], self.resolution[1])))
                            self.recording = True
                    except Exception as e:
                        pass
                    self.start_time = time.time()
                    self.get = []
                    self.types = {}
                    self.different_types = []
            elif self.recording == True:
                try:
                    self.formats = "{}/{}/{} {}:{}:{}   Motion: {}".format(self.today.day, self.today.month, self.today.year, self.today.hour, self.today.minute, self.second, self.motion)
                    self.frame = cv2.putText(self.frame, self.formats, (0+3, self.screen[1]-6), cv2.FONT_HERSHEY_DUPLEX, 0.75, (255, 255, 255), 1, cv2.LINE_AA, False)
                    self.duration = (time.time() - self.video_start)
                    if self.motion == False and self.duration > 5:
                        self.start_time = time.time()
                        self.records[-1].release()
                        self.recording = False
                    else:
                        self.records[-1].write(self.frame)
                except:
                    pass
            self.get.append(self.motion)
            self.formats = "{}/{}/{} {}:{}:{}   Motion: {}   Recording: {}".format(self.today.day, self.today.month, self.today.year, self.today.hour, self.today.minute, self.second, self.motion, self.recording)
            cv2.rectangle(self.frame, (0, self.screen[1]+5), (0 + self.resolution[0], self.resolution[1] + 35), (0, 0, 0), -1)
            self.frame = cv2.putText(self.frame, self.formats, (0+3, self.screen[1]-6), cv2.FONT_HERSHEY_DUPLEX, 0.75, (255, 255, 255), 1, cv2.LINE_AA, False)
            self.frame = cv2.rotate(self.frame, cv2.ROTATE_180)
            self.success, self.image = cv2.imencode('.jpeg', self.frame)
            return self.image.tobytes()
        else:
            return None

    def getNumber(self):
        self.current = "{}{}{}".format(self.today.day, self.today.month, self.today.year)
        self.foundDate = None
        self.dates = {}
        self.founds = []
        for self.root, self.dirs, self.files in os.walk(os.getcwd()):
            for self.file in self.files:
                if self.file.endswith(".avi"):
                    self.date, self.item = self.file.replace(".avi", "").split("(")
                    self.item = self.item.replace(")", "")
                    if self.date not in self.founds:
                        self.founds.append(self.date)
                        self.dates[self.date] = []
                    self.dates[self.date].append(self.item)
                    if self.current == self.date:
                        self.foundDate = self.date
        if self.foundDate != None:
            self.items = self.dates[self.foundDate]
            self.number = int(self.items[-1]) + 1
            return self.number
        else:
            return 0

    def close(self):
        self.open = False
        self.camera.release()

# App class

class App(Flask):

    def __init__(self, camera):
        Flask.__init__(self, __name__)
        self.camera = camera
        self.routes()
        self.start()

    def generate(self, camera):
        self.camera = camera
        while True:
            self.frame = self.camera.get_frame()
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + self.frame + b'\r\n\r\n')

    def routes(self):
        @self.route("/")
        def home():
            try:
                return render_template("index.html")
            except:
                return "Settings"
        @self.route("/video")
        def video():
            try:
                return Response(self.generate(self.camera), mimetype='multipart/x-mixed-replace; boundary=frame')
            except:
                return "Camera Offline."
        @self.route("/close")
        def close():
            self.camera.close()
            return redirect(url_for("home"))
        @self.route("/reset-memory")
        def reset_memory():
            for self.root, self.dirs, self.files in os.walk(os.getcwd()):
                for self.file in self.files:
                    if self.file.endswith(".avi"):
                        os.remove(self.file)
            return redirect(url_for("home"))

    def start(self):
        self.run(host="0.0.0.0", port=5000)

# Initial run

if __name__ in "__main__":
    camera = Camera()
    App(camera)
