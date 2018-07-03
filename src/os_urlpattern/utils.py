"""Utilities.
"""
import inspect
import logging
import os
import time
from functools import partial

from .compat import iteritems, itervalues


def pretty_counter(counter):
    """Format a dict like object.

    Args:
        counter (dict): The dict like object to be formatted.

    Returns:
        str: Formatted string.
    """

    return ", ".join(['{0}:{1}'.format(k, v) for k, v in iteritems(counter)])


def pick(iterable):
    """Get an obj from iterable object. """

    for obj in iterable:
        return obj


class Bag(object):
    """Uniq objects container.

    The objects in the bag can also be Bag instance.
    Use pick method to get a most inside object.
    Use iter_all method to iterate objects inside all inner bags.
    """

    __slots__ = ('_objs',)

    def __init__(self):
        self._objs = set()

    def add(self, obj):
        self._objs.add(obj)

    def __len__(self):
        return len(self._objs)

    def pick(self):
        obj = pick(self)
        while isinstance(obj, Bag):
            obj = pick(obj)
        return obj

    def __iter__(self):
        return iter(self._objs)

    def iter_all(self):
        for obj in self:
            if isinstance(obj, Bag):
                for o in obj.iter_all():
                    yield o
            else:
                yield obj


class TreeNode(object):
    """Node of a tree."""

    __slots__ = ('parrent', '_children', 'count',
                 'value', 'meta', '_level')

    def __init__(self, value):
        self.parrent = None
        self.count = 0
        self.value = value
        self.meta = None
        self._level = None
        self._children = None

    def leaf(self):
        return not self._children

    @property
    def level(self):
        """int: The level from root."""
        if self._level is None:
            l = 0
            n = self.parrent
            while n is not None:
                l += 1
                n = n.parrent
            self._level = l
        return self._level

    @property
    def children(self):
        return itervalues(self._children if self._children is not None else {})

    def add_child(self, kv):
        """Add a node to the children data set.

        Args:
            kv (pair): Key-value object, the key is used to identify
                a uniq node, the value is the node's data.

        Returns:
            tuple: 2-tuple, (node, is_new).
        """

        if self._children is None:
            self._children = {}
        k, v = kv
        is_new = False
        if k not in self._children:
            self._children[k] = self.__class__(v)
            self._children[k].parrent = self
            is_new = True
        child = self._children[k]
        return child, is_new


def build_tree(root, kv_sequence, count=1, meta=None):
    """Build a tee.

    This method will call the node's add_child(kv) to build tree.

    Args:
        root (TreeNode): Root node of a tree.
        kv_sequence (sequence): Objects will be used to build a tree.
        count (int, optional): Defaults to 1. Will increase the nodes count.
        meta (any, optional): Defaults to None. Will bind to the leaf node.

    Returns:
        tuple: 2-tuple, (node, is_new)
    """
    node = root
    node.count += count
    for kv in kv_sequence:
        node, is_new = node.add_child(kv)
        node.count += count
    if meta is not None:
        node.meta = meta

    return node, is_new


def dump_tree(root):
    """Dump each path of a tree.

    Args:
        root (TreeNode): The root node of a tree.

    Yields:
        list: List contains nodes from root to leaf as one path.
    """
    olist = []

    def _dump(node, _nodes):
        _nodes.append(node)
        if node.leaf():
            yield _nodes
            return
        for child in node.children:
            for nodes in _dump(child, _nodes):
                yield nodes
            _nodes.pop(-1)

    for nodes in _dump(root, olist):
        yield nodes


class LogSpeedAdapter(logging.LoggerAdapter):
    """Logger adapter for speed logging.

    Log only once when called every interal times,
    include total count and average speed.
    Used as 'with statement' for logging huge loop processing.

    """

    def __init__(self, logger, interval):
        super(LogSpeedAdapter, self).__init__(logger, {})
        self._count = 0
        assert(interval) > 0
        self._interval = interval
        self._start_time = time.time()
        self._replace()

    def _replace(self):
        for name in ['debug', 'info', 'warning', 'error', 'exception', 'critical']:
            setattr(self, name, partial(self._log, name))
        self.log = self._log

    def _log(self, name, msg, *args, **kwargs):
        self._count += 1

        if self._count % self._interval == 0:
            speed = self._speed()
            extra_msg = '{count} {speed:.1f}/s'.format(
                count=self._count, speed=speed)
            msg = ' '.join((msg, extra_msg))
            if isinstance(name, int):
                name = logging.getLevelName(name)
            getattr(self.logger, name)(msg, *args, **kwargs)

    def _speed(self):
        return self._count / (time.time() - self._start_time)

    def __enter__(self):
        self._start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        pass


def used_memory():
    """Human readable memory usage.

    Returns:
        str: Memory usage.
    """

    try:
        import psutil
    except:
        return '-'
    p = psutil.Process(os.getpid())
    memory = p.memory_info().rss / 1024.0
    for i in ('K', 'M', 'G'):
        if memory < 1024.0:
            return '%.1f%s' % (memory, i)
        memory = memory / 1024.0
    return '%.1fG' % memory


class MemoryUsageFormatter(logging.Formatter):
    """Formatter support memory keyword."""

    def __init__(self, fmt=None, datefmt=None):
        super(MemoryUsageFormatter, self).__init__(fmt, datefmt)
        self._log_memory = True
        if fmt and '%(memory)s' not in fmt:
            self._log_memory = False

    def format(self, record):
        if self._log_memory and 'memory' not in record.__dict__:
            record.__dict__['memory'] = used_memory()
        return super(MemoryUsageFormatter, self).format(record)


class cached_property(object):
    """Decrator for cache class property."""

    def __init__(self, func):
        self.__doc__ = getattr(func, "__doc__")
        self.func = func

    def __get__(self, obj, cls):
        if obj is None:
            return self

        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value


def get_classes(module, base_cls, include_base_cls=True):
    """Get specified classes form module.

    Args:
        module (module): Where to find classes.
        base_cls (type): The base class.
        include_base_cls (bool, optional): Defaults to True.
            Whether include base class.

    Returns:
        list: The specified classes.
    """
    def is_class(c):
        return inspect.isclass(c) \
            and issubclass(c, base_cls) \
            and (include_base_cls or c != base_cls)
    return [c for _, c in inspect.getmembers(module, is_class)]


def with_metaclass(meta, *bases):
    """Create a base class with a metaclass.

    From six.
    """
    # This requires a bit of explanation: the basic idea is to make a dummy
    # metaclass for one level of class instantiation that replaces itself with
    # the actual metaclass.
    class metaclass(type):

        def __new__(cls, name, this_bases, d):
            return meta(name, bases, d)

        @classmethod
        def __prepare__(cls, name, this_bases):
            return meta.__prepare__(name, bases)
    return type.__new__(metaclass, 'temporary_class', (), {})
