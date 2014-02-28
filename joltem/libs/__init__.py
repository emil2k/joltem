from .mix import mixer


def load_model(model_object):
    """ Reload model to check if metrics updated properly.

    :return Model: Reloaded instance.

    """
    return model_object.__class__._default_manager.select_for_update().get( #noqa
        pk=model_object.pk)


def load_models(*objs):
    for obj in objs:
        yield load_model(obj)
