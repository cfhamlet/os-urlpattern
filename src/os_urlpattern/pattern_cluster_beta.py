from .utils import Stack


def traverse_cluster(config, root):
    if root.count <= 1:
        return


def cluster(config, url_meta, piece_pattern_tree):
    stack = Stack()
    stack.push(piece_pattern_tree.root)
    p_cur = None
    p_pre = None
    min_cluster_num = config.getint('make', 'min_cluster_num')

    while len(stack) > 0:
        p_cur = stack.top()
        if not p_cur.children:
            stack.pop()
            p_pre = p_cur
        elif (p_pre is not None and p_pre.parrent != p_cur.parrent) or \
                (not p_cur.children[0].children):
            node = stack.pop()
            traverse_cluster(config, node)
            p_pre = p_cur
        else:
            p_pre = None
            stacked = False
            for child in p_cur.children:
                if child.count >= min_cluster_num:
                    stack.push(child)
                    stacked = True
            if not stacked:
                p_pre = p_cur.children[0]
