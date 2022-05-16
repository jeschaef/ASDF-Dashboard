from flask_caching import Cache

cache = Cache(config={
    # 'CACHE_TYPE': 'SimpleCache'
    'CACHE_TYPE': 'RedisCache',
    'CACHE_REDIS_HOST': 'localhost',
    'CACHE_REDIS_PORT': 6379,
    'CACHE_KEY_PREFIX': 'cache'         # prevent flushing of whole db on cache clear (e.g. celery queue)
})

