# RedisDict

A dict-like object using Redis as the backend.


## Example

```python
>>> from redisdict import RedisDict
>>> d = RedisDict('d', {'name': 'Kxrr'})
>>> d['name']
'Kxrr'


>>> import datetime
>>> from redisdict import ComplexRedisDict
>>> d2 = ComplexRedisDict('d2', {'birth': datetime.date.today()})
>>> d2['birth']
datetime.date(2016, 12, 28)
```


## TODO

- [x] Flexible redis connection settings
- [ ] More tests
- [ ] Fallback strategy when losing connection from redis 
- [ ] Python3 supporting
