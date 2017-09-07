from pattern import get_pattern_from_cache
from url_meta import URLMeta
from piece_pattern_tree import PiecePatternTree


class Combiner(object):
    def __init__(self, config, current_level, **kwargs):
        self._config = config
        self._current_level = current_level
        self._from_level = kwargs.get('from_level', 0)
        self._min_combine_num = config.getint('make', 'min_combine_num')
        self._nodes = []

    def last_level(self):
        return not self._nodes[0].children

    def add_node(self, node):
        self._nodes.append(node)

    def process(self):
        pass

    def combine(self):
        next_level_combiners = {}
        next_level = self._current_level + 1

        if self._current_level < self._from_level:
            next_level_combiner = create_combiner(
                self._config, self._nodes[0].children[0], next_level, from_level=self._from_level)
            for node in self._nodes:
                for child in node.children:
                    next_level_combiner.add_node(child)
            next_level_combiners[1] = next_level_combiner
        else:
            self.process()
            if self.last_level():
                return
            for node in self._nodes:
                n_hash = hash(node.pattern)
                if n_hash not in next_level_combiners:
                    next_level_combiners[n_hash] = create_combiner(
                        self._config, node.children[0], next_level, from_level=self._from_level)
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
    def __init__(self, config, current_level, **kwargs):
        super(SingleCombiner, self).__init__(config, current_level, **kwargs)
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


class MultilevelCombiner(Combiner):
    def __init__(self, config, current_level, **kwargs):
        super(MultilevelCombiner, self).__init__(
            config, current_level, **kwargs)
        from pattern_maker import PatternMaker
        self._maker = None

    def add_node(self, node):
        self._maker.load(
            node.piece_patterns.sub_piece_patterns(), node.count, uniq_path=False)

    def combine(self):
        pattern_tree = self._maker.make()


class FuzzyCombiner(Combiner):
    def __init__(self, config, current_level, **kwargs):
        super(FuzzyCombiner, self).__init__(config, current_level, **kwargs)
        self._multi_level_combiners = {}

    def add_node(self, node):
        super(FuzzyCombiner, self).add_node(node)
        b_hash = hash(node.piece_pattern.base_pattern)
        if b_hash not in self._multi_level_combiners:
            url_meta = URLMeta(node.piece_pattern.part_num, [], False)
            self._multi_level_combiners = create_combiner(
                self._config, node, self._current_level, multi=True, url_meta=url_meta)
        self._multi_level_combiners[b_hash].add_node(node)

    def process(self):
        for combiner in self._multi_level_combiners.values():
            combiner.combine()


def create_combiner(config, node, current_level, **kwargs):
    combiner_class = SingleCombiner
    if node.piece_pattern.part_num > 1:
        if kwargs.get('multi'):
            combiner_class = MultilevelCombiner
        else:
            combiner_class = FuzzyCombiner
    return combiner_class(config, current_level, **kwargs)


def combine(config, piece_pattern_tree, **kwargs):
    node = piece_pattern_tree.root
    combiner = create_combiner(config, node, 0, **kwargs)
    combiner.add_node(node)
    combiner.combine()
