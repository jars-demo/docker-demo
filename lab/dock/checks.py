"""How each case is checked. Every check takes the case module, so the tests can check a fixed
copy too. A check says what it expects in plain words.

Every check tests the job as well as the bug, so the lazy way out never passes: no skipping the
dependency install, no deleting the secret the app needs, no running as root."""

from collections.abc import Callable
from types import ModuleType

from dock.engine import installed, mb

Check = tuple[str, bool]


def attempt(fn: Callable[[], object]) -> object:
    """Run fn and return its result, or the exception it raised."""
    try:
        return fn()
    except Exception as error:  # a crash is an answer too
        return error


def check_01(m: ModuleType) -> list[Check]:
    builder = m.Builder()
    result = attempt(lambda: m.morning(builder))
    if isinstance(result, Exception):
        return [(f"the image builds (it raised {result!r})", False)]
    _, second = result
    price = attempt(lambda: m.sencha(second.image))
    edited = m.edit(m.PROJECT, "app.py", '"4.50"', '"4.80"')
    bumped = m.edit(edited, "requirements.txt", "flask==3.1.1", "flask==3.1.2")
    third = attempt(lambda: builder.build(m.DOCKERFILE, bumped))
    flask = "nothing" if isinstance(third, Exception) else installed(third.image).get("flask")
    files = second.image.filesystem()
    return [
        (f"the rebuilt image starts and charges 4.80 for sencha ({price})", price == "4.80"),
        (
            f"a one-line edit to app.py rebuilds in under 5 s (took {second.seconds:.1f} s)",
            second.seconds < 5,
        ),
        (f"a change to requirements.txt is installed: flask {flask}", flask == "3.1.2"),
        (
            "the image holds the whole app: app.py and templates/menu.html",
            {"/app/app.py", "/app/templates/menu.html"} <= set(files),
        ),
    ]


def check_02(m: ModuleType) -> list[Check]:
    build = attempt(m.release)
    if isinstance(build, Exception):
        return [(f"the image builds (it raised {build!r})", False)]
    found = m.leaks(build)
    files = build.image.filesystem()
    paid = attempt(lambda: m.payments(build))
    return [
        (f"no layer, history line or ENV holds the token (found {len(found)})", not found),
        (f"the app gets its token at run time: payments {paid}", paid == "connected"),
        (
            "the image holds the app: app.py and templates/menu.html",
            {"/app/app.py", "/app/templates/menu.html"} <= set(files),
        ),
        (
            "the git history stays out of the image",
            not any("/.git/" in path for layer in build.image.layers for path in layer.files),
        ),
    ]


def check_03(m: ModuleType) -> list[Check]:
    build = attempt(m.release)
    if isinstance(build, Exception):
        return [(f"the image builds (it raised {build!r})", False)]
    image = build.image
    tools = [path.rsplit("/", 1)[1] for path in m.TOOLS if path in image.filesystem()]
    started = m.boot(image)
    return [
        (f"the container starts and serves ({started})", started == "orders: serving on :8080"),
        (f"no compiler or headers in the image (found {', '.join(tools) or 'none'})", not tools),
        (f"the image is under 150 MB (it is {mb(image.bytes)})", image.bytes < 150_000_000),
    ]


def check_04(m: ModuleType) -> list[Check]:
    result = attempt(m.day)
    if isinstance(result, Exception):
        return [(f"the day runs (it raised {result!r})", False)]
    registry, cluster, seen = result
    back = [m.commit(build) for build in seen["11:10 rollback"]]
    during = [m.commit(build) for build in seen["11:05 deploy"]]
    registry.push(f"{m.IMAGE}:main", "c0de")
    deployed = attempt(lambda: cluster.deploy(f"{m.IMAGE}:main"))
    later = [m.commit(build) for build in cluster.nodes]
    return [
        (f"the rollback runs a1f3 on every node (ran {', '.join(back)})", back == ["a1f3"] * 3),
        (
            f"one deploy runs one build on every node (11:05 ran {', '.join(during)})",
            len(set(during)) == 1,
        ),
        (
            f"a new deploy of :main picks up the newest build, c0de (ran {', '.join(later)})",
            not isinstance(deployed, Exception) and later == ["c0de"] * 3,
        ),
    ]


def check_05(m: ModuleType) -> list[Check]:
    result = attempt(m.deploy)
    if isinstance(result, Exception):
        return [(f"the container starts (it raised {result!r})", False)]
    container, took = result
    code = container.main().exit_code
    return [
        (f"docker stop finishes in under 5 s (took {took:.1f} s)", took < 5),
        (f"the container exits cleanly with code 0, not 137 (code {code})", code == 0),
        (f"no order is cut off mid-pack (cut off: {container.cut_off})", not container.cut_off),
        ("migrations still run before the worker starts", container.migrated_before_worker),
        ("docker stop still waits 10 s before SIGKILL (keep GRACE)", m.GRACE == 10.0),
    ]


def check_06(m: ModuleType) -> list[Check]:
    net = attempt(m.up)
    if isinstance(net, Exception):
        return [(f"compose comes up (it raised {net!r})", False)]
    laptop = net.connect("laptop", "localhost", 8080)
    worker = net.connect("worker", "orders", 8080)
    return [
        (f"from the laptop, curl localhost:8080/menu works ({laptop})", laptop == "connected"),
        (f"the worker reaches http://orders:8080 ({worker})", worker == "connected"),
        (
            "orders keeps its own network namespace (no network_mode: host)",
            all(s.get("network_mode") != "host" for s in m.COMPOSE.values()),
        ),
        (
            "the database stays private: the laptop cannot reach port 5432",
            net.connect("laptop", "localhost", 5432) != "connected",
        ),
    ]


def check_07(m: ModuleType) -> list[Check]:
    stack = attempt(m.morning)
    if isinstance(stack, Exception):
        return [(f"compose comes up (it raised {stack!r})", False)]
    ready = stack.ready_at
    shown = "never" if ready is None else f"{ready:.1f} s"
    return [
        (
            f"all {len(m.CUSTOMERS)} customers can order (served {stack.served()})",
            stack.served() == len(m.CUSTOMERS),
        ),
        (
            f"orders serves within 2 s of the database being ready (at {shown}, db at 6.8 s)",
            ready is not None and ready - m.DB_READY <= 2.0,
        ),
        (f"no crash loop: orders starts once (restarts: {stack.restarts})", stack.restarts == 0),
        ("the database still takes 6.8 s to get ready", m.DB_READY == 6.8),
    ]


def check_08(m: ModuleType) -> list[Check]:
    result = attempt(m.redeploy)
    if isinstance(result, Exception):
        return [(f"the redeploy runs (it raised {result!r})", False)]
    _, _, before, second = result
    after = len(second.orders())
    mode = second.stat("/data")[1]
    return [
        (f"orders survive a redeploy ({before} before, {after} after)", before == after == 42),
        (f"the app runs as uid 10001, not root (uid {second.uid})", second.uid == 10001),
        (f"/data is not world-writable (mode {mode:o})", not mode & 0o002),
        ("orders are saved on the volume, not in the container", second.path in second.mounts),
    ]


def check_09(m: ModuleType) -> list[Check]:
    scenarios = {
        "production": m.PRODUCTION,
        "an 8-CPU host with no limit": m.limits("max 100000", "max", host_cpus=8),
        "a 1.5-CPU limit": m.limits("150000 100000", str(512 * 2**20), host_cpus=16),
    }
    booted = {
        name: attempt(lambda machine=machine: m.boot(machine))
        for name, machine in scenarios.items()
    }
    for name, result in booted.items():
        if isinstance(result, Exception):
            return [(f"the workers start on {name} (it raised {result!r})", False)]
    prod, free, half = (
        booted["production"],
        booted["an 8-CPU host with no limit"],
        booted["a 1.5-CPU limit"],
    )
    return [
        (
            f"2 CPUs and 1 GB: no OOM kill ({prod[0]} workers, {prod[2]:.0f} MB)",
            prod[1] is None,
        ),
        (f"2 CPUs: between 2 and 5 workers, to use both (got {prod[0]})", 2 <= prod[0] <= 5),
        (
            f"no CPU limit on an 8-CPU host: between 8 and 17 workers (got {free[0]})",
            8 <= free[0] <= 17 and free[1] is None,
        ),
        (
            f"1.5 CPUs and 512 MB: between 2 and 5 workers, no OOM kill (got {half[0]})",
            2 <= half[0] <= 5 and half[1] is None,
        ),
    ]


CHECKS: dict[int, Callable[[ModuleType], list[Check]]] = {
    1: check_01,
    2: check_02,
    3: check_03,
    4: check_04,
    5: check_05,
    6: check_06,
    7: check_07,
    8: check_08,
    9: check_09,
}
