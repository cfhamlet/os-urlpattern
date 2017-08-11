from __future__ import print_function
import sys
import os
import argparse
import logging
import sys
import json
from logging.config import dictConfig


def _config_logging(log_level):
    dictConfig(_DEFAULT_LOGGING)
    if log_level == 'NOTSET':
        handler = logging.NullHandler()
    else:
        handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    logging.root.setLevel(logging.NOTSET)
    handler.setFormatter(formatter)
    handler.setLevel(log_level)
    logging.root.addHandler(handler)


class Command(object):
    def add_argument(self, parser):
        parser.add_argument('-c', '--config',
                            help='config file',
                            action='store',
                            dest='config')

        parser.add_argument('-f', '--file',
                            help='file to be processed (default: stdin)',
                            action='store',
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
        pass


class PatternMaker(Command):

    def run(self, args):
        input = sys.stdin
        if args.file and os.path.exists(args.file):
            input = open(args.file, 'r')
        else:
            raise ValueError, 'File not exist: %s' % args.file
        from generator import UrlPatternGenerator
        generator = UrlPatternGenerator()
        generator.load(input)
        for pattern_path in generator.process_and_dump():
            pat_info = {'pid': pattern_path.pattern_path_hashcode,
                        'pat': str(pattern_path),
                        'count': pattern_path.count}
            print(json.dumps(pat_info))


class PatternMatcher(Command):
    pass


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
    _execute(PatternMaker(), argv)


def match(argv=None):
    _execute(PatternMatcher(), argv)
