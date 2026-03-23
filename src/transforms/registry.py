TRANSFORMS = {}

def register(name):

    def wrapper(fn):
        TRANSFORMS[name] = fn
        return fn

    return wrapper