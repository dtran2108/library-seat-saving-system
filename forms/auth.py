from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length

class LoginForm(FlaskForm):
    input_style = (
        "h-9 w-full min-w-0 rounded-md border border-slate-200 bg-transparent px-3 py-1 text-base transition-colors "
        "placeholder:text-slate-500 "
        "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-slate-950 "
        "disabled:cursor-not-allowed disabled:opacity-50 "
        "md:text-sm "
        "dark:border-slate-800 dark:placeholder:text-slate-400 dark:focus-visible:ring-slate-300"
    )
    username = StringField('Enter your username',
                           render_kw={"class": input_style},
                           validators=[DataRequired()])
    password = PasswordField('Enter your password',
                             render_kw={"class": input_style},
                             validators=[DataRequired()])
    submit = SubmitField('Submit',
                         render_kw={"class": "mt-4 h-9 px-4 py-2 inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors bg-slate-900 text-slate-50 hover:bg-slate-900/90 shadow focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-slate-950 disabled:pointer-events-none disabled:opacity-50"})