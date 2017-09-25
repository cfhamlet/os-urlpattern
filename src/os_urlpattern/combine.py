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

    def add_bag(self, bag):
        pass

    def process(self):
        pass

    def combine(self):
        self.process()
        if self.last_level():
            return
        next_level_combiners = {}
        for node in self._nodes:
            next_level = node.current_level + 1
            n_hash = hash(node.pattern)
            if n_hash not in next_level_combiners:
                next_level_combiners[n_hash] = PieceCombiner(
                    self._combiner_manager, next_level)
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


class LengthCombiner(Combiner):
    def __init__(self, combiner_manager, current_level, **kwargs):
        super(LengthCombiner, self).__init__(
            combiner_manager, current_level, **kwargs)
        self._length_bags = {}

    def add_bag(self, bag):
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

    def combine(self):
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


class BasePatternCombiner(Combiner):
    def __init__(self, combiner_manager, current_level, **kwargs):
        super(BasePatternCombiner, self).__init__(
            combiner_manager, current_level, **kwargs)
        self._base_pattern_bags = {}

    def add_bag(self, bag):
        h = hash(bag.objs[0].piece_pattern.base_pattern)
        if h not in self._base_pattern_bags:
            self._base_pattern_bags[h] = _Bag()
        self._base_pattern_bags[h].add(bag)

    def _combine_base_pattern(self, pattern_bags):
        for bag in pattern_bags.values():
            node = bag.objs[0].objs[0]
            part_num = node.piece_pattern.part_num
            combiner = MultilevelCombiner(
                self._combiner_manager, self._current_level, part_num=part_num, mixed=False)
            for piece_bag in bag.objs:
                combiner.add_bag(piece_bag)
            combiner.combine()

    def _combine_mixed_pattern(self, pattern_bags):
        mixed_combiners = {}
        for bag in pattern_bags.values():
            node = bag.objs[0][0]
            h = hash(node.piece_pattern.mixed_piece_pattern)
            if h not in mixed_combiners:
                part_num = node.piece_pattern.mixed_part_num
                if part_num == 1:
                    combiner_class = LengthCombiner
                else:
                    combiner_class = MultilevelCombiner
                mixed_combiners[h] = combiner_class(
                    self._combiner_manager, self._current_level, part_num=part_num, mixed=True)
            combiner = mixed_combiners[h]

            for piece_bag in bag.objs:
                combiner.add_bag(piece_bag)
            combiner.combine()

    def combine(self):
        if len(self._base_pattern_bags) == 1:
            bag = self._base_pattern_bags.values()[0]
            if bag.num >= self._min_combine_num:
                self._combine_base_pattern(self._base_pattern_bags)
            return

        low_prob = {}
        high_prob = {}
        for h, bag in self._base_pattern_bags.items():
            if bag.num >= self._min_combine_num:
                high_prob[h] = bag
            else:
                low_prob[h] = bag

        if len(low_prob) > self._min_combine_num:
            self._combine_mixed_pattern(self._base_pattern_bags)
        else:
            if len(high_prob) == 1:
                self._combine_base_pattern(high_prob)
            else:
                self._combine_mixed_pattern(self._base_pattern_bags)


class MultilevelCombiner(Combiner):
    def __init__(self, combiner_manager, current_level, **kwargs):
        super(MultilevelCombiner, self).__init__(
            combiner_manager, current_level, **kwargs)
        self._mixed = kwargs['mixed']
        part_num = kwargs['part_num']
        self._url_meta = URLMeta(part_num, [], False)
        self._piece_pattern_tree = PiecePatternTree()

    def add_bag(self, bag):
        for node in bag.objs:
            pp = node.piece_pattern.sub_piece_patterns
            if self._mixed:
                pp = node.piece_pattern.mixed_piece_patterns
            self._piece_pattern_tree.add_piece_patterns(
                pp, node.count)
            self.add_node(node)

    def combine(self):
        combine(self.config, self._url_meta, self._piece_pattern_tree)
        piece_pattern_dict = {}
        for path in self._piece_pattern_tree.dump_paths():
            piece = ''.join([node.piece for node in path])
            pattern = get_pattern_from_cache(
                ''.join([str(node.pattern) for node in path]))
            piece_pattern_dict[piece] = pattern
        for node in self._nodes:
            if node.piece in piece_pattern_dict:
                node.set_pattern(piece_pattern_dict[node.piece])


class PieceCombiner(Combiner):
    def __init__(self, combiner_manager, current_level, **kwargs):
        super(PieceCombiner, self).__init__(
            combiner_manager, current_level, **kwargs)
        self._piece_node_bag = {}

    def add_node(self, node):
        super(PieceCombiner, self).add_node(node)
        piece = node.piece_pattern.piece
        if piece not in self._piece_node_bag:
            self._piece_node_bag[piece] = _Bag()
        self._piece_node_bag[piece].add(node)

    def process(self):
        if len(self._piece_node_bag) == 1:
            return

        combiner_class = LengthCombiner
        if self._nodes[0].piece_pattern.part_num > 1:
            combiner_class = BasePatternCombiner

        combiner = combiner_class(
            self._combiner_manager, self._current_level)

        for bag in self._piece_node_bag.values():
            if bag.count < self._min_combine_num:
                combiner.add_bag(bag)
        combiner.combine()


class CombinerManager(object):
    def __init__(self, config, url_meta, piece_pattern_tree, **kwargs):
        self._config = config
        self._url_meta = url_meta
        self._piece_pattern_tree = piece_pattern_tree

    @property
    def config(self):
        return self._config

    @property
    def url_meta(self):
        return self._url_meta

    def combine(self):
        node = self._piece_pattern_tree.root
        combiner = PieceCombiner(self, 0)
        combiner.add_node(node)
        combiner.combine()


def combine(config, url_meta, piece_pattern_tree, **kwargs):
    combiner_manager = CombinerManager(
        config, url_meta, piece_pattern_tree, **kwargs)
    combiner_manager.combine()
