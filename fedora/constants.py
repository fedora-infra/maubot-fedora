import re

NL = "      \n"
ALIASES: dict[str, list[str]] = {}
MATRIX_USER_RE = re.compile(r"@([^:]+):([^\s]+)")
COMMAND_RE = re.compile(r"^!(\S+)(?:\s+|$)(.*)")
# Domains where we can safely use the username as a FAS user
FAS_MATRIX_DOMAINS = ["fedora.im"]
