from flask import Flask, request

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


app = Flask(__name__)


global_cart = None


@app.route("/")
def ok():
    return "ok"


@app.route("/cart/status", methods=["GET"])
def status():
    if request.method == "GET":
        # return information
        # - current indexes
        # - current specification
        # - last request
        # - request completed?
        # - num images present
        return "/cart/status"


@app.route("/cart/initialize", methods=["POST"])
def initialize():
    global global_cart
    if request.method == "POST":
        # TODO: ensure reasonable
        mm_to_object = request.args.get("mm_to_object")
        angle = request.args.get("angle")
        force_init = request.args.get("force_init")
        try:
            _ = init_config["multiview"]
        except KeyError:
            init_config["multiview"] = {}
        if mm_to_object:
            init_config["multiview"]["mm_to_object"] = mm_to_object
        if angle:
            init_config["multiview"]["angle"] = angle

        if global_cart is not None and global_cart.instructions is not None:
            # cart+instructions have already been created at least once
            if force_init is False:
                return f"already initialized: {global_cart.instructions}", 200

        global_cart = MultiView(init_config=init_config)
        global_cart.initialize()
        return (
            f"initialized: mm_to_object: {mm_to_object}, angle: {angle}, force_init: {force_init}",
            200,
        )


@app.route("/cart/images/retrieve", methods=["GET"])
def retrieve():
    # retrieve specific image, ensure it exists
    if request.method == "GET":
        file_name = request.args.get("file_name")
        return f"file_name: {file_name}"


@app.route("/cart/images/capture", methods=["POST"])
def capture():
    # capture all specified images
    if request.method == "POST":
        if global_cart is None:
            return "MultiView cart not initialized", 400
        else:
            try:
                global_cart.follow_all_instructions(func=take_photo)
                return f"instuctions followed", 200
            except Exception as e:
                return f"Unable to follow all instruction: Exception: {e}", 400


@app.route("/cart/images/capture_single", methods=["POST"])
def capture_single():
    if request.method == "POST":
        # TODO: ensure existing
        index = request.args.get("index")
        position = request.args.get("position")
        # TODO: ensure either index or position is set, not both
        angle = request.args.get("angle")
        return f"index: {index}, position: {position}, angle: {angle}"


if __name__ == "__main__":
    app.run(threaded=False)
