class Persona:
    def __init__(self, data):
        self.arcana = data["arcana"]
        self.id = data["id"]
        self.inherits = data["inherits"]
        self.item = data["item"]
        self.itemr = data["itemr"]
        self.level = data["lvl"]
        self.name = data["name"]
        self.resists = data["resists"]
        self.skills = data["skills"]
        self.stats = data["stats"]
        self.trait = data["trait"]

    def __str__(self):
        return f"Persona: {self.name}, Arcana: {self.arcana}, Level: {self.level}"
