from flask_caching import Cache

cache = Cache()


def configure_cache(app):
    app.config['CACHE_TYPE'] = 'simple'
    cache.init_app(app)
