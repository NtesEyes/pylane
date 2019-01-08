#!/usr/bin/env python
# encoding: utf-8

'''
All functions here must be written with function doc.
And all exceptions must be handled in this module....
Don't Import Any Unnecessary things.
Use remote ipc to inject, don't import them in remote process in case of reload.
'''


def get_insts(class_name):
    """get_insts(class_name) -> instance_list"""
    ins_list = []
    import gc
    for obj in gc.get_objects():
        try:
            if getattr(obj, "__class__", None):
                if obj.__class__.__name__ == class_name:
                    ins_list.append(obj)
        # weak ref items will raise an exc here
        except ReferenceError:
            continue
    return ins_list


def get_classes(class_name):
    """get_classes(class_name) -> class_object_list : cast new type class only"""
    cls_list = []
    import gc
    import inspect
    for obj in gc.get_objects():
        try:
            if getattr(obj, "__class__", None):
                if inspect.isclass(obj) and obj.__name__ == class_name:
                    cls_list.append(obj)
        # weak ref items will raise an exc here
        except ReferenceError:
            continue
    return cls_list


def cast_id(object_id):
    """cast_id(object_id) -> object"""
    if not getattr(cast_id, 'ensured', False):
        print('Warning: If you provide an invalid or expired id, '\
            + 'this call will cause a segment fault, '\
            + 'and the attached process will be killed.\n'\
            + 'cast_id will do nothing this time.\n'\
            + 'If you know whats going on, recall this function to execute.')
        setattr(cast_id, 'ensured', True)
        return
    import ctypes
    return ctypes.cast(object_id, ctypes.py_object).value


def get_source_code(obj, encoding='utf-8'):
    """get_source_code(obj, encoding='utf-8') -> source_code_string : print it for pretty format"""
    import inspect
    try:
        raw = ''.join(inspect.getsourcelines(obj)[0])
        if encoding:
            raw = raw.decode(encoding)
        return raw
    except Exception as e:
        print('failed, error:', e)
