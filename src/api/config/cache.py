from flask_caching import Cache

cache = Cache()


def configure_cache(app):
    config = {
        'CACHE_TYPE': 'filesystem',
        'CACHE_DEFAULT_TIMEOUT': 0,
        'CACHE_THRESHOLD': 0,
        'CACHE_DIR': '/tmp/cache'
    }
    cache.init_app(app, config)
    cache.clear()
