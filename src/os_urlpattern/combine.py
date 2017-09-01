class LevelCombiner(object):
    def __init__(self, config, default_pattern, current_level):
        self._default_pattern = default_pattern
        self._config = config
        self._min_combine_num = config.getint('make', 'min_combine_num')
        self._current_level = current_level
        self._nodes = []

    def last_level(self):
        return not self._nodes[0].child

    def add_node(self, node):
        self._nodes.append(node)

    def define(self):
        pass

    def combine(self):
        self.define()
        if self.last_level():
            return
        next_level_combiners = {}
        for node in self._nodes:
            p = hash(node.piece_pattern.pattern)
            if p not in next_level_combiners:
                next_level_combiners[p] = {}
            combiners = next_level_combiners[p]
            for child in node.children:
                fp = child.piece_pattern.fuzzy_pattern
                if fp not in combiners:
                    combiners[fp] = create_level_combiner(
                        self._config, child, self._current_level + 1)
                combiners[fp].add_node(child)
        for combiners in next_level_combiners.values():
            for combiner in combiners.values():
                combiner.combine()


class NodeBag(object):
    def __init__(self):
        self._piece_nodes = {}
        self._count = 0

    def add_node(self, node):
        piece = node.piece_pattern.piece
        if piece not in self._piece_nodes:
            self._piece_nodes[piece] = []
        self._piece_nodes[piece].append(node)
        self._count += node.count

    @property
    def count(self):
        return self._count


class SingleCombiner(LevelCombiner):
    def __init__(self, config, default_pattern, current_level):
        super(SingleCombiner, self).__init__(
            config, default_pattern, current_level)
        self._length_node_bag = {}

    def add_node(self, node):
        super(SingleCombiner, self).add_node(node)
        l = len(node.piece_pattern.piece)
        if l not in self._length_node_bag:
            self._length_node_bag[l] = NodeBag()
        self._length_node_bag[l].add_node(node)

    def define(self):
        pass


class MultilevelCombiner(object):
    pass


class FuzzyLevelCombiner(LevelCombiner):
    pass


def create_level_combiner(config, node, current_level, fuzzy=True):
    level_combiner_class = SingleCombiner
    default_pattern = node.piece_pattern.base_pattern
    if node.piece_pattern.piece_num > 1:
        if not fuzzy:
            level_combiner_class = MultilevelCombiner
        else:
            level_combiner_class = FuzzyLevelCombiner
            default_pattern = node.piece_pattern.fuzzy_pattern
    return level_combiner_class(config, default_pattern, current_level)


def combine(config, piece_pattern_tree):
    node = piece_pattern_tree.root
    level_combiner = create_level_combiner(config, node, 0)
    level_combiner.add_node(node)
    level_combiner.combine()
