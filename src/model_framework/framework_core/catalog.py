class ComponentCatalog:
    def __init__(self):
        self.items = {}
    def register(self, name, component):
        self.items[name] = component
    def resolve(self, name):
        if name not in self.items:
            raise KeyError(f"Plugin not registered: {name}")
        return self.items[name]
