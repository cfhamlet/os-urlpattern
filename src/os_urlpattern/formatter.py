"""Clustered record formatter.
"""
import json
import sys

from .definition import BasePatternRule, Symbols
from .parse_utils import pack
from .utils import dump_tree, get_classes


class Formatter(object):
    """Base class for format clustered data.

    The subclass must define format method which yield formatted strings.
    """

    def format(self, url_meta, root, **kwargs):
        """Format the clustered tree.

        Args:
            url_meta (URLMeta): The url_meta.
            root (TreeNode): Root node of the clustered tree.
            **kwargs: Arbitray keyword arguments.

        Yields:
            str: the formatted string.

        """
        return
        yield


class PatternFormatter(Formatter):
    """Pattern only formatter."""

    def format(self, url_meta, root, **kwargs):
        """Yield URL pattern string.

        Args:
            url_meta (URLMeta): The URLMeta object.
            root (TreeNode): Root of a clustered piece tree.
            **kwargs: Arbitray keyword arguments.

        Yields:
            str: URL pattern string.

        """
        for nodes in dump_tree(root):
            yield pack(url_meta, [p.pattern for p in nodes[1:]])
            break


class ClusterFormatter(PatternFormatter):
    """URL pattern and meta data formatter.

    Yield URL pattern string first, then all meta data strings.
    """

    def format(self, url_meta, root, **kwargs):
        """Yield URL pattern and all bound meta data strings.

        Args:
            url_meta (URLMeta): The URLMeta object.
            root (TreeNode): Root of a clustered piece tree.
            **kwargs: Arbitray keyword arguments.

        Yields:
            object: URL pattern string first, then all meta
                data string prefixed with '\t'.

        """
        for r in super(ClusterFormatter, self).format(url_meta, root, **kwargs):
            yield r

        for nodes in dump_tree(root):
            if nodes[-1].meta is None:
                continue
            for obj in nodes[-1].meta:
                yield u'\t'.join((u'', str(obj)))


class InlineFormatter(PatternFormatter):
    """URL pattern and meta data formatter.

    URL pattern and meta data string in one line.
    """

    def format(self, url_meta, root, **kwargs):
        """Yield URL pattern with each bound meta data string in on line.

        Args:
            url_meta (URLMeta): The URLMeta object.
            root (TreeNode): Root of a clustered piece tree.
            **kwargs: Arbitray keyword arguments.

        Yields:
            object: URL pattern string + '\t' + str(meta)

        """
        url_pattern_string = None
        for r in super(InlineFormatter, self).format(url_meta, root, **kwargs):
            url_pattern_string = r

        for nodes in dump_tree(root):
            if nodes[-1].meta is None:
                continue
            for obj in nodes[-1].meta:
                yield u'\t'.join((url_pattern_string, str(obj)))


class JsonFormatter(Formatter):
    """Json formatter.

    Yiled Json string, {"ptn":url_pattern, "cnt":count}
        ptn: URL pattern string.
        cnt: Number of uniq path in the cluster.
    """

    def format(self, url_meta, root, **kwargs):
        """Yield json format string.

        Args:
            url_meta (URLMeta): The URLMeta object.
            root (TreeNode): Root of a clustered piece tree.
            **kwargs: Arbitray keyword arguments.

        Yields:
            str: Json string, key-value:
                ptn: URL pattern string.
                cnt: Number of uniq path in the cluster.
        """
        for nodes in dump_tree(root):
            p = pack(url_meta, [p.pattern for p in nodes[1:]])
            yield json.dumps({u'ptn': p, u'cnt': root.count})
            break


class ETEFormatter(Formatter):
    """Ete tree formatter."""

    def __init__(self):
        import ete3

    def format(self, url_meta, root, **kwargs):
        """Yield ete tree string.

        Args:
            url_meta (URLMeta): The URLMeta object.
            root (TreeNode): Root of a pattern tree.
            **kwargs: Arbitray keyword arguments.

        Yields:
            str: An ete tree string.
        """
        def f(pattern_node):
            sep = Symbols.EMPTY
            query_key = Symbols.EMPTY
            path_depth = url_meta.path_depth
            query_depth = len(url_meta.query_keys)
            current_level = pattern_node.level
            if path_depth < current_level \
                    and current_level <= (path_depth + query_depth):
                sep = Symbols.AMPERSAND
                if current_level == path_depth + 1:
                    sep = BasePatternRule.SINGLE_QUESTION
                query_key = url_meta.query_keys[current_level - path_depth - 1]
            elif current_level == path_depth + query_depth + 1:
                sep = Symbols.NUMBER
            return u' {sep}{query_key}{pattern_string}({count}) '.format(
                count=pattern_node.count,
                pattern_string=pattern_node.value,
                query_key=query_key,
                sep=sep)

        if root.count <= 0:
            return

        ete_tree = get_ete_tree(root, format=f)
        yield ete_tree.get_ascii(show_internal=True)


def get_ete_tree(root_node, format=str):
    """Transfor a tree-like object into ete tree.

    Args:
        root_node (TreeNode): The root of the tree.
        format (callable, optional): Defaults to str.
            A callable object to format the ete tree node.

    Returns:
        ete3.Tree: The ete tree.
    """
    from ete3 import Tree

    def add_children(node, ete_node):
        for child in node.children:
            ete_child = ete_node.add_child(name=format(child))
            add_children(child, ete_child)

    ete_root_node = Tree(name=format(root_node))
    add_children(root_node, ete_root_node)
    return ete_root_node


def pformat(name, url_meta, root, **kwargs):
    """Shortcut for formatting.

    Args:
        name (str): Format type.
        url_meta (URLMeta): The URLMeta object.
        root (TreeNode): Root of a clustered tree.
        **kwargs: Arbitray keyword arguments.

    Returns:
        Iterator: For iterate formatted strings.
    """
    return FORMATTERS[name.upper()].format(url_meta, root, **kwargs)


# Auto discover Formatter classes and init FORMATTERS.
FORMATTERS = {}
for c_cls in get_classes(sys.modules[__name__], Formatter):
    c_name = c_cls.__name__
    t = c_name.rfind('Formatter')
    if t < 0:
        raise ImportError('Invalid formatter name: %s' % c_name)
    name = c_name[0:t].upper() if c_name[0:t] else 'NULL'
    try:
        FORMATTERS[name] = c_cls()
    except:
        pass
