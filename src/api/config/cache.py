from atexit import register

from flask import Flask
from flask_caching import Cache

cache = Cache()


def configure_cache(app: Flask) -> None:
    config = {
        "CACHE_TYPE": "FileSystemCache",
        "CACHE_DIR": "/tmp/cache"
    }
    cache.init_app(app, config)
    register(cache.clear)
