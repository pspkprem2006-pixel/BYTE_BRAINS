"""Learning resource discovery package.

Layered on top of the search abstraction; provider details never leak
beyond ``app.services.search``.
"""

# Intentionally no re-exports (avoids import cycles with schemas).