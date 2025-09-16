def get_nested_value(dictionary, keys, default=None):
    """
    Safely get a value from a nested dictionary.

    :param dictionary: The dictionary to search
    :param keys: A list of keys to traverse
    :param default: The default value to return if the key is not found
    :return: The value if found, else the default value
    """
    for key in keys:
        if isinstance(dictionary, dict):
            dictionary = dictionary.get(key, default)
        else:
            return default
    return dictionary
