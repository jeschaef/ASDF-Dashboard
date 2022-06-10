from flask_caching import Cache

from app.config import ProductionConfig

cache = Cache(config={
    'CACHE_TYPE': 'RedisCache',
    'CACHE_REDIS_HOST': ProductionConfig.CACHE_REDIS_HOST,
    'CACHE_REDIS_PORT': ProductionConfig.CACHE_REDIS_PORT,
    'CACHE_KEY_PREFIX': 'cache'         # prevent flushing of whole db on cache clear (e.g. celery queue)
})

