import inspect
import collections


KEYWORD_ONLY = inspect.Parameter.KEYWORD_ONLY


def fix_public_signature(func):
    """Remove private arguments from the signature of a function

    Private arguments are keyword-only, and prefixed by an underscore.
    """
    old_signature = inspect.signature(func)
    new_signature = old_signature.replace(parameters=[
        p for name, p in old_signature.parameters.items()
        if not (p.name.startswith('_') and p.kind == KEYWORD_ONLY)
    ])
    func.__signature__ = new_signature
    return func
