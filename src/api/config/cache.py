from flask import Flask
from flask_caching import Cache

from definitions import VOLUME_PATH

cache = Cache()


def configure_cache(app: Flask) -> None:
    config = {
        'CACHE_TYPE': 'FileSystemCache',
        'CACHE_DEFAULT_TIMEOUT': 0,
        'CACHE_THRESHOLD': 0,
        'CACHE_DIR': f'{VOLUME_PATH}/tmp/cache'
    }
    cache.init_app(app, config)
    cache.clear()
