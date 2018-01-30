"""
This is a sphinx extension which watches autodoc events and extends docstrings with info
about implementation status of methods
"""

import inspect

from six import text_type as t
try:
    from sphinx.util import logging
except ImportError:  # el7 has old sphinx
    import logging


logger = logging.getLogger(__name__)


def get_method_names(kls):
    return set([x[0]
                for x in inspect.getmembers(kls, predicate=inspect.ismethod)
                if not x[0].startswith("_")])


def prepare_lines(txt):
    """ Let's put some preface first -- the newline is required b/c of reST """
    return [
        t(txt),
        t("")
    ]


def process_methods(txt, kls, methods, lines, short=True):
    lines += prepare_lines(txt)
    for method_name in methods:
        # :class:`conu.apidefs.backend.Backend` class.
        if short:
            lines.append(t(" * :meth:`%s.%s`" % (kls.__name__,  method_name)))
        else:
            lines.append(t(" * :meth:`%s.%s.%s`" % (kls.__module__, kls.__name__,  method_name)))
    lines.append(t(""))  # sphinx needs this


def process_autodoc(app, what, name, obj, options, lines):
    if not inspect.isclass(obj):
        return
    if obj.__module__.startswith("conu.apidefs."):
        return
    for parent_class in inspect.getmro(obj):
        if parent_class.__module__.startswith("conu.apidefs."):
            break
    else:
        return  # not found
    these_method_names = get_method_names(obj)
    parent_method_names = get_method_names(parent_class)
    extra = these_method_names.difference(parent_method_names)
    if extra:
        process_methods("These methods are specific to this backend:", obj, extra, lines)
    missing = []
    # we need to check for missing by looking where the method definition lives
    for method in inspect.getmembers(obj, predicate=inspect.ismethod):
        method_name, method_obj = method
        f = inspect.getfile(method_obj)
        method_code = inspect.getsource(method_obj)
        if "apidefs" in f and 'NotImplementedError' in method_code:
            missing.append(method_name)
    if missing:
        process_methods("These generic methods are not implemented in this backend:",
                        parent_class, missing, lines, short=False)


def setup(app):
    app.connect('autodoc-process-docstring', process_autodoc)

    return {'version': '0.1'}
