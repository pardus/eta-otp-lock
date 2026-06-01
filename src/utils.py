import pickle

class SafeUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        # only allow builtins for simple types
        if module == "builtins" and name in {"dict","list","str","int","float","bool","tuple"}:
            return getattr(__builtins__, name)
        raise pickle.UnpicklingError("global '%s.%s' is forbidden" % (module, name))

if __name__ == "__main__":
    import sys
    with open(sys.argv[1], "rb") as f:
        print(SafeUnpickler(f).load())