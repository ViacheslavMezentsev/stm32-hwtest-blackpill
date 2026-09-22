"""Minimal single-board hardware testing support."""


def case(identifier, *, timeout_s=20, labels=()):
    """Metadata is read statically by the host; GDB imports the function unchanged."""
    def decorate(function):
        return function
    return decorate
