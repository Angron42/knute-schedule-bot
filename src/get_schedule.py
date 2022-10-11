import os
import logging
import requests.exceptions

from requests import Response
from urllib.parse import urljoin
from datetime import datetime, timedelta
from requests_cache import CachedSession



logger = logging.getLogger()
session = CachedSession(
    'cache/schedule',
    cache_control=True,
    expire_after=timedelta(days=1),
    allowable_methods=['POST'],
    match_headers=True,
    stale_if_error=True
)



def get_schedule(group_id: int, date = datetime.today()) -> Response:
    logger.debug('Getting schedule for group {0}'.format(group_id))

    week_start = date - timedelta(days=date.weekday())
    week_end = week_start + timedelta(days=6)

    req_data = {
        'groupId': group_id,
        'dateStart': week_start.strftime('%Y-%m-%d'),
        'dateEnd': week_end.strftime('%Y-%m-%d')
    }

    headers = {
        'Accept-Language': 'uk',
        'Content-Type': 'application/json; charset=utf-8'
    }

    logger.debug('Getting schedule with data %s' % req_data)
    url = urljoin(os.getenv('API_URL'), '/time-table/group')
    timeout = int(os.getenv('API_REQUEST_TIMEOUT'))
    res = session.post(url, json=req_data, headers=headers, timeout=timeout)

    if not res.ok:
        raise requests.exceptions.HTTPError()

    return res
