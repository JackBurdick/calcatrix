import os
from pathlib import Path

from flask import Flask, request, send_from_directory

from calcatrix.devices.multiview import MultiView  # pylint: disable=import-error
from calcatrix.functions.photo import Photo  # pylint: disable=import-error

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
BASE_PATH = "/home/pi/dev/imgs"
photo_func = Photo(base_path=BASE_PATH)


@app.route("/cart/status", methods=["GET"])
def status():
    """
    Return basic cart information
    """
    if request.method == "GET":
        # return information
        # - current indexes
        # - current specification
        # - last request
        # - request completed?
        # - num images present
        sd = {}
        if global_cart:
            sd["mm_to_object"] = global_cart.mm_to_object
            sd["angle"] = global_cart.angle
            sd["max_steps"] = global_cart.linear.max_steps
            sd["cur_location"] = global_cart.linear.cur_location
            sd["_view_locations"] = global_cart._view_locations
            sd["instructions"] = global_cart.instructions
        else:
            sd["cart"] = None
        return sd, 200


@app.route("/cart/initialize", methods=["POST"])
def initialize():
    """
    Initialize the cart, the cart is stored in `global_cart` as a global
    variable
    """
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
            init_config["multiview"]["mm_to_object"] = int(mm_to_object)
        if angle:
            init_config["multiview"]["angle"] = int(angle)

        if global_cart is not None:
            if global_cart.instructions is not None:
                # cart+instructions have already been created at least once
                if force_init == False:
                    return f"already initialized: {global_cart.instructions}", 200
                else:
                    global_cart.initialize(force_init=force_init)
                    return f"no existing instructions, re-initializing", 200
            else:
                global_cart.initialize()
                return f"cart existed, but no instructions found, reinitializing", 200
        else:
            global_cart = MultiView(init_config=init_config)
            global_cart.initialize(force_init=force_init)
            return (
                f"initialized: mm_to_object: {mm_to_object}, angle: {angle}, force_init: {force_init}",
                200,
            )


@app.route("/cart/images/retrieve", methods=["GET"])
def retrieve():
    """
    Retrieve an already captured image, if it exists
    """
    if request.method == "GET":
        file_name = request.args.get("file_name")
        if not file_name:
            return f"Please provide a file name", 400
        else:
            full_path = Path(BASE_PATH).joinpath(file_name)
            if not full_path.exists():
                return f"File ({file_name}) not found", 404
            else:
                if not full_path.is_file():
                    return f"Requested file {file_name} is not a valid file", 400
                else:
                    return send_from_directory(BASE_PATH, file_name), 200


@app.route("/cart/images/remove", methods=["GET"])
def remove_file():
    """
    Remove an already captured image, if it exists
    """
    if request.method == "GET":
        file_name = request.args.get("file_name")
        if not file_name:
            return f"Please provide a file name", 400
        else:
            full_path = Path(BASE_PATH).joinpath(file_name)
            if not full_path.exists():
                return f"File ({file_name}) not found", 404
            else:
                if not full_path.is_file():
                    return f"Requested file {file_name} is not a valid file", 400
                else:
                    os.remove(str(full_path))
                    return f"file ({full_path}) removed", 200


@app.route("/cart/images/list", methods=["GET"])
def list_files():
    """
    List all the images currently present
    """
    if request.method == "GET":
        try:
            files = (str(x) for x in Path(BASE_PATH).iterdir() if x.is_file())
        except Exception as e:
            return f"unable to list files from {BASE_PATH}. \n {e}", 400
        files = list(files)
        rd = {}
        rd["files"] = files
        rd["num_files"] = len(files)
        return rd, 200


@app.route("/cart/images/capture", methods=["POST"])
def capture():
    """
    Follow all pre-initialized cart instructions
    """
    if request.method == "POST":
        if global_cart is None:
            return "MultiView cart not initialized", 400
        else:
            try:
                global_cart.follow_all_instructions(func=photo_func)
                return f"instructions followed", 200
            except Exception as e:
                return f"Unable to follow all instruction: Exception: {e}", 400


@app.route("/cart/images/capture_index", methods=["POST"])
def capture_index():
    """
    Capture image at the specified index
    """
    if request.method == "POST":
        # args
        index = request.args.get("index")
        if not index:
            return f"Please specify an index", 400
        if isinstance(index, str):
            index = int(index)

        pos_name = request.args.get("position_name")
        if not isinstance(pos_name, str):
            pos_name = str(pos_name)
        if not pos_name:
            # default to straight on image
            pos_name = "0"

        # capture if specified exists
        if global_cart:
            cur_locations = global_cart._view_locations
            try:
                loc = cur_locations[index]
                try:
                    _ = loc[pos_name]
                    found = False
                    # NOTE: a more clever implementation could be worked here.
                    # Technically, only the inner or outter loop is necessary, but this
                    # the outter loop makes it easy to provide better error messages
                    for instruction in global_cart.instructions:
                        if str(instruction["index"]) == str(index):
                            if str(instruction["name"]) == str(pos_name):
                                found = True
                                break
                    if found:
                        # CAPTURE IMAGE
                        ret_val = global_cart.follow_instruction(
                            instruction, func=photo_func
                        )
                        return f"instruction followed ({ret_val})", 200
                    else:
                        return (
                            f"index ({index}) and position_name ({pos_name}) not found"
                            f"\n {global_cart.instructions}",
                            400,
                        )
                except KeyError:
                    return f"position ({pos_name}), not in index ({loc})", 400
            except KeyError:
                return f"index ({index}), not in {cur_locations.keys()}", 400
        else:
            return (
                "cart not initialized, please initialize (/cart/initialize, POST)",
                400,
            )


# TODO: allow for custom photos
@app.route("/cart/images/capture_step", methods=["POST"])
def capture_step():
    """
    Capture image at the specified step/rotation
    """
    if request.method == "POST":
        # TODO: ensure existing
        location = request.args.get("location")
        if location is None:
            return f"please specify a location", 400
        if not isinstance(location, int):
            location = int(location)

        rotation_degree = request.args.get("rotation_degree")
        if rotation_degree is None:
            return f"please specify a rotation_degree", 400
        if not isinstance(rotation_degree, int):
            rotation_degree = int(rotation_degree)

        name = request.args.get("name")
        if name is None:
            return f"please specify a name", 400
        if not isinstance(name, str):
            name = str(name)

        index = request.args.get("index")
        if index is None:
            return f"please specify a index", 400
        if not isinstance(index, int):
            index = int(index)

        if global_cart:
            instruction = global_cart._create_instruction(
                location=location,
                rotation_degree=rotation_degree,
                name=name,
                index=index,
            )
            ret_val = global_cart.follow_instruction(instruction, func=photo_func)
            return f"instruction followed ({ret_val})", 200

        return (
            f"location: {location}, rotation_degree: {rotation_degree}, name: {name}, index: {index}",
            200,
        )


if __name__ == "__main__":
    # threded=False --> allow only one instruction at a time. This could be
    # modifed by using a queue, but for now, having only a single thread is sufficient
    app.run(host="0.0.0.0", threaded=False)
