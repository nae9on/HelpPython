# Reference
# https://docs.python.org/3/library/abc.html

import abc
import random
import inspect


class ModifierInterfaceClass(metaclass=abc.ABCMeta):
    __slots__ = ()

    @abc.abstractmethod
    def __call__(self, image, boxes, classes):
        pass

    @classmethod
    def __subclasshook__(cls, subclass):
        if cls is ModifierInterfaceClass:
            attrs = set(dir(subclass))

            # Check 1 - if all abstract methods are implemented
            if set(cls.__abstractmethods__) > attrs:
                return False

            # Check 2 - if default constructable
            try:
                subclass()
            except TypeError:
                return False

            # Check 3 - the call should take exactly three arguments image, boxes and labels
            sig = inspect.signature(subclass.__call__)
            attribute_names = []
            attribute_default_value = []
            for param in sig.parameters.values():
                attribute_names.append(param.name)
                attribute_default_value.append(param.default)

            if len(attribute_names) != 4 \
                    or attribute_names[0] != 'self' \
                    or attribute_names[1] not in ('img', 'image', 'tensor', 'cvimage') \
                    or attribute_names[2] != 'boxes' \
                    or attribute_names[3] not in ('labels', 'classes'):
                return False

            if attribute_default_value[1] != inspect.Parameter.empty:
                return False

            # Return true when all the checks have passed
            return True

        return NotImplemented


class Modifier1(object):
    def __init__(self):
        self.probability = 0.5

    def __call__(self, image, boxes, classes):
        _, width, _ = image.shape
        random_number = random.uniform(0.0, 1.0)
        if random_number < float(self.probability):
            print(random_number, float(self.probability))
            image = image[:, ::-1]
            if boxes is not None:
                boxes = boxes.copy()
                boxes[:, 0::2] = width - boxes[:, 2::-2]
        return image, boxes, classes


class Modifier2(object):
    def __init__(self, p=0.5):
        self.probability = p

    def __call__(self, image, boxes=None, classes=None):
        return image, boxes, classes


class NotModifier1(object):
    pass


class NotModifier2(object):
    def __init__(self, p):
        self.probability = p


class NotModifier3(object):
    def __init__(self):
        self.probability = 0.5

    def __call__(self, image):
        return image


class NotModifier4(object):
    def __init__(self):
        self.probability = 0.5

    def __call__(self, image, box, classes):
        return image, box, classes


class NotModifier5(object):
    def __init__(self):
        self.probability = 0.5

    def __call__(self, image=None, boxes=None, classes=None):
        return image, boxes, classes


class NotModifier6(ModifierInterfaceClass):
    pass


if __name__ == "__main__":
    assert issubclass(Modifier1, ModifierInterfaceClass)
    assert isinstance(Modifier1(), ModifierInterfaceClass)

    assert issubclass(Modifier2, ModifierInterfaceClass)
    assert isinstance(Modifier2(), ModifierInterfaceClass)

    assert not issubclass(NotModifier1, ModifierInterfaceClass)
    assert not isinstance(NotModifier1(), ModifierInterfaceClass)

    assert not issubclass(NotModifier2, ModifierInterfaceClass)

    # TypeError: __init__() missing 1 required positional argument: 'p'
    # assert not isinstance(NotModifier2(), ModifierInterfaceClass)

    assert not issubclass(NotModifier3, ModifierInterfaceClass)
    assert not isinstance(NotModifier3(), ModifierInterfaceClass)

    assert not issubclass(NotModifier4, ModifierInterfaceClass)
    assert not isinstance(NotModifier4(), ModifierInterfaceClass)

    assert not issubclass(NotModifier5, ModifierInterfaceClass)
    assert not isinstance(NotModifier5(), ModifierInterfaceClass)

    assert not issubclass(NotModifier6, ModifierInterfaceClass)

    # TypeError: Can't instantiate abstract class NotModifier6 with abstract methods __call__
    # assert not isinstance(NotModifier6(), ModifierInterfaceClass)