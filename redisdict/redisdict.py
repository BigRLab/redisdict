#!/usr/bin/env python
# encoding: utf-8
from __future__ import absolute_import

import cPickle
from collections import Mapping, defaultdict


from . import logger
from .utils import connect_redis, mutex
from .exceptions import SerialisationError


class SimpleRedisDict(Mapping):
    def __init__(self, name, dct, uri='redis://127.0.0.1:6379/0', **kwargs):
        """
        :param name: Name to specific this object in Redis.
        :param dct: The dict will map to Redis.
        :type dct: dict
        :param uri: Redis uri.

        :param autoclean: If sets to False, will keep the existing key in redis hash, then mapping the others.
                          If sets to True, with delete the old redis hash first, then start mapping.
                          Default is **True** .

        """
        self.name = name

        self._name = self.generate_key_name(self.name)
        self._dct = dct.copy()
        self._conn = connect_redis(uri)
        self._default_key = self.generate_key_name('default')

        self.resolve_options(kwargs)

        for key, value in self._dct.items():
            self.setitem(key, value, force=False)

        if isinstance(self._dct, defaultdict):
            self.setitem(self._default_key, self._dct.default_factory())

        self.after_init()

    def after_init(self):
        pass

    def resolve_options(self, options):
        autoclean = options.pop('autoclean', True)
        if autoclean:
            self.clear()

    @classmethod
    def generate_key_name(cls, name):
        prefix = cls.__name__ + ':'
        return '{0}{1}'.format(prefix, name)

    @classmethod
    def dumps(cls, obj):
        if obj is None:
            raise SerialisationError('NoneType is not supported in {}'.format(cls.__name__))
        if not isinstance(obj, basestring):
            logger.warning("{0} => {1} will be converting to <type 'str'>".format(obj, type(obj)))
        return str(obj)

    @classmethod
    def loads(cls, b):
        return b

    def setitem(self, key, value, force=False):
        if (key not in self) or force:
            return bool(self._conn.hset(self._name, key, self.dumps(value)))
        return False

    def getitem(self, key):
        value = self._conn.hget(self._name, key=key)
        return self.loads(value)

    def clear(self):
        """
        Delete this object in Redis.
        """
        return self._conn.delete(self._name)

    def __getitem__(self, key):
        return self.getitem(key) or self.get(self._default_key)

    def __setitem__(self, key, value):
        return self.setitem(key, value, force=True)

    def __delitem__(self, key):
        return self._conn.hdel(self._name, key)

    def __len__(self):
        return self._conn.hlen(self._name)

    def __iter__(self):
        return (key for key in self._conn.hkeys(self._name) if key != self._default_key)

    def __contains__(self, item):
        return self._conn.hexists(self._name, item)

    def Lock(self, expire):
        """
        :type expire: int
        """
        name = '_LOCK_{0}'.format(self._name)
        return mutex(self._conn, name, expire)

    def __str__(self):
        return '<{0}>'.format(self._name)


class ComplexRedisDict(SimpleRedisDict):

    @classmethod
    def dumps(cls, obj):
        return cPickle.dumps(obj)

    @classmethod
    def loads(cls, b):
        return cPickle.loads(b)


RedisDict = SimpleRedisDict