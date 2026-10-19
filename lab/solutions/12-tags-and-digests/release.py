"""Release records.

After the pipeline pushes an image, it calls pin() and stores the result as this release's
image. A rollback runs exactly what was stored. Only change pin().
"""

import urllib.request

# The manifest types a registry may store under a tag: single-platform images and indexes
# that point at one image per platform, in Docker's and OCI's formats.
MANIFEST_TYPES = ", ".join(
    [
        "application/vnd.oci.image.index.v1+json",
        "application/vnd.oci.image.manifest.v1+json",
        "application/vnd.docker.distribution.manifest.list.v2+json",
        "application/vnd.docker.distribution.manifest.v2+json",
    ]
)


def pin(reference: str) -> str:
    """The reference to record for an image that was just pushed.

    A tag is a name that can move. Ask the registry which manifest the tag points at right now
    and record its digest, which can only ever mean these exact bytes.
    """
    name, _, tag = reference.rpartition(":")
    registry, _, repository = name.partition("/")
    request = urllib.request.Request(
        f"http://{registry}/v2/{repository}/manifests/{tag}",
        method="HEAD",
        headers={"Accept": MANIFEST_TYPES},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        digest = response.headers["Docker-Content-Digest"]
    return f"{name}@{digest}"
