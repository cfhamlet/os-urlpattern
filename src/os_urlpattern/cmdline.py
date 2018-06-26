from __future__ import print_function

import argparse
import logging
import sys
import time
from collections import Counter
from logging.config import dictConfig

from .compat import binary_stdin, binary_stdout
from .config import get_default_config
from .definition import DEFAULT_ENCODING
from .exceptions import (InvalidCharException, InvalidPatternException,
                         IrregularURLException)
from .formatter import FORMATTERS
from .pattern_maker import PatternMaker
from .pattern_matcher import PatternMatcher
from .utils import LogSpeedAdapter, pretty_counter, MemoryUsageFormatter


def _config_logging(log_level):
    dictConfig(_DEFAULT_LOGGING)
    if log_level == 'NOTSET':
        handler = logging.NullHandler()
    else:
        handler = logging.StreamHandler()
    formatter = MemoryUsageFormatter(
        fmt='[%(asctime)s] [%(name)s] [%(levelname)s] [%(memory)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    logging.root.setLevel(logging.NOTSET)
    handler.setFormatter(formatter)
    handler.setLevel(log_level)
    logging.root.addHandler(handler)


class Command(object):
    def __init__(self, config=None):
        self._config = config
        self._logger = logging.getLogger(self.__class__.__name__)

    def add_argument(self, parser):

        parser.add_argument('-f', '--file',
                            help='file to be processed (default: stdin)',
                            nargs='+',
                            type=argparse.FileType('rb'),
                            default=[binary_stdin],
                            dest='file')

        parser.add_argument('-L', '--loglevel',
                            help='log level (default: NOTSET)',
                            default='NOTSET',
                            action='store',
                            dest='log_level',
                            choices=['NOTSET', 'DEBUG', 'INFO',
                                     'WARN', 'ERROR', 'FATAL'],
                            type=lambda s: s.upper())

    def process_args(self, args):
        _config_logging(args.log_level)

    def run(self, args):
        raise NotImplementedError


class MakePatternCommand(Command):

    def process_args(self, args):
        super(MakePatternCommand, self).process_args(args)
        if args.config:
            self._config.readfp(args.config[0])

    def add_argument(self, parser):
        super(MakePatternCommand, self).add_argument(parser)
        parser.add_argument('-c', '--config',
                            help='config file',
                            nargs='+',
                            type=argparse.FileType('r'),
                            action='store',
                            dest='config')

        parser.add_argument('-F', '--formatter',
                            help='output formatter (default: CLUSTER)',
                            default='CLUSTER',
                            action='store',
                            dest='formatter',
                            choices=FORMATTERS.keys(),
                            type=lambda s: s.upper())

    def _load(self, pattern_maker, args):
        stats = Counter()
        speed_logger = LogSpeedAdapter(self._logger, 5000)
        for url in args.file[0]:
            stats['ALL'] += 1
            url = url.strip()
            if not url:
                stats['EMPTY'] += 1
                continue
            speed_logger.debug('[LOADING]')
            try:
                url = url.decode(DEFAULT_ENCODING)
                _, is_new = pattern_maker.load(url)
                if is_new:
                    stats['UNIQ'] += 1
                stats['VALID'] += 1
            except (InvalidPatternException,
                    IrregularURLException,
                    InvalidCharException,
                    UnicodeDecodeError,
                    ValueError) as e:
                self._logger.warn('%s, %s', str(e), url)
                stats['INVALID'] += 1
                continue
            except Exception as e:
                self._logger.error('%s, %s', str(e), url)
                stats['INVALID'] += 1
                continue
        self._logger.debug('[LOADED] %s', pretty_counter(stats))

    def _process(self, pattern_maker, args):
        formatter = FORMATTERS[args.formatter]()
        s = time.time()
        combine = args.formatter == 'ETE'
        for maker in pattern_maker.makers:
            for url_meta, root in maker.make(combine):
                e = time.time()
                self._logger.debug('[CLUSTER] %d %.2fs', root.count, e - s)
                for record in formatter.format(url_meta, root):
                    print(record)
                s = time.time()

    def _confirm_config(self, args):
        if args.formatter != 'CLUSTER':
            self._config.set('make', 'drop_url', 'true')
        self._config.freeze()

    def run(self, args):
        self._confirm_config(args)
        pattern_maker = PatternMaker(self._config)
        self._load(pattern_maker, args)
        self._process(pattern_maker, args)


class MatchPatternCommand(Command):
    def __init__(self):
        super(MatchPatternCommand, self).__init__()

    def add_argument(self, parser):
        super(MatchPatternCommand, self).add_argument(parser)
        parser.add_argument('-p', '--pattern-file',
                            help='pattern file to be loaded',
                            nargs='+',
                            type=argparse.FileType('rb'),
                            required=True,
                            action='store',
                            dest='pattern_file')

        parser.add_argument('-a', '--all_matched',
                            help='all matched patterns',
                            default=False,
                            action='store_true',
                            dest='all_matched')

    def _load(self, pattern_matcher, args):
        stats = Counter()
        io_input = args.pattern_file[0]
        self._logger.debug('[LOAD] Start %s', io_input.name)
        speed_logger = LogSpeedAdapter(self._logger, 1000)
        for line in io_input:
            speed_logger.debug('[LOADING]')
            stats['ALL'] += 1
            pattern = line.rstrip()
            if not pattern.startswith(b'/'):
                stats['UNKNOW'] += 1
                continue
            try:
                pattern = pattern.decode(DEFAULT_ENCODING)
                pattern_matcher.load(pattern, meta=pattern)
                stats['VALID'] += 1
            except Exception as e:
                self._logger.warn("%s, %s", str(e), line)
                stats['INVALID'] += 1
        self._logger.debug('[LOAD] Finished %s', pretty_counter(stats))

        self._logger.debug('[PREPROCESS] Start')
        pattern_matcher.preprocess()
        self._logger.debug('[PREPROCESS] Finished')

    def _match_result(self, pattern_matcher, raw_url, args):
        result = None
        try:
            url = raw_url.decode(DEFAULT_ENCODING)
            result = pattern_matcher.match(url)
            if not args.all_matched:
                result = sorted(result, reverse=True)
                result = result[:1]
            result = u'\t'.join([r.meta for r in result]
                                ).encode(DEFAULT_ENCODING)
        except (InvalidPatternException,
                IrregularURLException,
                InvalidCharException,
                UnicodeDecodeError,
                ValueError) as e:
            result = b'E'
            self._logger.warn("%s, %s", str(e), raw_url)
        except Exception as e:
            result = b'E'
            self._logger.error("%s, %s", str(e), raw_url)
        return result

    def _match(self, pattern_matcher, args):
        speed_logger = LogSpeedAdapter(self._logger, 5000)
        for line in args.file[0]:
            speed_logger.debug('[MATCHING]')
            line = line.strip()
            result = self._match_result(pattern_matcher, line, args)
            if not result:
                result = b'N'
            binary_stdout.write(result)
            binary_stdout.write(b'\t')
            binary_stdout.write(line)
            binary_stdout.write(b'\n')

    def run(self, args):
        pattern_matcher = PatternMatcher()
        self._load(pattern_matcher, args)
        self._match(pattern_matcher, args)


_DEFAULT_LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'incremental': True,
}


def _execute(command, argv=None):
    argv = argv or sys.argv
    parser = argparse.ArgumentParser()
    command.add_argument(parser)
    args = parser.parse_args(argv[1:])
    command.process_args(args)
    command.run(args)


def make(argv=None):
    _execute(MakePatternCommand(get_default_config()), argv)


def match(argv=None):
    _execute(MatchPatternCommand(), argv)
