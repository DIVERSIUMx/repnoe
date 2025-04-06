import json

from flask import Blueprint, jsonify, make_response, request

import properties
from data import db_session
from data.projects import Project

blueprint = Blueprint(
    "iot_api",
    __name__,
    template_folder="templates"
)


@blueprint.route("/api")
def api():
    project_name = request.args.get('project')
    if not project_name:
        return make_response(jsonify({'error': 'Bad request, project name has not found'}), 400)
    db_sess = db_session.create_session()
    project = db_sess.query(Project).filter(
        Project.name == project_name).first()
    if not project:
        return make_response(jsonify({"error": "Not found"}), 404)
    data = json.loads(project.properties)
    in_props = properties.get_input_propertyes(data["input"])
    for prop in in_props:
        val = request.args.get(prop.name)
        if val:
            try:
                if prop.type is bool:
                    if val.lower() in ["true", "1"]:
                        prop.val = True
                    elif val.lower() in ["false", "0"]:
                        prop.val = False
                    else:
                        raise ValueError
                else:
                    prop.val = prop.type(val)
            except ValueError:
                return make_response(jsonify({"error": "Bad request"}), 400)
    else:
        data["input"] = properties.to_data_input(in_props)
        project.properties = json.dumps(data)
        db_sess.commit()
        con_props = properties.get_control_propertyes(data["control"])

        return jsonify({key: val for key, val in map(lambda f: (f.name, f.val), con_props)})
