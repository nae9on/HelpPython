import inspect
import json
import sys


data = {
   "RandomInvert":{
      "chance": "0.7"
   },
   "RandomStretch": {
      "factor": "10",
      "chance": 0.5,
      "max_stretch_percent": 76
   }
}


class RandomInvert(object):
    def __init__(self, chance: float = 0.5):
        self.chance = max(0.0, min(1.0, chance))

    def __call__(self):
        print("self.chance: ", self.chance)


class RandomStretch(object):
    def __init__(self, factor: int, chance: float = 0.5, max_stretch_percent: int = 50):
        self.factor = factor
        self.chance = max(0.0, min(1.0, chance))
        self.max_stretch_percent = max_stretch_percent

    def __call__(self):
        print("self.factor: ", self.factor)
        print("self.chance: ", self.chance)
        print("self.max_stretch_percent: ", self.max_stretch_percent)


def read_json() -> dict:
    json_data: dict
    with open("data.json") as json_file:
        json_data = json.load(json_file)
    return json_data


def get_augmentation_object(class_type, class_parameters: dict):
    sig = inspect.signature(class_type.__init__)
    # sig_bind = sig.bind(class_parameters)
    attributes = []
    for param in sig.parameters.values():
        if param.name == 'self':
            continue
        new_param = class_parameters.setdefault(param.name, param.default)
        if new_param == inspect.Parameter.empty:
            print('Parameter not present in json and also there is no default available')
            raise KeyError
        attributes.append(param.annotation(new_param))

    return class_type(*attributes)


if __name__ == "__main__":
    # data = read_json()

    classes = {}
    for name, obj in inspect.getmembers(sys.modules[__name__]):
        if inspect.isclass(obj):
            classes[name] = obj

    for key, value in data.items():
        augmentation_object = get_augmentation_object(classes[key], value)
        augmentation_object()
        
