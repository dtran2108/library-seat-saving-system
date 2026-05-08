from flask import Flask, render_template
import secrets

from forms import LoginForm
from flask_wtf import CSRFProtect

app = Flask(__name__)

# secret key prevents malicious hijacking of form from an outside submission
secret = secrets.token_urlsafe(16)
app.secret_key = secret

# forms in Flask
csrf = CSRFProtect(app)
 
@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    message = ""
    if form.validate_on_submit():
        message = "Invalid login credentials!"
    return render_template("auth/login.html", form=form, message=message)

@app.route("/sign-up", methods=['GET', 'POST'])
def sign_up():
    form = LoginForm()
    message = ""
    if form.validate_on_submit():
        message = "Invalid login credentials!"
    return render_template("auth/sign-up.html", form=form, message=message)

 
if __name__ == "__main__":
    app.run(debug=True)