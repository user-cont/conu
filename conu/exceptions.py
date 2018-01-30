from __future__ import print_function, unicode_literals


class ConuException(Exception):
    """ Generic exception when something goes wrong """


class PackageSignatureException(ConuException):
    """ Exception raised when package signature validation goes wrong"""
