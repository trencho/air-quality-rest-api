"""The shared cache instance, owned by no layer.

`processing` and `preparation` memoize expensive reads, and the object they memoize with used to
live in `api/config/cache.py`. That made the two non-HTTP layers import the HTTP layer, and the
cost was concrete: importing anything under `modeling` or `processing` on its own pulled in the
whole Flask app and died on a circular import, so the training code could not be exercised or
tested without booting the service.

The Flask wiring (`init_cache`, the Redis-or-filesystem choice, the atexit hook) stays in
`api/config/cache.py`, which is where it belongs. Only the instance lives here, above every layer
that needs it.
"""

from flask_caching import Cache

cache = Cache()
