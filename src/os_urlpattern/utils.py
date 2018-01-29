import os
import time
import logging


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
