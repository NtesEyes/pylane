# -*- coding: utf-8 -*-


import traceback


class PylaneException(Exception):
    pass


class RequirementsInvalid(PylaneException):
    pass


def PylaneExceptionHandler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except PylaneException as e:
            print e.message
        # TODO
        except Exception as e:
            print 'Internal error occured, contact author if u need help.'
            print e.message
            print traceback.format_tb()
        exit(1)
    return wrapper
