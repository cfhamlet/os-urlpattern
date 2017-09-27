import os
import time
import logging


class Counter(object):
    def __init__(self, logger_name, log_interval):
        self._start_time = None
        self._count = 0
        self._log_interval = log_interval
        self._logger = logging.getLogger(logger_name)

    def reset(self):
        self._start_time = time.time()
        self._count = 0

    def _speed(self):
        now = time.time()
        return self._count / (now - self._start_time)

    def _log(self, tag):
        sf = '[{tag}] [{mem}] {count} {speed:.1f}/s'
        self._logger.debug(sf.format(tag=tag, mem=used_memory(),
                                     count=self._count, speed=self._speed()))

    def log(self, tag, force=False):

        self._count += 1
        if force or self._count % self._log_interval == 0:
            self._log(tag)


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
