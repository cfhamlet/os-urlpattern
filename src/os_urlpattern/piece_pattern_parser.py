import StringIO
from definition import BasePatternRule, CHAR_RULE_DICT, SIGN_RULE_SET, \
    BASE_ASCII_RULE_SET, DIGIT_AND_ASCII_RULE_SET
from piece_pattern import PiecePattern, MultiPiecePattern, EMPTY_PIECE_PATTERN
from pattern import get_pattern_from_cache


class PiecePatternParser(object):
    def __init__(self, config):
        self._reserved_ext_names =  set(config.getlist('make', 'reserved_ext_names'))
        self._merge_multi_piece_threshold = config.getint('make', 'merge_multi_piece_threshold')
        self._reset()

    def _reset(self):
        self._last_char = None
        self._rule_list = []
        self._piece_list = []
        self._last_dot_pos = -1024

    def parse(self, string, last_dot_split=False):
        self._reset()
        self._pre_process(string)
        return self._get_piece_pattern(last_dot_split)

    def _pre_process(self, string):
        for c in string:
            self._define(c)

    def _define(self, char):
        last_rule = self._rule_list[-1] if self._rule_list else None
        rule = CHAR_RULE_DICT[char]

        if last_rule != rule:
            if last_rule not in BASE_ASCII_RULE_SET or rule not in BASE_ASCII_RULE_SET:
                self._piece_list.append(StringIO.StringIO())
                self._rule_list.append(rule)
            elif last_rule != BasePatternRule.BASE_ASCII:
                self._rule_list.pop()
                self._rule_list.append(BasePatternRule.BASE_ASCII)
        self._piece_list[-1].write(char)

    def _exact_num(self, rule, num):
        if num == 1:
            return '[%s]' % rule
        return '[%s]{%d}' % (rule, num)

    def _normalize(self, letter, rule):
        if rule in SIGN_RULE_SET:
            l = len(letter)
            return self._exact_num(rule, l)
        return letter

    def _should_split_by_last_dot(self):
        parts_num = len(self._rule_list)
        if self._last_dot_pos > parts_num - 3 and self._last_dot_pos < parts_num - 1:
            return True
        return False

    def _update_info(self, last_dot_split):
        part_num = len(self._rule_list)
        for ridx, buf in enumerate(self._piece_list[::-1]):
            idx = part_num - ridx - 1
            buf.seek(0)
            letter = buf.read()
            self._piece_list[idx] = self._normalize(
                letter, self._rule_list[idx])
            if last_dot_split and self._last_dot_pos < 0 and \
                    self._rule_list[idx] == BasePatternRule.DOT:
                self._last_dot_pos = idx

        if self._should_split_by_last_dot():
            ext_name = "".join(self._piece_list[self._last_dot_pos + 1:])
            if ext_name in self._reserved_ext_names:
                del self._piece_list[self._last_dot_pos + 1:]
                del self._rule_list[self._last_dot_pos + 1:]
                self._piece_list.append(ext_name)
                self._rule_list.append(ext_name)

    def _get_piece_pattern(self, last_dot_split):
        if len(self._piece_list) <= 0:
            return EMPTY_PIECE_PATTERN
        self._update_info(last_dot_split)
        return self._create_piece_pattern()

    def _p_one_or_more(self, rule):
        return get_pattern_from_cache('[%s]+' % rule)

    def _p_merge_rules(self, rules):
        rules = sorted(rules)
        return self._p_one_or_more(''.join(rules))

    def _process(self, piece_list, rule_list):
        part_num = len(piece_list)
        if part_num == 1:
            return PiecePattern(piece_list[0], self._p_one_or_more(rule_list[0]))
        rule_set = set(rule_list)
        if BasePatternRule.BASE_ASCII in rule_set:
            rule_set.update(BASE_ASCII_RULE_SET)
            rule_set.discard(BasePatternRule.BASE_ASCII)
        if part_num > self._merge_multi_piece_threshold:
            return PiecePattern(''.join(piece_list), self._p_merge_rules(rule_set))

        if not rule_set.intersection(DIGIT_AND_ASCII_RULE_SET):
            return PiecePattern(''.join(piece_list), self._p_merge_rules(rule_set))

        return MultiPiecePattern([PiecePattern(part, self._p_one_or_more(pattern_str))
                                  for part, pattern_str in zip(piece_list, rule_list)])

    def _create_piece_pattern(self):
        def _ext_pattern(piece, pattern_string):
            if pattern_string == BasePatternRule.DOT:
                return self._p_one_or_more(pattern_string)
            return get_pattern_from_cache(pattern_string)

        if self._should_split_by_last_dot():
            pos = self._last_dot_pos
            bpp = self._process(
                self._piece_list[0:pos], self._rule_list[0:pos])
            fpp = MultiPiecePattern([PiecePattern(piece, _ext_pattern(piece, pattern_str))
                                     for piece, pattern_str in zip(self._piece_list[pos:],
                                                                   self._rule_list[pos:])])
            return MultiPiecePattern([bpp, fpp])
        else:
            return self._process(self._piece_list, self._rule_list)
