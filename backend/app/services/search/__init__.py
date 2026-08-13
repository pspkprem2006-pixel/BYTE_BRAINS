"""Web search package: provider abstraction, Brave provider, search service."""

# Intentionally no re-exports: importing this package must not pull in the
# service layer before schemas are initialized (avoids import cycles).
