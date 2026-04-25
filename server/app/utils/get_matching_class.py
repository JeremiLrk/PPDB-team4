def get_matching_class(obj, classes):
    for cls in classes:
        if isinstance(obj, cls):
            return cls
    return None