import base64

from mod_manager.cache import *
from mod_manager import factorio_folder

MODPACK_TEMPLATE = "# Comments are allowed\n# Mods are listed in any order by name in mods.factorio.com url\n\n"

class ModPack(object):
    """A mod pack. Lazily loads contents when required."""

    @staticmethod
    def clean_name(name):
        """Sanitize string to be used with modpack name."""
        FORBIDDEN_CHARS = list("./\\# \t\n")
        return "".join(["_" if c in FORBIDDEN_CHARS else c for c in name])

    @classmethod
    def from_filename(cls, filename):
        """Create a ModPack object from filename."""
        return cls(os.path.basename(filename).rsplit(".", 1)[0])

    def __init__(self, name):
        self.name = ModPack.clean_name(name)
        self._lines = None

    @property
    def exists(self):
        return self.name+".txt" in os.listdir("modpacks")

    @property
    def lines(self):
        if self._lines is None:
            self._load()
        return self._lines

    @property
    def contents(self):
        """List of modpack names."""
        return [i.strip() for i in self.lines if i != "" and i[0] != "#"]

    @property
    def path(self):
        return os.path.join("modpacks", self.name+".txt")

    def _load(self):
        if self.exists:
            with open(self.path) as f:
                self._lines = [line.strip() for line in f.readlines()]
        else:
            self._lines = MODPACK_TEMPLATE.split("\n")

    def edit(self, lines):
        self._lines = lines

    def save(self):
        # This must be before open call, so file gets created with template
        data = "\n".join(self.lines)
        with open(self.path, "w") as f:
            f.write(data)

    def compress(self):
        data = "\n".join([self.name] + self.lines)
        return base64.b64encode(data.encode()).decode()

    @classmethod
    def decompress(cls, data):
        info = base64.b64decode(data.encode()).decode()
        name, contents = info.split("\n", 1)
        self = cls(name)
        self._lines = contents.split("\n")
        return self