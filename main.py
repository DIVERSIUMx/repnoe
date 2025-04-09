import json
import os

from flask import Flask, abort, redirect, render_template, request
from flask_login import LoginManager, current_user, login_user

import properties
from data import db_session
from data.projects import Project
from data.users import User
from forms.login import UpdateUser, UserLogin
from forms.project import AddProject
from forms.property import AddProperty
from iot_api import blueprint

app = Flask(__file__)
app.config['SECRET_KEY'] = 'mega-sectret-key-ogo'

login_manager = LoginManager()
login_manager.init_app(app)


def main():
    if "db" not in os.listdir():
        os.makedirs("db")
    app.register_blueprint(blueprint)
    db_session.global_init("./db/blob.db")
    db_sess = db_session.create_session()
    admin = db_sess.query(User).filter(User.permissions == -1).first()
    if not admin:
        admin = User()
        admin.name = "Admin"
        admin.set_password("admin")
        admin.permissions = -1
        db_sess.add(admin)
        db_sess.commit()


@app.route("/login", methods=["GET", "POST"])
def login():
    if not current_user.is_authenticated:
        form = UserLogin()
        if form.validate_on_submit():
            db_sess = db_session.create_session()
            user = db_sess.query(User).filter(
                User.name == form.name.data).first()
            if user and user.check_password(form.password.data):
                login_user(user)
                return redirect("/projects")
            return render_template("login.html", form=form, title="Авторизация", message="Неверный логин или пароль", current_user=current_user)
        return render_template("login.html", form=form, title="Авторизация", current_user=current_user)
    return abort(404)


@app.route("/")
@app.route("/index")
@app.route("/projects")
def projects():
    if not current_user.is_authenticated:
        return redirect("/login")
    db_sess = db_session.create_session()
    projects = db_sess.query(Project).all()

    return render_template("projects.html", title="Проекты", projects=projects)


@app.route("/projects/add", methods=["GET", "POST"])
def add_project():
    if not current_user.is_authenticated:
        return redirect("/login")
    form = AddProject()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        project = Project()
        project.name = form.name.data
        project.description = form.description.data
        project.properties = json.dumps({"input": {}, "control": {}})
        db_sess.add(project)
        db_sess.commit()
        return redirect(f"/projects/redact/{project.id}")
    return render_template("add_project.html", form=form, title="Создать проект")


@app.route("/projects/delete/<int:id>")
def del_project(id):
    if not current_user.is_authenticated:
        return redirect("/login")
    db_sess = db_session.create_session()
    project = db_sess.query(Project).get(id)
    if not project:
        abort(404)
    db_sess.delete(project)
    db_sess.commit()
    return redirect("/projects")


@app.route("/projects/redact/<int:id>", methods=["GET", "POST"])
def redact_project(id):
    if not current_user.is_authenticated:
        return redirect("/login")
    db_sess = db_session.create_session()
    project = db_sess.query(Project).get(id)
    if not project:
        abort(404)
    form = AddProject()
    form.submit.label.text = "Применить"
    if request.method == "GET":
        form.name.data = project.name
        form.description.data = project.description
    else:
        if form.validate_on_submit():
            project.name = form.name.data
            project.description = form.description.data
            db_sess.commit()
        else:
            return render_template("project_dashboard.html", form=form, project=project, title=f'Проект "{project.name}"', message="Не все поля заполненны")
    return render_template("project_dashboard.html", project=project, form=form, title=f'Проект "{project.name}"')


@app.route("/projects/redact/<int:id>/props", methods=["GET", "POST"])
def redact_props(id):
    if not current_user.is_authenticated:
        return redirect("/login")
    db_sess = db_session.create_session()
    project = db_sess.query(Project).get(id)
    if not project:
        return abort(404)

    data = json.loads(project.properties)
    in_props = properties.get_input_propertyes(data["input"])
    con_props = properties.get_control_propertyes(data["control"])
    if request.method == "GET":
        return render_template("project_props.html", in_props=in_props, con_props=con_props, project=project)
    else:
        for prop in con_props:
            pre_val = request.form[prop.name]
            try:
                if prop.type is bool:
                    prop.val = pre_val == "1"
                else:
                    prop.val = prop.type(pre_val)
            except ValueError:
                return render_template("project_props.html", in_props=in_props, con_props=con_props, project=project, message="Не у всех полей введён верный формат данных")
        else:
            data["control"] = properties.to_data_control(con_props)
            project.properties = json.dumps(data)
            db_sess.commit()
            return render_template("project_props.html", in_props=in_props, con_props=con_props, project=project)


@app.route("/projects/redact/<int:id>/props/add", methods=["GET", "POST"])
def add_prop(id):
    if not current_user.is_authenticated:
        return redirect("/login")
    db_sess = db_session.create_session()
    project = db_sess.query(Project).get(id)
    if not project:
        return abort(404)
    form = AddProperty()

    if form.validate_on_submit():
        data = json.loads(project.properties)
        if form.prop_type.data == "input":
            if form.name.data in ["project", "apikey"] or form.name.data in data["input"].keys():
                return render_template("add_prop.html", form=form, message="Свойство с таким названием кже существует")
            props = properties.get_input_propertyes(data["input"])
            props.append(properties.InputProperty(form.prop_data_type.data,
                         ("")if form.prop_data_type == "str" else (0), form.name.data))
            data["input"] = properties.to_data_input(props)
            project.properties = json.dumps(data)
            db_sess.commit()
        if form.prop_type.data == "control":
            if form.name.data in data["control"].keys():
                return render_template("add_prop.html", form=form, message="Свойство с таким названием кже существует")
            props = properties.get_control_propertyes(data["control"])
            props.append(properties.ControlProperty(form.prop_data_type.data,
                         ("")if form.prop_data_type == "str" else (0), form.name.data))
            data["control"] = properties.to_data_control(props)
            project.properties = json.dumps(data)
            db_sess.commit()
        return redirect(f"/projects/redact/{id}/props")
    return render_template("add_prop.html", form=form)


@app.route("/projects/redact/<int:id>/props/delete/input/<prop_name>")
def delete_prop_in(id, prop_name):
    if not current_user.is_authenticated:
        return redirect("/login")
    db_sess = db_session.create_session()
    project = db_sess.query(Project).get(id)
    if not project:
        return abort(404)
    data = json.loads(project.properties)
    if prop_name not in data["input"].keys():
        return abort(404)
    del data["input"][prop_name]

    project.properties = json.dumps(data)
    db_sess.commit()
    return redirect(f"/projects/redact/{id}/props")


@app.route("/projects/redact/<int:id>/props/delete/control/<prop_name>")
def delete_prop_con(id, prop_name):
    if not current_user.is_authenticated:
        return redirect("/login")
    db_sess = db_session.create_session()
    project = db_sess.query(Project).get(id)
    if not project:
        return abort(404)
    data = json.loads(project.properties)
    if prop_name not in data["control"].keys():
        return abort(404)
    del data["control"][prop_name]

    project.properties = json.dumps(data)
    db_sess.commit()
    return redirect(f"/projects/redact/{id}/props")


@app.route("/user", methods=["GET", "POST"])
def user_redact():
    if not current_user.is_authenticated:
        return redirect("/login")
    db_sess = db_session.create_session()
    user = db_sess.query(User).get(current_user.id)
    form = UpdateUser()
    if request.method == "GET":
        form.name.data = user.name
    else:
        if form.validate_on_submit():
            if not user.check_password(form.password.data):
                return render_template("update_user.html", title="Настройки пользователя", form=form, message="Неверный пароль")
            # if db_sess.query(User).filter(User.name == form.name.data).get:
            for u in db_sess.query(User).filter(User.name == form.name.data):
                if user.id != u.id and user.name == form.name.data:
                    return render_template("update_user.html", title="Настройки пользователя", form=form, message="Пользователь с таким именем уже существует")
            if form.new_password.data != form.new_password_two.data:
                print(form.new_password.data, form.new_password_two.data)
                return render_template("update_user.html", title="Настройки пользователя", form=form, message="Пароли не совпадают")
            user.name = form.name.data
            user.set_password(form.new_password.data)
            db_sess.commit()
            return render_template("update_user.html", title="Настройки пользователя", form=form, message="Данные успешно изменены")
    return render_template("update_user.html", title="Настройки пользователя", form=form)


@login_manager.user_loader
def load_user(id):
    print(type(id))
    db_sess = db_session.create_session()
    return db_sess.query(User).get(id)


if __name__ == "__main__":
    main()
    app.run("127.0.0.1", port=8080)
