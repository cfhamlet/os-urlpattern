from lib.matcher import Matcher
import sys
import urlparse
import logging
import time
logging.basicConfig(level='DEBUG', format='%(asctime)s [%(name)s] [%(levelname)s] %(message)s', datefmt='[%Y-%m-%d %H:%M:%S]',)
_logger = logging.getLogger('Match')

pattern_file = sys.argv[1]

matcher = Matcher()
_logger.debug('[LOAD] START')
matcher.load(open(pattern_file))
_logger.debug('[LOAD] FINISH %d' % matcher.count)

start_time = time.time()
count = 0
match_count = 0
for line in sys.stdin:
    if count % 5000 == 0:
        now = time.time()
        _logger.debug('[MATCHING] %d %.1f/s' % (count, count / (now - start_time)))
    count += 1
    url = line.strip()
    pat_info = matcher.match(url)
    pid = None
    if pat_info:
        pid = pat_info['pid']
        match_count += 1
    print "\t".join((str(pid), url))

m_percent = float(match_count) / count * 100 if count > 0 else 0
now = time.time()
_logger.debug('[MATCH] FINISH ALL:%d MATCH:%d %.2f%% %.1f/s' % (count, match_count, m_percent, count / (now - start_time)))
