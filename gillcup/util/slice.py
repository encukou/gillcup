def get_slice_indices(source_len, index):
    try:
        index = int(index)
    except TypeError:
        try:
            indices = index.indices
        except AttributeError:
            message = 'indices must be slices or integers, not {}'
            raise TypeError(message.format(type(index).__name__))
        start, stop, step = indices(source_len)
        if step not in (None, 1):
            raise IndexError('non-1 step not supported')
        if stop < start:
            stop = start
        return start, stop
    else:
        if index < 0:
            index += source_len
        if not (0 <= index < source_len):
            raise IndexError('index out of range')
        return index, index + 1
