from pattern import get_pattern_from_cache


class Combiner(object):
    def __init__(self, config, current_level):
        self._config = config
        self._min_combine_num = config.getint('make', 'min_combine_num')
        self._current_level = current_level
        self._nodes = []

    def last_level(self):
        return not self._nodes[0].children

    def add_node(self, node):
        self._nodes.append(node)

    def process(self):
        pass

    def combine(self):
        self.process()
        if self.last_level():
            return
        next_level_combiners = {}
        next_level = self._current_level + 1
        for node in self._nodes:
            n_hash = hash(node.pattern)
            if n_hash not in next_level_combiners:
                next_level_combiners[n_hash] = create_combiner(
                    self._config, node.children[0], next_level)
            for child in node.children:
                next_level_combiners[n_hash].add_node(child)
        for combiner in next_level_combiners.values():
            combiner.combine()


class _Bag(object):
    def __init__(self):
        self._objs = []
        self._count = 0

    @property
    def objs(self):
        return self._objs

    @property
    def num(self):
        return len(self._objs)

    def add(self, obj):
        self._objs.append(obj)
        self._count += obj.count

    @property
    def count(self):
        return self._count

    def set_pattern(self, pattern):
        for obj in self._objs:
            obj.set_pattern(pattern)


class _CombineStrategy(object):

    def __init__(self, config):
        self._min_combine_num = config.getint('make', 'min_combine_num')
        self._length_bags = {}

    def add(self, bag):
        piece = bag.objs[0].piece_pattern.piece
        length = len(piece)
        if length not in self._length_bags:
            self._length_bags[length] = _Bag()
        self._length_bags[length].add(bag)

    def process(self):
        keep_word = {}
        keep_length = {}
        for length, bag in self._length_bags.items():
            if bag.num >= self._min_combine_num:
                keep_length[length] = bag
            else:
                keep_word[length] = bag
        if len(keep_word) >= self._min_combine_num:
            for bag in keep_word.values():
                bag.set_pattern(bag.objs[0].objs[0].piece_pattern.base_pattern)

        if len(keep_length) >= self._min_combine_num:
            for bag in keep_length.values():
                bag.set_pattern(bag.objs[0].objs[0].piece_pattern.base_pattern)
        else:
            for length, bag in keep_length.items():
                bag.set_pattern(
                    bag.objs[0].objs[0].piece_pattern.exact_num_pattern(length))


class SingleCombiner(Combiner):
    def __init__(self, config,  current_level):
        super(SingleCombiner, self).__init__(
            config,  current_level)
        self._piece_node_bag = {}

    def add_node(self, node):
        super(SingleCombiner, self).add_node(node)
        piece = node.piece_pattern.piece
        if piece not in self._piece_node_bag:
            self._piece_node_bag[piece] = _Bag()
        self._piece_node_bag[piece].add(node)

    def process(self):
        high_prob = _CombineStrategy(self._config)
        low_prob = _CombineStrategy(self._config)

        for bag in self._piece_node_bag.values():
            if bag.count < self._min_combine_num:
                low_prob.add(bag)
            else:
                high_prob.add(bag)
        low_prob.process()
        high_prob.process()


class MultilevelCombiner(object):
    pass


class FuzzyCombiner(Combiner):
    pass


def create_combiner(config, node, current_level, fuzzy=True):
    combiner_class = SingleCombiner
    if node.piece_pattern.part_num > 1:
        if not fuzzy:
            combiner_class = MultilevelCombiner
        else:
            combiner_class = FuzzyCombiner
    return combiner_class(config, current_level)


def combine(config, piece_pattern_tree):
    node = piece_pattern_tree.root
    combiner = create_combiner(config, node, 0)
    combiner.add_node(node)
    combiner.combine()
