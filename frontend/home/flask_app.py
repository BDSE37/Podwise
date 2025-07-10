from flask import Flask, render_template

app = Flask(
    __name__, static_url_path="", static_folder=".", template_folder="templates"
)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/podri")
def podri():
    return render_template("podri_integrated.html")


if __name__ == "__main__":
    app.run(debug=True)
