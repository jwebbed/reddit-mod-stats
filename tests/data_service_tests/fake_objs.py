class FakeMod:
    def __init__(self, mod):
        self.name = mod

class FakeRedditQuery:
    def __init__(self, name, subscribers, nsfw=False, moderators=[]):
        self.display_name = name
        self.subscribers = subscribers
        self.over18 = nsfw
        self.moderator = [FakeMod(m) for m in moderators]

    def add_mod(self, name):
        self.moderator.append(FakeMod(name))

    def remove_mod(self, name):
        for mod in self.moderator:
            if mod.name == name:
                self.moderator.remove(mod)
                break
