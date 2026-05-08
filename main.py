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
 
@app.route("/", methods=['GET', 'POST'])
def hello_world():
    form = LoginForm()
    message = ""
    if form.validate_on_submit():
        message = "Invalid login credentials!"
    return render_template("auth/login.html", form=form, message=message)
 
if __name__ == "__main__":
    app.run(debug=True)