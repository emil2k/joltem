from .mix import mixer
from .mock.models import load_model


def load_models(*objs):
    for obj in objs:
        yield load_model(obj)
