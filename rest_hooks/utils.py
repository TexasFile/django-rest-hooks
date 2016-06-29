def get_module(path):
    """
    A modified duplicate from Django's built in backend
    retriever.

        slugify = get_module('django.template.defaultfilters.slugify')
    """
    try:
        from importlib import import_module
    except ImportError as e:
        from django.utils.importlib import import_module

    try:
        mod_name, func_name = path.rsplit('.', 1)
        mod = import_module(mod_name)
    except ImportError as e:
        raise ImportError(
            'Error importing alert function {0}: "{1}"'.format(mod_name, e))

    try:
        func = getattr(mod, func_name)
    except AttributeError:
        raise ImportError(
            ('Module "{0}" does not define a "{1}" function'
                            ).format(mod_name, func_name))

    return func


def find_and_fire_hook(event_name, instance, user_override=False):
    """
    Look up Hooks that apply
    """
    from django.db.models import Q
    from rest_hooks.models import Hook, HOOK_EVENTS

    if not event_name in HOOK_EVENTS.keys():
        raise Exception(
            '"{}" does not exist in `settings.HOOK_EVENTS`.'.format(event_name)
        )

    # fetch all registered hooks for this event
    hooks = Hook.objects.filter(event=event_name)

    # iterate over all registered hooks & deliver the event to each one
    for hook in hooks:
        hook.deliver_hook(instance)


def distill_model_event(instance, model, action, user_override=False):
    """
    Take created, updated and deleted actions for built-in 
    app/model mappings, convert to the defined event.name
    and let hooks fly.

    If that model isn't represented, we just quit silenty.
    """
    from rest_hooks.models import HOOK_EVENTS

    event_name = None
    for maybe_event_name, auto in HOOK_EVENTS.items():
        if auto:
            # break auto into App.Model, Action
            maybe_model, maybe_action = auto.rsplit('.', 1)
            maybe_action = maybe_action.rsplit('+', 1)
            if model == maybe_model and action == maybe_action[0]:
                event_name = maybe_event_name
                if len(maybe_action) == 2:
                    user_override = False

    if event_name:
        find_and_fire_hook(event_name, instance, user_override=user_override)
