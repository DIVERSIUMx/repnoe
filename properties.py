class InputProperty:
    ...

    def __init__(self, prop_type, val, name):
        self.type = {"float": float, "int": int,
                     "bool": bool, "str": str}[prop_type]
        self.val = self.type(val)
        self.name = name

    def to_data(self):
        return self.name, {"type": self.get_type(), "value": self.val}

    @staticmethod
    def from_data(name, data):
        return InputProperty(data["type"], data["value"], name)

    def get_type(self):
        return {float: "float", int: "integer", bool: "bool", str: "string"}[self.type]


class ControlProperty:
    ...

    def __init__(self, prop_type, val, name):
        self.type = {"float": float, "int": int,
                     "bool": bool, "str": str}[prop_type]
        self.val = self.type(val)
        self.name = name

    def to_data(self):
        return self.name, {"type": self.get_type(), "value": self.val}

    @staticmethod
    def from_data(name, data):
        return InputProperty(data["type"], data["value"], name)

    def get_type(self):
        return {float: "float", int: "integer", bool: "bool", str: "string"}[self.type]


def get_input_propertyes(data: dict):
    input_props = []
    for (key, val) in data.items():
        input_props.append(InputProperty.from_data(key, val))
    return input_props


def get_control_propertyes(data: dict):
    control_props = []
    for (key, val) in data.items():
        control_props.append(ControlProperty.from_data(key, val))
    return control_props


def to_data_input(props):
    res = {}
    for prop in props:
        name, val = prop.to_data()
        res[name] = val

    return res


def to_data_control(props):
    res = {}
    for prop in props:
        name, val = prop.to_data()
        res[name] = val

    return res
