import logging
import os
import time
from importlib import import_module


def pretty_counter(counter):
    return ", ".join(['{0}:{1}'.format(k, v) for k, v in counter.items()])


class Bag(object):
    def __init__(self):
        self._objs = set()

    def add(self, obj):
        self._objs.add(obj)

    def __len__(self):
        return len(self._objs)

    def pick(self):
        obj = self._pick()
        while isinstance(obj, Bag):
            obj = obj._pick()
        return obj

    def _pick(self):
        for obj in self._objs:
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


class Stack(object):
    def __init__(self):
        self._objs = []

    def push(self, obj):
        self._objs.append(obj)

    def pop(self):
        return self._objs.pop()

    def top(self):
        return self._objs[-1]

    def __len__(self):
        return len(self._objs)


class LogSpeedAdapter(logging.LoggerAdapter):
    def __init__(self, logger, interval):
        super(LogSpeedAdapter, self).__init__(logger, {})
        self._count = 0
        self._interval = interval
        self._start_time = time.time()

    def process(self, msg, kwargs):
        self._count += 1

        if self._count % self._interval == 0:
            speed = self._speed()
            mem = used_memory()
            extra_msg = '[{mem}] {count} {speed:.1f}/s'.format(
                count=self._count, speed=speed, mem=mem)
            msg = ' '.join((msg, extra_msg))
            return msg, kwargs

    def debug(self, msg, *args, **kwargs):
        returnd = self.process(msg, kwargs)
        if not returnd:
            return
        msg, kwargs = returnd
        self.logger.debug(msg, *args, **kwargs)

    def _speed(self):
        now = time.time()
        return self._count / (now - self._start_time)


def used_memory():
    try:
        import psutil
    except:
        return '-'
    p = psutil.Process(os.getpid())
    memory = p.memory_info().rss / 1024.0
    for i in ['K', 'M', 'G']:
        if memory < 1024.0:
            return '%.1f%s' % (memory, i)
        memory = memory / 1024.0
    return '%.1fG' % memory


def get_ete_tree(root_node, format=str):
    from ete3 import Tree

    def add_children(node, ete_node):
        for child in node.children:
            ete_child = ete_node.add_child(name=format(child))
            add_children(child, ete_child)

    ete_root_node = Tree(name=format(root_node))
    add_children(root_node, ete_root_node)
    return ete_root_node


def load_obj(obj_path):
    module_path, obj_name = obj_path.rsplit('.', 1)
    _mod = import_module(module_path)
    return getattr(_mod, obj_name)
