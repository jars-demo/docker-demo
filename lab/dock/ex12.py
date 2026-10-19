"""12: tags, digests and a real registry."""

import importlib.util
from collections.abc import Callable
from pathlib import Path

from dock import docker as d

TITLE = "The rollback that rolled forward"
HINTS = [
    "Print both release records. What do they have in common?",
    "A tag is a name that the next push moves. A digest names one exact manifest, forever.",
    "In pin(), ask the registry for the tag's digest: a HEAD request to "
    "/v2/<repository>/manifests/<tag> returns it in the Docker-Content-Digest header. "
    "Return name@digest.",
]
REGISTRY_IMAGE = "registry:3.0.0"


def load_pin(path: Path) -> Callable[[str], str]:
    spec = importlib.util.spec_from_file_location("release", path / "release.py")
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module.pin


def scenario(path: Path, prefix: str) -> dict:
    """Release 1.4.0, then 1.5.0 under the same tag, then roll back to the 1.4.0 record."""
    registry, app = f"{prefix}-registry", f"{prefix}-app"
    port = d.free_port()
    d.run(REGISTRY_IMAGE, registry, "-p", f"127.0.0.1:{port}:5000")
    d.wait_http(f"http://127.0.0.1:{port}/v2/", 15)
    reference = f"localhost:{port}/dockerlab/api:stable"
    pin = load_pin(path)
    records, images = [], []
    try:
        for version in ("1.4.0", "1.5.0"):
            build = d.build(path / "app", reference, "--build-arg", f"VERSION={version}")
            if not build.ok:
                return {"error": build.error()}
            images.append(
                d.docker("image", "inspect", reference, "--format", "{{.Id}}").stdout.strip()
            )
            d.docker("push", "-q", reference)
            records.append(pin(reference))
        # A fresh server: nothing cached locally, so the rollback must pull what was recorded.
        d.docker("image", "rm", "-f", *images, check=False)
        d.run(records[0], app, "-p", "127.0.0.1::8000")
        port_app = d.host_port(app)
        reply = (
            d.wait_http(f"http://127.0.0.1:{port_app}/version", 15) if port_app else d.Reply(0, "")
        )
        return {"records": records, "ran": reply.json().get("version", "-")}
    except Exception as error:  # a broken pin() should fail the check, not crash the lab
        return {"error": f"{type(error).__name__}: {error}", "records": records}
    finally:
        d.remove(app, registry)
        d.docker("image", "rm", "-f", *images, check=False)


def run(path: Path) -> None:
    result = scenario(path, "dockerlab-12")
    if "ran" not in result:
        print(f"the release failed: {result.get('error')}")
        return
    first, second = result["records"]
    print(f"release 1.4.0 recorded as  {first}")
    print(f"release 1.5.0 recorded as  {second}")
    print()
    print("1.5.0 has a bug. Roll back: run the image recorded for 1.4.0.")
    print(f"$ docker run {first}")
    print(f"the running version is {result['ran']}")


def check(path: Path) -> list[tuple[str, bool]]:
    result = scenario(path, "dockerlab-12-check")
    records = result.get("records", [])
    first = records[0] if records else ""
    if "error" in result:
        return [(f"the release runs ({result['error']})", False)]
    return [
        (f"the recorded reference names a digest ({first})", "@sha256:" in first),
        (
            f"rolling back to the first release runs 1.4.0 (it ran {result['ran']})",
            result["ran"] == "1.4.0",
        ),
        ("each release recorded a different image", len(set(records)) == 2),
    ]
