# -*- coding: utf-8 -*-

from __future__ import absolute_import

import json
import random
import sys
import hashlib
import os
import re

if sys.version_info[0] == 2:
    PY3 = False
    from urllib import urlencode
    from httplib import HTTPConnection

elif sys.version_info[0] == 3:
    PY3 = True
    from urllib.parse import urlencode
    from http.client import HTTPConnection

DEFAULT_TIMEOUT = 10
DEFAULT_CLUSTER = "default"

TOS_API_SERVICE_NAME = "toutiao.tos.tosapi"
TOS_ACCESS_HEADER = "x-tos-access"
TOS_MD5_HEADER = "x-tos-md5"
TOS_REQ_ID_HEADER = "x-tos-request-id"



class TosException(Exception):
    def __init__(self, code, msg, request_id, remote_addr):
        self.code = code
        self.msg = msg
        self.request_id = request_id or "-"
        self.remote_addr = remote_addr or "-"
        Exception.__init__(self, "%s:%s:%s:%s" % (self.code, self.msg, self.request_id, self.remote_addr))


key_re = re.compile("^[-./a-zA-Z0-9_]+$")


def assert_validate_key(k):
    if not k or k.startswith("/") or k.endswith("/") or not key_re.match(k):
        raise ValueError("invalid key: %s" % k)


def _rid(headers):
    return headers.get(TOS_REQ_ID_HEADER) or "-"


def parse_date(ims):
    if not ims:
        return 0
    import time
    from email.utils import parsedate_tz
    """ Parse rfc1123, rfc850 and asctime timestamps and return UTC epoch. """
    try:
        ts = parsedate_tz(ims)
        return int(time.mktime(ts[:8] + (0, )) - (ts[9] or 0) - time.timezone)
    except (TypeError, ValueError, IndexError, OverflowError):
        return 0


def md5data(data):
    assert isinstance(data, bytes), type(data)
    return hashlib.md5(data).hexdigest()


class TosClient(object):
    # cluster timeout
    def __init__(self, bucket, accessKey, **kwargs):
        self.bucket = bucket
        self.access_key = accessKey
        self.timeout = kwargs.get("timeout", DEFAULT_TIMEOUT)
        self.cluster = kwargs.get("cluster", DEFAULT_CLUSTER)
        self.service_name = kwargs.get("service", TOS_API_SERVICE_NAME)
        self.addrs = kwargs.get("addrs")

    def _get_addr(self):
        if self.addrs:
            return random.choice(self.addrs)

        _test_addr = os.environ.get("TEST_TOSAPI_ADDR")
        if _test_addr:
            host_port = _test_addr.split(":")
            return (host_port[0], int(host_port[1]))

        from pytos import consul
        try:
            addr = consul.getone(self.service_name, cluster=self.cluster)
        except Exception as e:
            print(e)
        else:
            return (addr[0], addr[1])

        from .consul import consul_translate
        ins = consul_translate(self.service_name)
        addrs = [v for v in ins if v["Tags"].get("cluster") == self.cluster]
        addr = random.choice(addrs)
        return (addr.get("Host", ""), int(addr.get("Port", 0)))

    def _get_conn(self):
        addr = self._get_addr()
        return HTTPConnection(addr[0], addr[1], timeout=self.timeout)

    def _uri(self, key, **kwargs):
        param = {"timeout": self.timeout}
        param.update(kwargs)
        return "/%s/%s?%s" % (self.bucket, key, urlencode(param))

    def _encode_utf8(self, data):
        if isinstance(data, unicode):
            data = data.encode('utf-8')
        return data

    def _req(self, method, url, body=None, headers=None):
        assert not body or isinstance(body, bytes), "body type: %s" % type(body)
        _headers = {TOS_ACCESS_HEADER: self.access_key}
        if headers:
            _headers.update(headers)

        if PY3 == False:
            url = self._encode_utf8(url)
            body = self._encode_utf8(body)
            for k, v in _headers.iteritems():
                k = self._encode_utf8(k)
                v = self._encode_utf8(v)

        conn = self._get_conn()
        conn.request(method, url, body, _headers)
        response = conn.getresponse()
        status = response.status
        data = response.read()
        conn.close()
        remote_addr = "%s:%d" % (conn.host, conn.port)
        headers = response.getheaders()
        if PY3:
            headers = [(k.lower(), v) for k, v in headers]
        return status, data, dict(headers), remote_addr

    def put_object(self, key, data):
        assert_validate_key(key)
        assert data, "data zero len"
        uri = self._uri(key)
        md5Hash = md5data(data)
        status, data, headers, addr = self._req("PUT", uri, data, None)
        if status != 200:
            raise TosException(status, data.decode("utf8"), _rid(headers), addr)
        if headers.get(TOS_MD5_HEADER) != md5Hash:
            raise TosException(40001, "expect:%s; actual:%s" % (md5Hash, headers.get(TOS_MD5_HEADER)),
                               _rid(headers), addr)

    def get_object(self, key, withheaders=False):
        uri = self._uri(key)
        status, data, headers, addr = self._req("GET", uri)
        if status == 404:
            raise TosException(404, "Not Found", _rid(headers), addr)
        if status != 200:
            raise TosException(status, data.decode("utf-8"), _rid(headers), addr)
        if withheaders:
            return data, headers
        return data

    def head_object(self, key):
        uri = self._uri(key)
        status, data, headers, addr = self._req("HEAD", uri)
        if status == 404:
            return None
        if status != 200:
            raise TosException(status, data.decode("utf8"), _rid(headers), addr)
        ret = {}
        ret["size"] = int(headers.get("content-length"))
        ret["time"] = parse_date(headers.get("last-modified"))
        return ret

    def delete_object(self, key):
        uri = self._uri(key)
        status, data, headers, addr = self._req("DELETE", uri)
        if status in (404, 410):
            raise TosException(404, "Not Found", _rid(headers), addr)
        if status != 204:
            raise TosException(status, data.decode("utf8"), _rid(headers), addr)
        return True

    def init_upload(self, key):
        uri = self._uri(key, uploads="")
        status, data, headers, addr = self._req("POST", uri)
        if status != 200:
            raise TosException(status, data.decode("utf8"), _rid(headers), addr)
        data = json.loads(data.decode("utf8"))
        return data["payload"]["uploadID"]

    def upload_part(self, key, upload_id, part_number, body):
        md5Hash = md5data(body)
        uri = self._uri(key, partNumber=part_number, uploadID=upload_id)
        status, data, headers, addr = self._req("PUT", uri, body=body)
        if status != 200:
            raise TosException(status, data.decode("utf8"), _rid(headers), addr)
        if headers.get(TOS_MD5_HEADER) != md5Hash:
            raise TosException(40001, "expect:%s; actual:%s" % (md5Hash, headers.get(TOS_MD5_HEADER)),
                               _rid(headers), addr)

    def complete_upload(self, key, upload_id, part_list):
        uri = self._uri(key, uploadID=upload_id)
        body = ",".join(part_list).encode("utf-8")
        status, data, headers, addr = self._req("POST", uri, body=body)
        if status != 200:
            raise TosException(status, data.decode("utf8"), _rid(headers), addr)
        return None

    def list_prefix(self, prefix, delimiter, start_after, max_keys, witheaders=False):
        uri = self._uri("", **{"prefix":prefix, "delimiter":delimiter, "start-after":start_after, "max-keys":max_keys})
        status, data, headers, addr = self._req("GET", uri)

        if status != 200:
            raise TosException(status, data.decode("utf8"), _rid(headers), addr)

        if witheaders:
            return data, headers

        return data

_test_client = TosClient("tostest", "BG8DFYMLM6U44P9KX755", cluster="default", timeout=2)
