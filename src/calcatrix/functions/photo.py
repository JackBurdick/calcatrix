import time
from datetime import datetime

from picamera import PiCamera


def take_photo(idict):
    IMG_PATH_TEMPLATE = "{}__{}__{}.jpg"

    # image index/bucket
    try:
        loc = idict["index"]
    except KeyError:
        loc = "X"

    try:
        base_path = idict["base_path"]
    except KeyError:
        base_path = "home/pi/dev/imgs/"

    # view/rotation
    try:
        view = int(idict["rot_degree"])
    except KeyError:
        view = "X"

    # e.g. '01_01_2021__17_13_18'
    ts = datetime.now().strftime("%m_%d_%Y__%H_%M_%S")
    filename = IMG_PATH_TEMPLATE.format(loc, view, ts)
    filepath = f"/{base_path}{filename}"

    # capture image
    with PiCamera() as camera:
        camera.start_preview()
        time.sleep(2)
        try:
            camera.capture(filepath)
        finally:
            camera.stop_preview()
