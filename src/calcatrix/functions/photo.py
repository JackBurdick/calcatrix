import time
from datetime import datetime

from picamera import PiCamera


class Photo:
    def __init__(self, base_path="/home/pi/dev/imgs"):
        self.img_template = "{}__{}__{}__{}.jpg"
        self.base_path = base_path

    def __call__(self, instruction):
        try:
            index = instruction["index"]
        except KeyError:
            index = "X"

        try:
            rot_degree = instruction["rot_degree"]
        except KeyError:
            rot_degree = 0

        # image index/bucket
        rot_degree = int(rot_degree)

        try:
            location = instruction["location"]
        except KeyError:
            location = 0

        # e.g. '01_01_2021__17_13_18'
        ts = datetime.now().strftime("%m_%d_%Y__%H_%M_%S")
        filename = self.img_template.format(index, location, rot_degree, ts)
        filepath = f"{self.base_path}/{filename}"

        # capture image
        with PiCamera() as camera:
            camera.start_preview()
            time.sleep(2)
            try:
                camera.capture(filepath)
            finally:
                camera.stop_preview()

        return filepath
