import json

class Json:
    """A class of functions to help with JSONw"""
    @staticmethod
    def load(file_path):
        """Load a JSON file"""
        with open(file_path, 'r') as f:
            return json.load(f)

    @staticmethod
    def dump(file_path, data):
        """Dump data to a JSON file"""
        with open(file_path, 'w') as f:
            json.dump(data, f)

    @staticmethod
    def pretty_dump(file_path, data):
        """Dump data to a JSON file with indentation"""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def pretty_print(data):
        """Print data to the console with indentation"""
        print(json.dumps(data, indent=4))


class JsHandler(Json):
    def __init__(self, file_name):
        self.latest = self.load(file_name)
        self.file = file_name

    @classmethod
    def from_dict(cls, data, file_name):
        """Create a JsHandler from a dictionary"""
        cls.pretty_dump(file_name, data)
        return cls(file_name)


    def __getitem__(self, item):
        return self.latest[item]

    def __setitem__(self, key, value):
        self.latest[key] = value

    def __delitem__(self, key):
        del self.latest[key]

    def __contains__(self, item):
        return item in self.latest

    def __iter__(self):
        return iter(self.latest)

    def __enter__(self):
        """On exit dump the latest data to the file"""
        return self.latest

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.save()

    def update(self, updatedDict):
        self.latest.update(updatedDict)

    def getDict(self):
        return self.latest

    def save(self):
        self.pretty_dump(self.file, self.latest)

    def jsonify(self):
        return json.dumps(self.latest, indent=4)

