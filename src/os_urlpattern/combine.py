from pattern import get_pattern_from_cache
from url_meta import URLMeta
from piece_pattern_tree import PiecePatternTree
from piece_pattern_agent import BasePiecePattern, MixedPiecePattern, LastDotSplitPiecePattern


class _Bag(object):
    def __init__(self):
        self._objs = []
        self._count = 0

    def get_inner_obj(self):
        obj = self._objs[0]
        while isinstance(obj, _Bag):
            obj = obj.objs[0]
        return obj

    def _iter_inner_objs(self, obj):
        if isinstance(obj, _Bag):
            for o in obj.iter_objs():
                yield self._iter_inner_objs(o)
        else:
            yield obj

    def iter_inner_objs(self):
        yield self._iter_inner_objs(self)

    def iter_objs(self):
        return iter(self._objs)

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
        change = False
        for obj in self._objs:
            if obj.set_pattern(pattern):
                change = True
        return change


class Combiner(object):
    def __init__(self, combine_processor, **kwargs):
        self._combine_processor = combine_processor
        self._min_combine_num = self.config.getint(
            'make', 'min_combine_num')

    @property
    def meta_info(self):
        return self._combine_processor.meta_info

    @property
    def config(self):
        return self._combine_processor.config

    def add(self, obj):
        pass

    def combine(self):
        pass


class PieceCombiner(Combiner):
    def __init__(self, combine_processor, **kwargs):
        super(PieceCombiner, self).__init__(combine_processor, **kwargs)
        self._piece_node_bag = {}

    def add(self, node):
        piece = node.piece
        if piece not in self._piece_node_bag:
            self._piece_node_bag[piece] = _Bag()
        self._piece_node_bag[piece].add(node)

    def piece_num(self):
        return len(self._piece_node_bag)

    def iter_nodes(self):
        for bag in self._piece_node_bag.itervalues():
            for node in bag.iter_inner_objs():
                yield node

    def _get_combiner_class(self):
        combine_class = LengthCombiner
        for node in self.iter_nodes():
            if node.piece_pattern.base_part_num > 1:
                combine_class = BasePatternCombiner
            return combine_class

    def combine(self):
        combiner_class = self._get_combiner_class()
        combiner = combiner_class(self._combine_processor)

        for bag in self._piece_node_bag.itervalues():
            if not self._combine_processor.keep_piece(bag):
                combiner.add_bag(bag)
        combiner.combine()


class LengthCombiner(Combiner):
    def __init__(self, combine_processor, **kwargs):
        super(LengthCombiner, self).__init__(combine_processor, **kwargs)
        self._length_bags = {}

    def add(self, piece_bag):
        length = piece_bag.get_inner_obj().piece_pattern.piece_length
        if length not in self._length_bags:
            self._length_bags[length] = _Bag()
        self._length_bags[length].add(piece_bag)

    def _set_pattern(self, length_bags, use_base=False):
        only_one = len(length_bags) == 1
        for length, bag in length_bags.iteritems():
            pattern = None
            if use_base and not only_one:
                pattern = bag.get_inner_obj().piece_pattern.base_pattern
            else:
                pattern = bag.get_inner_obj().piece_pattern.exact_num_pattern(
                    length)
            bag.set_pattern(pattern)

    def combine(self):
        if self._combine_processor.force_combine:
            self._set_pattern(self._length_bags, use_base=True)
        else:
            length_keep = {}
            length_unknow = {}
            _num = 0
            for length, bag in self._length_bags.iteritems():
                if self._combine_processor.keep_length(bag):
                    length_keep[length] = bag
                else:
                    length_unknow[length] = bag
                    _num += bag.num

            self._set_pattern(length_keep)
            if _num >= self._min_combine_num:
                self._set_pattern(length_unknow, use_base=True)


class LastDotSplitFuzzyPatternCombiner(Combiner):
    def __init__(self, combine_processor, **kwargs):
        super(LastDotSplitFuzzyPatternCombiner, self).__init__(
            combine_processor, **kwargs)
        self._combiners = {}

    def add(self, bag):
        piece_pattern = LastDotSplitPiecePattern(
            bag.get_inner_obj().piece_pattern)
        if piece_pattern.part_num <= 1:
            return
        h = hash(piece_pattern.pattern)
        if h not in self._combiners:
            self._combiners[h] = MultiLevelCombiner(
                self._combine_processor, part_num=piece_pattern.part_num,
                pp_agent_class=LastDotSplitPiecePattern)
        self._combiners[h].add_bag(bag)

    def combine(self):
        for combiner in self._combiners.itervalues():
            combiner.combine()


class MixedPatternCombiner(Combiner):
    def __init__(self, combine_processor, **kwargs):
        super(MixedPatternCombiner, self).__init__(combine_processor, **kwargs)
        self._mixed_pattern_bags = {}

    def add(self, bag):
        h = hash(bag.get_inner_obj().piece_pattern.mixed_pattern)
        if h not in self._mixed_pattern_bags:
            self._mixed_pattern_bags[h] = _Bag()
        self._mixed_pattern_bags[h].add(bag)

    def _combine_mixed_pattern(self, pattern_bag_dict):
        for pattern_bag in pattern_bag_dict.itervalues():
            self._combine_mixed_pattern_bag(pattern_bag)

    def _combine_mixed_pattern_bag(self, pattern_bag, force_combine=False):
        pp_agent_class = MixedPiecePattern
        piece_pattern = pp_agent_class(
            pattern_bag.get_inner_obj().piece_pattern)
        combiner = MultiLevelCombiner(
            self._combine_processor,
            part_num=piece_pattern.part_num, force_combine=force_combine,
            pp_agent_class=pp_agent_class)
        for piece_bag in pattern_bag.iter_objs():
            combiner.add(piece_bag)
        combiner.combine()

    def _combine_fuzzy_pattern_with_last_dot_split(self, pattern_bag_dict):
        combiner = LastDotSplitFuzzyPatternCombiner(self._combine_processor)
        for pattern_bag in pattern_bag_dict.itervalues():
            for piece_bag in pattern_bag.iter_objs():
                combiner.add(piece_bag)
        combiner.combine()

    def _combine_fuzzy_pattern(self, pattern_bag_dict):
        if self.meta_info.is_last_path_level():
            self._combine_fuzzy_pattern_with_last_dot_split(pattern_bag_dict)
        _bag = _Bag()
        for pattern_bag in pattern_bag_dict.itervalues():
            for piece_bag in pattern_bag.iter_objs():
                if piece_bag.get_inner_obj().piece_eq_pattern():
                    _bag.add(piece_bag)
        if _bag.num >= self._min_combine_num:
            _bag.set_pattern(_bag.get_inner_obj().piece_pattern.fuzzy_pattern)

    def combine(self):
        low_prob = {}
        high_prob = {}
        _num = 0
        for h, bag in self._mixed_pattern_bags.iteritems():
            if bag.num >= self._min_combine_num:
                high_prob[h] = bag
            else:
                low_prob[h] = bag
                _num += bag.num

        self._combine_mixed_pattern(high_prob)
        for h, pattern_bag in high_prob.iteritems():
            bag = _Bag()
            for piece_bag in pattern_bag.iter_objs():
                if piece_bag.get_inner_obj().piece_eq_pattern():
                    bag.add(piece_bag)
            if bag.num > 0:
                if bag.num < self._min_combine_num:
                    low_prob[h] = bag
                    _num += bag.num
                else:
                    self._combine_mixed_pattern_bag(bag, True)
        if len(low_prob) > 1 and _num >= self._min_combine_num:
            self._combine_fuzzy_pattern(low_prob)


class BasePatternCombiner(Combiner):
    def __init__(self, combine_processor, *kwargs):
        super(BasePatternCombiner, self).__init__(combine_processor, ** kwargs)
        self._base_pattern_bags = {}

    def add(self, bag):
        h = hash(bag.get_inner_obj().piece_pattern.base_pattern)
        if h not in self._base_pattern_bags:
            self._base_pattern_bags[h] = _Bag()
        self._base_pattern_bags[h].add(bag)

    def _combine_base_pattern(self, pattern_bag_dict):
        for pattern_bag in pattern_bag_dict.itervalues():
            self._combine_base_pattern_bag(pattern_bag)

    def _combine_base_pattern_bag(self, pattern_bag, force_combine=False):
        pp_agent_class = BasePiecePattern
        piece_pattern = pp_agent_class(
            pattern_bag.get_inner_obj().piece_pattern)
        combiner = MultiLevelCombiner(
            self._combine_processor,
            part_num=piece_pattern.part_num, force_combine=force_combine,
            pp_agent_class=pp_agent_class)
        for piece_bag in pattern_bag.iter_objs():
            combiner.add_bag(piece_bag)
        combiner.combine()

    def _combine_mixed_pattern(self, pattern_bag_dict):
        combiner = MixedPatternCombiner(self._combine_processor)
        for pattern_bag in pattern_bag_dict.itervalues():
            for piece_bag in pattern_bag.iter_objs():
                combiner.add(piece_bag)
        combiner.combine()

    def combine(self):
        low_prob = {}
        high_prob = {}
        _num = 0
        for h, bag in self._base_pattern_bags.iteritems():
            if bag.num >= self._min_combine_num:
                high_prob[h] = bag
            else:
                low_prob[h] = bag
                _num += bag.num
        self._combine_base_pattern(high_prob)
        for h, pattern_bag in high_prob.iteritems():
            bag = _Bag()
            for piece_bag in pattern_bag.iter_objs():
                if piece_bag.get_inner_obj().piece_eq_pattern():
                    bag.add(piece_bag)
            if bag.num > 0:
                if bag.num < self._min_combine_num:
                    low_prob[h] = bag
                    _num += bag.num
                else:
                    self._combine_base_pattern_bag(bag, True)

        if len(low_prob) > 1 and _num >= self._min_combine_num:
            self._combine_mixed_pattern(low_prob)


class MultiLevelCombiner(Combiner):
    def __init__(self, combine_processor, **kwargs):
        super(MultiLevelCombiner, self).__init__(combine_processor, **kwargs)
        self._kwargs = kwargs
        self._url_meta = URLMeta(self._kwargs.pop('part_num'), [], False)
        self._piece_pattern_tree = PiecePatternTree()
        self._piece_bags = []
        self._pp_agent_class = self._kwargs.pop('pp_agent_class')

    def add_bag(self, bag):
        self._piece_bags.append(bag)
        for node in bag.iter_objs():
            pps = self._pp_agent_class(node.piece_pattern).piece_patterns
            self._piece_pattern_tree.add_piece_patterns(
                pps, node.count, False)

    def combine(self):
        combine(self.config, self._url_meta,
                self._piece_pattern_tree, self._kwargs.get('force_combine', False))
        piece_pattern_dict = {}
        pattern_counter = {}
        for path in self._piece_pattern_tree.dump_paths():
            piece = ''.join([node.piece for node in path])
            pattern = get_pattern_from_cache(
                ''.join([str(node.pattern) for node in path]))
            piece_pattern_dict[piece] = pattern
            if pattern not in pattern_counter:
                pattern_counter[pattern] = 0
            pattern_counter[pattern] += 1
        for piece_bag in self._piece_bags:
            node = piece_bag.get_inner_obj()
            if node.piece in piece_pattern_dict:
                pattern = piece_pattern_dict[node.piece]
                if pattern in pattern_counter and pattern_counter[pattern] >= self._min_combine_num:
                    piece_bag.set_pattern(pattern)


class MetaInfo(object):
    def __init__(self, url_meta, current_level):
        self._url_meta = url_meta
        self._current_level = current_level

    @property
    def current_level(self):
        return self._current_level

    @property
    def url_meta(self):
        return self._url_meta

    def is_last_level(self):
        return self.url_meta.depth == self._current_level

    def is_last_path_level(self):
        return self.url_meta.path_depth == self._current_level

    def get_next_level_meta_info(self):
        return MetaInfo(self.url_meta, self._current_level + 1)


class CombineProcessor(object):
    def __init__(self, config, meta_info, force_combine=False):
        self._config = config
        self._min_combine_num = self.config.getint('make', 'min_combine_num')
        self._meta_info = meta_info
        self._piece_combiner = PieceCombiner(self)
        self._force_combine = force_combine
        self._pattern_cluster = None

    def iter_nodes(self):
        return self._piece_combiner.iter_nodes()

    def pattern_num(self):
        n = self._piece_combiner.piece_num()
        if n <= 1:
            return n
        pattern_set = set()
        for node in self._piece_combiner.iter_nodes():
            pattern_set.add(node.pattern)
        return len(pattern_set)

    def keep_piece(self, piece_bag):
        if self._force_combine:
            return False
        if self._pattern_cluster is None:  # preprocess
            if piece_bag.count >= self._min_combine_num:
                return True
        else:
            if self.meta_info.is_last_level():
                if piece_bag.count >= self._min_combine_num and piece_bag.num <= 1:
                    return True
            else:
                if piece_bag.count >= self._min_combine_num:
                    piece = piece_bag.get_inner_obj().piece
                    if piece not in self._pattern_cluster:
                        return True
                    else:
                        n = len(self._pattern_cluster[piece])
                        if n < self._min_combine_num:
                            return True
        return False

    def keep_length(self, length_bag):
        if self._force_combine or length_bag.num < self._min_combine_num:
            return False
        if self._pattern_cluster is None:
            return True
        else:
            if not self._pattern_cluster:
                return True
            lp = set(
                [piece_bag.get_inner_obj().pattern for piece_bag in length_bag.iter_objs()])
            pp = self._pattern_cluster[length_bag.get_inner_obj().piece]
            if pp - lp:
                return False
        return False

    @property
    def force_combine(self):
        return self._force_combine

    @property
    def meta_info(self):
        return self._meta_info

    @property
    def config(self):
        return self._config

    def add_node(self, node):
        self._piece_combiner.add(node)

    def _get_next_level_processor(self, meta_info):
        return CombineProcessor(self.config, meta_info.get_next_level_meta_info(), self._force_combine)

    def _preprocess(self):
        self._pattern_cluster = {}
        if self.meta_info.is_last_level():
            return
        self.combine(preprocess=False)
        if self.pattern_num() < self._min_combine_num:
            return
        p_processor = self
        n_processor = self._get_next_level_processor(self.meta_info)
        count = 0
        while not p_processor.meta_info.is_last_level():
            count += 1
            for node in p_processor.iter_nodes():
                for child in node.children:
                    n_processor.add_node(child)
            n_processor.combine(preprocess=False)
            if n_processor.pattern_num() <= 1 and not n_processor.meta_info.is_last_level():
                p_processor = n_processor
                n_processor = self._get_next_level_processor(
                    p_processor.meta_info)
            else:
                break

        pattern_cluster = {}
        for node in n_processor.iter_nodes():
            pattern = node.pattern
            if pattern not in pattern_cluster:
                pattern_cluster[pattern] = set()
            parrent = node.get_parrent(count)
            pattern_cluster[pattern].add(parrent.pattern)
            if parrent.piece not in self._pattern_cluster:
                self._pattern_cluster[parrent.piece] = {
                    pattern: pattern_cluster[pattern]}
            elif pattern not in self._pattern_cluster[parrent.piece]:
                self._pattern_cluster[parrent.piece][pattern] = pattern_cluster[pattern]

        for p in self._pattern_cluster:
            self._pattern_cluster[p] = set.union(
                *self._pattern_cluster[p].values())

    def combine(self, preprocess=True):
        if self._piece_combiner.piece_num() <= 1:
            return
        if preprocess:
            self._preprocess()

        self._piece_combiner.combine()

    def process(self):
        self.combine()
        if self.meta_info.is_last_level():
            return
        next_level_processors = {}
        for node in self._piece_combiner.iter_nodes():
            n_hash = hash(node.pattern)
            if n_hash not in next_level_processors:
                next_level_processors[n_hash] = self._get_next_level_processor(
                    self.meta_info)
            for child in node.children:
                next_level_processors[n_hash].add_node(child)
        for processor in next_level_processors.itervalues():
            processor.process()


def combine(config, url_meta, piece_pattern_tree, force_combine=False):
    meta_info = MetaInfo(url_meta, 0)
    processor = CombineProcessor(config, meta_info, force_combine)
    processor.add_node(piece_pattern_tree.root)
    processor.process()
