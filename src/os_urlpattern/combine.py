from pattern import get_pattern_from_cache
from url_meta import URLMeta
from piece_pattern_tree import PiecePatternTree


class Combiner(object):
    def __init__(self, combiner_manager, current_level, **kwargs):
        self._combiner_manager = combiner_manager
        self._current_level = current_level
        self._min_combine_num = self.config.getint('make', 'min_combine_num')
        self._nodes = []

    @property
    def url_meta(self):
        return self._combiner_manager.url_meta

    @property
    def config(self):
        return self._combiner_manager.config

    def last_level(self):
        return self.url_meta.depth == self._current_level

    def last_path_level(self):
        return self.url_meta.path_depth == self._current_level

    def add_node(self, node):
        self._nodes.append(node)

    def process(self):
        pass

    def combine(self):
        self.process()
        if self.last_level():
            return
        next_level_combiners = {}
        for node in self._nodes:
            n_hash = hash(node.pattern)
            if n_hash not in next_level_combiners:
                next_level_combiners[n_hash] = self._combiner_manager.create_combiner(
                    node.children[0])
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


class CombineStrategy(object):
    def __init__(self, config):
        self._min_combine_num = config.getint('make', 'min_combine_num')

    def add(self, bag):
        pass

    def process(self):
        pass


class LengthCombineStrategy(CombineStrategy):

    def __init__(self, config):
        super(LengthCombineStrategy, self).__init__(config)
        self._length_bags = {}

    def add(self, bag):
        length = bag.objs[0].piece_pattern.piece_length
        if length not in self._length_bags:
            self._length_bags[length] = _Bag()
        self._length_bags[length].add(bag)

    def _set_pattern(self, length_bags, use_base=False):
        for length, bag in length_bags.items():
            pattern = None
            if use_base:
                pattern = bag.objs[0].objs[0].piece_pattern.base_pattern
            else:
                pattern = bag.objs[0].objs[0].piece_pattern.exact_num_pattern(
                    length)
            bag.set_pattern(pattern)


class LowProbLengthCombineStrategy(LengthCombineStrategy):

    def process(self):
        if len(self._length_bags) == 1:
            bag = self._length_bags.values()[0]
            if bag.num >= self._min_combine_num:
                self._set_pattern(self._length_bags)
            return

        length_keep = {}
        length_unknow = {}
        for length, bag in self._length_bags.items():
            if bag.num >= self._min_combine_num:
                length_keep[length] = bag
            else:
                length_unknow[length] = bag
        if len(length_unknow) >= self._min_combine_num:
            self._set_pattern(self._length_bags, use_base=True)
        else:
            if len(length_keep) == 1:
                self._set_pattern(length_keep)
            else:
                self._set_pattern(self._length_bags, use_base=True)


class HighProbLengthCombineStrategy(CombineStrategy):
    def process(self):
        pass


class SingleCombiner(Combiner):
    def __init__(self, combiner_manager, current_level, **kwargs):
        super(SingleCombiner, self).__init__(
            combiner_manager, current_level, **kwargs)
        self._piece_node_bag = {}

    def add_node(self, node):
        super(SingleCombiner, self).add_node(node)
        piece = node.piece_pattern.piece
        if piece not in self._piece_node_bag:
            self._piece_node_bag[piece] = _Bag()
        self._piece_node_bag[piece].add(node)

    def process(self):
        low_prob = LowProbLengthCombineStrategy(self.config)
        high_prob = HighProbLengthCombineStrategy(self.config)

        for bag in self._piece_node_bag.values():
            if bag.count < self._min_combine_num:
                low_prob.add(bag)
            else:
                high_prob.add(bag)
        low_prob.process()
        high_prob.process()


class MultiPartCombineStrategy(CombineStrategy):
    def __init__(self, config):
        super(MultiPartCombineStrategy, self).__init__(config)
        self._base_pattern_bags = {}

    def add(self, bag):
        base_hash = hash(bag.objs[0].piece_pattern.base_pattern)
        if base_hash not in  self._base_pattern_bags:
            self._base_pattern_bags[base_hash] = _Bag()
        self._base_pattern_bags[base_hash].add(bag)

    def _combine(self, pattern_bags):
        pass

    def process(self):
        if len(self._base_pattern_bags) == 1:
            bag = self._base_pattern_bags.values()[0]
            if bag.num >= self._min_combine_num:
                self._combine(self._base_pattern_bags)



class MultilevelCombiner(Combiner):
    def __init__(self, combiner_manager, current_level, **kwargs):
        super(MultilevelCombiner, self).__init__(
            combiner_manager, current_level, **kwargs)
        self._piece_pattern_tree = PiecePatternTree(kwargs['url_meta'])

    def add_node(self, node):
        super(MultilevelCombiner, self).add_node(node)
        self._piece_pattern_tree.add_piece_patterns(
            node.piece_pattern.mixed_piece_patterns, node.count)

    def combine(self):
        combine(self.config, self._piece_pattern_tree)
        piece_pattern_dict = {}
        for path in self._piece_pattern_tree.dump_paths():
            piece = ''.join([node.piece for node in path])
            pattern = get_pattern_from_cache(
                ''.join([str(node.pattern) for node in path]))
            piece_pattern_dict[piece] = pattern
        for node in self._nodes:
            if node.piece in piece_pattern_dict:
                node.set_pattern(piece_pattern_dict[node.piece])


class FuzzyCombiner(Combiner):
    def __init__(self, combiner_manager, current_level, **kwargs):
        super(FuzzyCombiner, self).__init__(
            combiner_manager, current_level, **kwargs)
        # self._multi_level_combiners = {}
        # self._base_type = {}
        # self._mixed_type = {}
        self._piece_node_bag = {}

    def add_node(self, node):
        super(FuzzyCombiner, self).add_node(node)
        piece = node.piece_pattern.piece
        if piece not in self._piece_node_bag:
            self._piece_node_bag[piece] = _Bag()
        self._piece_node_bag[piece].add(node)

        # base_hash = hash(node.piece_pattern.base_pattern)
        # mixed_hash = hash(node.piece_pattern.mixed_base_pattern)
        # if base_hash not in self._base_type:
        #     self._base_type[base_hash] = 0
        # self._base_type[base_hash] += 1
        # if mixed_hash not in self._mixed_type:
        #     self._mixed_type[mixed_hash] = 0
        # self._mixed_type[mixed_hash] += 1

        # b_hash = hash(node.piece_pattern.mixed_base_pattern)
        # if b_hash not in self._multi_level_combiners:
        #     url_meta = URLMeta(
        #         len(node.piece_pattern.mixed_piece_patterns), [], False)
        #     self._multi_level_combiners[b_hash] = self._combiner_manager.create_combiner(
        #         node, url_meta=url_meta, multi=True)
        # self._multi_level_combiners[b_hash].add_node(node)

    def process(self):
        low_prob = MultiPartCombineStrategy(self.config)

        for bag in self._piece_node_bag.values():
            if bag.count < self._min_combine_num:
                low_prob.add(bag)
        low_prob.process()


class CombinerManager(object):
    def __init__(self, config, piece_pattern_tree, **kwargs):
        self._config = config
        self._piece_pattern_tree = piece_pattern_tree

    @property
    def config(self):
        return self._config

    @property
    def url_meta(self):
        return self._piece_pattern_tree.url_meta

    def combine(self):
        node = self._piece_pattern_tree.root
        combiner = self.create_combiner(node)
        combiner.add_node(node)
        combiner.combine()

    def create_combiner(self, node, **kwargs):
        current_level = node.current_level
        combiner_class = SingleCombiner
        if node.piece_pattern.part_num > 1:
            if kwargs.get('multi'):
                combiner_class = MultilevelCombiner
            else:
                combiner_class = FuzzyCombiner
        return combiner_class(self, current_level, **kwargs)


def combine(config, piece_pattern_tree, **kwargs):
    combiner_manager = CombinerManager(config, piece_pattern_tree, **kwargs)
    combiner_manager.combine()
