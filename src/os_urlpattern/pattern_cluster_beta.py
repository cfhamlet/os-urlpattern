from utils import Stack


def traverse_cluster(config, root):
    if root.count <= 1:
        return


def cluster(config, url_meta, piece_pattern_tree):
    stack = Stack()
    stack.push(piece_pattern_tree.root)
    p_cur = None
    p_pre = None

    while len(stack) != 0:
        p_cur = stack.top()
        if not p_cur.children:
            stack.pop()
            p_pre = p_cur
        elif p_pre is not None and p_pre.parrent != p_cur.parrent:
            node = stack.pop()
            traverse_cluster(config, node)
            p_pre = p_cur
        else:
            for child in p_cur.children:
                stack.push(child)
