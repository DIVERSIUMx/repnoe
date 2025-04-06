from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField
from wtforms.validators import DataRequired


class AddProperty(FlaskForm):
    name = StringField("Название", validators=[DataRequired()])
    prop_type = SelectField("Тип свойства", choices=[
                            ("input", "Вывода"), ("control", "Ввода")])
    prop_data_type = SelectField("Тип данных", choices=[(
        "int", "integer"), ("float", "float"), ("bool", "bool"), ("str", "string")])
    submit = SubmitField("Подтвердить")
