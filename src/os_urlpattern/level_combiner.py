class LevelCombiner(object):
    def __init__(self, config, part_pattern_tree, current_level):
        self._part_pattern_tree = part_pattern_tree
        self._current_level = current_level
        self._depth = self._part_pattern_tree.depth
        self._pattern_combiners = {}
        self._keep_part_method = self.config.strategy.keep_part_method_class(
            self)

    @property
    def url_struct(self):
        return self._part_pattern_tree.url_struct

    @property
    def current_level(self):
        return self._current_level

    @property
    def last_level(self):
        return self._current_level >= self._depth

    @property
    def pattern_combiners(self):
        return self._pattern_combiners

    @property
    def next_level_combiner(self):
        return self._part_pattern_tree.level_combiners[self._current_level + 1]

    @property
    def part_pattern_tree(self):
        return self._part_pattern_tree

    def keep_part(self, pattern_combiner, nc):
        return self._keep_part_method.keep_part(pattern_combiner, nc)

    @property
    def count(self):
        return self._part_pattern_tree.count

    def add_node(self, node, is_new, count=1):
        base_pattern = node.base_pattern
        if base_pattern not in self._pattern_combiners:
            self._pattern_combiners[base_pattern] = PatternCombiner(
                self, node.base_part_pattern)
        self._pattern_combiners[base_pattern].add_node(node, is_new, count)

    def combine(self):
        change = False
        for _, pattern_combiner in self._pattern_combiners.items():
            if self.config.use_base_pattern or pattern_combiner.count <= 1 and pattern_combiner.count < self.count * self.config.rare_pattern_threshold:
                pattern_combiner.use_base_pattern()
            c = pattern_combiner.combine()
            if not change and c:
                change = c
        return change


class StepLevelCombiner(LevelCombiner):

    def complexity(self, all_count):
        if not self.last_level:
            return 0
        return 0

    def entropy(self, all_count=-1):
        if not self.last_level:
            return 0
        if all_count < self.count:
            all_count = self.count
        return sum([p.entropy(all_count) for p in self._pattern_combiners.values()])

    def add_node(self, node, is_new, count=1):
        if is_new is not None:  # None is root node, only process root node
            return
        if not self._pattern_combiners:
            pc = StepPatternCombiner(self, node.base_part_pattern)
            self._pattern_combiners[hash(pc)] = pc
        for pc in self._pattern_combiners.values():
            pc.add_node(node, is_new, count)
