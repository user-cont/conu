from __future__ import print_function, unicode_literals

FEDORA_REPOSITORY = "registry.fedoraproject.org/fedora"
FEDORA_MINIMAL_REPOSITORY = "registry.fedoraproject.org/fedora-minimal"
FEDORA_MINIMAL_REPOSITORY_TAG = "26"
FEDORA_MINIMAL_IMAGE = "{}:{}".format(FEDORA_MINIMAL_REPOSITORY, FEDORA_MINIMAL_REPOSITORY_TAG)
S2I_IMAGE = "punchbag"

THE_HELPER_IMAGE = "rudolph"
