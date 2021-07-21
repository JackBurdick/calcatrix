from flask import Flask

app = Flask(__name__)


@app.route("/")
def ok():
    return "ok"


@app.route("/cart/status")
def status():
    return "/cart/status"


@app.route("/cart/initialize")
def initialize():
    return "/cart/initialize"


@app.route("/cart/images/retrieve")
def retrieve():
    return "/cart/images/retrieve"


@app.route("/cart/images/capture")
def capture():
    return "/cart/images/capture"


if __name__ == "__main__":
    app.run()