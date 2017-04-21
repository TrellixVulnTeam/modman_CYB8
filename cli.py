#!python3

import os
import sys
import subprocess

import mod_manager

def open_gui_editor(filename):
    """Opens default GUI text editor."""
    if sys.platform == "win32":
        os.startfile(filename)
    elif sys.platform.startswith("darwin"):
        try:
            subprocess.call(["open", filename])
        except FileNotFoundError:
            print("Your default editor \"{}\" could not be opened.")
            print("You can manually open \"{}\" if you want to edit it.".format(filename))
    elif sys.platform.startswith("linux"):
        try:
            subprocess.call(["xdg-open", filename])
        except FileNotFoundError:
            print("Your default editor \"{}\" could not be opened.")
            print("You can manually open \"{}\" if you want to edit it.".format(filename))
    else:
        print("Could not determine text editor.")
        print("You can manually open \"{}\" if you want to edit it.".format(filename))

def open_editor(filename):
    """Opens default text editor, preferring CLI editors to GUI editors."""
    if sys.platform.startswith("win32"):
        open_gui_editor(filename)
    elif sys.platform.startswith("darwin") or sys.platform.startswith("linux"):
        default_editor = os.environ.get("EDITOR", None)
        if default_editor:
            try:
                subprocess.call([default_editor, filename])
            except FileNotFoundError:
                # could not use default editor
                print("Your default editor \"{}\" could not be opened.")
                print("You can manually open \"{}\" if you want to edit it.".format(filename))
        else:
            open_gui_editor(filename)


class CLI(object):
    ACTIONS = [
        "help [action]",
        "list [package]",
        "edit <packname>",
        "compress <packname>",
        "decompress <base64>",
        "install <packname>",
        "match <server_address>",
        "search <query>"
    ]

    HELP = {
        "help": "If action is present, prints detailed information of the action, otherwise this help message is printed",
        "list": "Lists all installed packages",
        "edit": "Opens the specified pack in default text editor",
        "compress": "Makes a base64 digest of the mentioned modpack",
        "decompress": "Unpacks a mod from base64 digest (overrides existing modpacks with the same name)",
        "install": "Despite what is in the mod folder, downloads the newest mods into the specified folder",
        "match": "Match your mod configuration to one in a server, using exactly same versions",
        "search": "Search for mods from the Factorio mod portal"
    }

    ACTION_NAMES = [a.split()[0] for a in ACTIONS]

    def __init__(self):
        self.mod_manager = mod_manager.ModManager()

    def cmd_help(self, args):
        if args == []:
            print("")
            print("Usage: ./{} [action] [args]".format(sys.argv[0]))
            print("")
            maxlen = max(map(len, self.ACTIONS))
            for action in self.ACTIONS:
                print("  "+action+" "*(maxlen-len(action)+2)+self.HELP[action.split()[0]])
            print("")
        elif args[0] in self.ACTION_NAMES:
            print(args[0]+":  "+self.HELP[args[0].split()[0]])
        else:
            print("Invalid action \"{}\"").format(action)
            exit(1)

    def cmd_list(self, args):
        if args == []:
            for p in self.mod_manager.modpacks:
                print(p.name)
        else:
            packs = {p.name: p for p in self.mod_manager.modpacks}
            for arg in args:
                if arg in packs:
                    pack = packs[arg]
                    print(pack.name)
                    if pack.contents == []:
                        print("  (no mods)")
                    else:
                        for mod in pack.contents:
                            print(" "*2 + mod)
                else:
                    print("Mod pack \"{}\" does not exist.".format(pack.name))
                    exit(1)

    def cmd_edit(self, args):
        if len(args) != 1:
            print("Invalid argument count")
            exit(1)

        mp = self.mod_manager.get_pack(args[0])
        open_editor(mp.path)

    def cmd_compress(self, args):
        if len(args) != 1:
            print("Invalid argument count")
            exit(1)

        mp = self.mod_manager.get_pack(args[0])
        if mp.exists:
            print(mp.compress())
        else:
            print("Mod pack \"{}\" does not exist.".format(args[0]))
            exit(1)


    def cmd_decompress(self, args):
        if len(args) != 1:
            print("Invalid argument count")
            exit(1)

        self.mod_manager.ModPack.decompress(args[0]).save()

    def cmd_install(self, args):
        if args:
            for p in args:
                mp = self.mod_manager.get_pack(p)
                if mp.exists:
                    print("Installing modpack: "+mp.name)
                    for msg in self.mod_manager.install_pack(mp):
                        print(msg, end="")
                        sys.stdout.flush()
                else:
                    print("Mod pack \"{}\" does not exist.".format(p))
                    exit(1)
        else:
            print("Invalid argument count")
            exit(1)

    def cmd_match(self, args):
        if len(args) != 1:
            print("Invalid argument count")
            exit(1)

        try:
            for msg in self.mod_manager.install_matching(args[0]):
                print(msg, end="")
                sys.stdout.flush()
        except ConnectionRefusedError:
            print("Could not connect to the server. Is it running?")
            exit(1)
        except RuntimeError as e:
            print("Could not communicate with the server. Are you using same Factorio version?")
            exit(1)

    def cmd_search(self, args):
        results = self.mod_manager.mod_portal.search(" ".join(args))

        for i,s in enumerate(results):
            print("{}. {}: {} ({} downloads)".format(i+1, s.name, s.title, s.downloads))

    def run(self, cmd):
        if cmd == []:
            cmd = ["help"]

        if cmd[0] in self.ACTION_NAMES:
            try:
                # get function in this folder named "cmd_<action>"
                fn = getattr(self, "cmd_"+cmd[0])
            except AttributeError:
                print("Action not implemented yet.")
                exit(1)

            fn(cmd[1:])
        else:
            print("Invalid action \"{}\"").format(cmd[0])
            exit(1)


def main():
    CLI().run(sys.argv[1:])

if __name__ == '__main__':
    main()