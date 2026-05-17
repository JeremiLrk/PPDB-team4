def get_matching_class(obj, classes):
    """Return the first class from the list that matches the type of the given object."""
    for cls in classes:
        if isinstance(obj, cls):
            return cls
    return None