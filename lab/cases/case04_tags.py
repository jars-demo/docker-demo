"""Case 04: the rollback that rolled forward.

CI builds every commit on main and pushes it as tidepool/orders:main. Deploys run that tag on
three nodes and write it down in the release history. At 11:05 a release breaks the menu, so at
11:10 someone rolls back to the 10:05 release. The menu is still broken.
Run it: uv run python -m dock run 4
"""

import hashlib

IMAGE = "tidepool/orders"

# What each commit's image does. Only the first one is good.
BUILDS = {
    "a1f3": "commit a1f3: sencha 4.50",
    "9c2e": "commit 9c2e: sencha 0.00",
    "7d40": "commit 7d40: sencha 0.00",
    "c0de": "commit c0de: sencha 4.60",
}


class Registry:
    """Tags point at digests, and a push moves the tag. A digest names one exact image."""

    def __init__(self) -> None:
        self.blobs: dict[str, str] = {}
        self.tags: dict[str, str] = {}

    def push(self, tag: str, commit: str) -> str:
        content = BUILDS[commit]
        digest = "sha256:" + hashlib.sha256(content.encode()).hexdigest()
        self.blobs[digest] = content
        self.tags[tag] = digest
        return digest

    def resolve(self, ref: str) -> str:
        """The digest a reference means right now: name@sha256:... always, name:tag today."""
        if "@" in ref:
            return ref.split("@", 1)[1]
        return self.tags[ref]

    def pull(self, ref: str) -> str:
        return self.blobs[self.resolve(ref)]


class Cluster:
    def __init__(self, registry: Registry, nodes: int = 3) -> None:
        self.registry = registry
        self.nodes: list[str] = [""] * nodes
        self.history: list[str] = []
        self.between_nodes = lambda node: None  # whatever else happens during a rollout

    def record(self, ref: str) -> str:
        """What the release history keeps for a deploy of ref."""
        return ref

    def rollout(self, ref: str) -> None:
        for node in range(len(self.nodes)):
            self.nodes[node] = self.registry.pull(ref)
            self.between_nodes(node)

    def deploy(self, ref: str) -> None:
        entry = self.record(ref)
        self.history.append(entry)
        self.rollout(entry)

    def rollback(self) -> None:
        self.history.pop()
        self.rollout(self.history[-1])


def day() -> tuple[Registry, Cluster, dict[str, list[str]]]:
    """The morning, as it happened. Returns what every node ran after each step."""
    registry = Registry()
    cluster = Cluster(registry)
    seen: dict[str, list[str]] = {}

    registry.push(f"{IMAGE}:main", "a1f3")
    cluster.deploy(f"{IMAGE}:main")
    seen["10:05 deploy"] = list(cluster.nodes)

    registry.push(f"{IMAGE}:main", "9c2e")

    def ci_pushes_mid_rollout(node: int) -> None:
        if node == 1:
            registry.push(f"{IMAGE}:main", "7d40")

    cluster.between_nodes = ci_pushes_mid_rollout
    cluster.deploy(f"{IMAGE}:main")
    cluster.between_nodes = lambda node: None
    seen["11:05 deploy"] = list(cluster.nodes)

    cluster.rollback()
    seen["11:10 rollback"] = list(cluster.nodes)
    return registry, cluster, seen


def commit(build: str) -> str:
    return build.split()[1].rstrip(":")


def run() -> None:
    _, cluster, seen = day()
    for when, nodes in seen.items():
        ran = "  ".join(f"node-{n + 1} {commit(build)}" for n, build in enumerate(nodes))
        print(f"{when:<16}{ran}   {nodes[0].split(': ')[1]}")
    print(f"the 10:05 release was recorded as: {cluster.history[-1]}")
    print("the rollback should have run a1f3 everywhere. It ran 7d40, a build nobody chose.")
