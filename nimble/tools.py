import inspect

def setup_django_environment(settings_module_string):
    import os
    os.environ['DJANGO_SETTINGS_MODULE'] = settings_module_string

class LazyProperty(object):
    def __init__(self, getter):
        self.data = {}
        self.getter = getter

    def __get__(self, instance, owner):
        if instance not in self.data:
            self.data[instance] = self.getter(instance, owner)
        return self.data[instance]

    def __delete__(self, instance):
        try:
            del self.data[instance]
        except KeyError, ex:
            pass

def object_type(obj):
    cls = type(obj)
    return inspect.getmodule(cls).__name__, cls.__name__

def object_type_string(obj):
    return '.'.join(object_type(obj))
