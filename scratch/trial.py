from calcatrix.devices.multiview import MultiView  # pylint: disable=import-error
from picamera import PiCamera
from datetime import datetime
import time

DIR_PIN = 27
STEP_PIN = 17
LOC_PIN = 26
ENABLE_PIN = 22
BOUND_A_PIN = 23
BOUND_B_PIN = 25
ROTATE_PINS = [21, 20, 16, 12]
init_config = {
    "rotate": {"pins": ROTATE_PINS},
    "linear": {
        "stepper": {"dir": DIR_PIN, "step": STEP_PIN, "enable": ENABLE_PIN},
        "location": {
            "marker": {"pin": LOC_PIN},
            "bound_a": {"pin": BOUND_A_PIN},
            "bound_b": {"pin": BOUND_B_PIN},
        },
    },
}

mv = MultiView(init_config=init_config)

mv.initialize()

print(mv)


def take_photo(idict):
    BASEPATH = "home/pi/dev/imgs/"
    IMG_PATH_TEMPLATE = "{}__{}__{}.jpg"

    # image index/bucket
    try:
        loc = idict["index"]
    except KeyError:
        loc = "X"

    # view/rotation
    try:
        view = int(idict["rot_degree"])
    except KeyError:
        view = "X"

    # e.g. '01_01_2021__17_13_18'
    ts = datetime.now().strftime("%m_%d_%Y__%H_%M_%S")

    filename = IMG_PATH_TEMPLATE.format(loc, view, ts)
    filepath = f"/{BASEPATH}{filename}"

    # capture image
    with PiCamera() as camera:
        camera.start_preview()
        time.sleep(2)
        try:
            camera.capture(filepath)
        finally:
            camera.stop_preview()


mv.follow_all_instructions(func=take_photo)
