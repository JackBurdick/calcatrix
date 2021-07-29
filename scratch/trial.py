import time
from datetime import datetime

from picamera import PiCamera

from calcatrix.devices.multiview import MultiView  # pylint: disable=import-error
from calcatrix.functions.photo import take_photo  # pylint: disable=import-error

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
        "positions": {
            # filepath is the location to store, init, if true will initialize the cart
            # from the saved filepath, if present
            # data = {"marker_positions": [], "current_position": 0}
            "file_path": "/home/pi/dev/saved_positions/trial_0.pickle",
            "init_from_file": True,
        },
    },
}

mv = MultiView(init_config=init_config)

mv.initialize()

print(mv)

mv.follow_all_instructions(func=take_photo)
