"""Base class for audio plugins"""

__author__ = "Daniel Larsson <Daniel.Larsson@servicefactory.se>"

__all__ = (
    "PLAY_STOPPED",
    "PLAY_PAUSED",
    "PLAY_RESUMED",
    "get_plugin"
    )

# Play status messages

(PLAY_STOPPED,
 PLAY_PAUSED,
 PLAY_RESUMED) = range(3)


class plugin:
    def __init__(self, player):
        self.player = player

    def stop(self):
        "Stop playing song"
        raise NotImplementedError()

    def pause(self):
        "Toggle pause state"
        raise NotImplementedError()

    def fast_forward_play(self):
        "Fast forward by skipping frames"
        raise NotImplementedError()


_plugin_registry = {}
_instance_registry = {}

def register(mime, klass):
    _plugin_registry[mime] = klass


def get_plugin(mime, player):
    "Get a plugin instance for handling 'mime' audio types"
    # We're assuming 'player' is always the same for a given
    # execution, otherwise we can return an instance created for
    # another player here. Should be a reasonable assumption though,
    # having multiple players in one application makes little sense
    instance = _instance_registry.get(mime, None)
    if not instance:
        instance = _plugin_registry[mime](player)
        _instance_registry[mime] = instance
    return instance
