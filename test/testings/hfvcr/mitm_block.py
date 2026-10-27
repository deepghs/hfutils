"""
mitmproxy add-on that refuses every request. Used for a replay that has nothing recorded.

mitmproxy only kills an unknown request while there is at least one recorded flow (``server_replay_extra=kill``): with an empty
list it lets everything through to the real server, which would break the promise that replaying never leaves the machine.
"""


# mitmproxy registers an add-on under its lower-cased class name: a plain 'Block' collides with its own 'block' add-on
class HfvcrRefuseAll:
    def request(self, flow):
        flow.kill()


addons = [HfvcrRefuseAll()]
