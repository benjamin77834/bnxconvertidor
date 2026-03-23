class Component:

    def __init__(self, id, type, inputs=None, attrs=None):
        self.id = id
        self.type = type.upper()
        self.inputs = inputs or []
        self.attrs = attrs or {}

    def __repr__(self):
        return f"Component(id={self.id}, type={self.type}, inputs={self.inputs}, attrs={self.attrs})"