from flask import Flask, request

app = Flask(__name__)


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
    if request.method == "POST":
        # TODO: ensure reasonable
        mm_to_object = request.args.get("mm_to_object")
        angle = request.args.get("angle")
        return f"mm_to_object: {mm_to_object}, angle: {angle}"


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
        return f"/cart/images/capture"


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
    app.run()