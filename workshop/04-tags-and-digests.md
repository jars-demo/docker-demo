# Tags and digests

> A tag is a name that can move. A digest is the image itself. Deploy and record the one that cannot change.

**Time:** 15 minutes

## Goal

Know what a tag and a digest are, see how a mutable tag turns a rollback into a roll forward, pin images by digest, and understand why two builds of the same commit can still produce different digests.

## The case

```bash
uv run python -m dock run 4
```

```text
10:05 deploy    node-1 a1f3  node-2 a1f3  node-3 a1f3   sencha 4.50
11:05 deploy    node-1 9c2e  node-2 9c2e  node-3 7d40   sencha 0.00
11:10 rollback  node-1 7d40  node-2 7d40  node-3 7d40   sencha 0.00
the 10:05 release was recorded as: tidepool/orders:main
the rollback should have run a1f3 everywhere. It ran 7d40, a build nobody chose.
```

CI builds every commit on main and pushes it as `tidepool/orders:main`. At 11:05 a release starts selling sencha for nothing. While it rolls out, CI pushes another commit, so node 3 runs something different from nodes 1 and 2. At 11:10 someone rolls back to the 10:05 release, and gets the newest build instead. Open `lab/cases/case04_tags.py`.

## What a name points at

A registry stores two kinds of things.

- **Content**, addressed by its hash. Each layer and each image manifest has a **digest** such as `sha256:3f9a...`, the SHA-256 of its bytes. Change one byte and you have a different digest. A digest can never point at anything else.
- **Tags**, which are names that point at a manifest digest. `main`, `latest` and `1.4` are tags. Pushing to a tag moves it. The old image is still there, under its digest, but the name now means something new.

`latest` is not special. It is the tag Docker uses when you do not give one, nothing more. It does not mean newest, and it does not mean stable.

You can run an image by digest: `docker pull tidepool/orders@sha256:3f9a...`. That reference means one image forever. `docker buildx imagetools inspect tidepool/orders:main` shows what a tag points at right now.

## Three ways a moving tag hurts

**Rollbacks that roll forward.** If the release history says `orders:main`, rolling back means "run whatever `main` is now", which is the newest build. The case shows exactly that.

**Nodes that disagree.** Each node resolves the tag when it pulls. If the tag moves during a rollout, the first nodes and the last ones run different code under the same release. Worse, a node that already has `orders:main` on disk may not pull at all. Kubernetes pulls on every start only for `:latest` or with `imagePullPolicy: Always`; for other tags the default is to use the copy already on the node. Two nodes, same tag, different code, for days.

**Builds that drift.** `FROM python:3.13-slim` is a tag too. It moves when the base image gets security fixes, which is good, but it means rebuilding last month's commit today gives you a different image. Pin the base by digest, and let a bot such as Renovate or Dependabot open a pull request when it moves. Then every change to what you ship is a reviewed commit.

## Tags for people, digests for machines

Tags are still useful: they are how humans and CI find images. A sensible scheme:

- An **immutable tag per build**, such as the commit SHA (`orders:9c2e1b7`). Many registries can refuse to overwrite a tag, which turns this convention into a rule.
- **Moving tags** for humans (`main`, `staging`), never written into a deploy.
- **Deploy by digest.** Resolve the tag once, at the start of the deploy, and record `name@sha256:...` in the release history. Every node pulls that, and a rollback replays it exactly.

For images built for more than one CPU type, the tag points at an **index** that lists one manifest per platform. Pin the index digest, and each node still pulls the right platform from it.

## Same commit, different digest

A digest hashes bytes, and a layer's bytes include more than your files' contents. Each file in a layer tar carries a timestamp, an owner and a position in the archive. Compressed layers add a timestamp in the gzip header. See it:

```bash
uv run python -m dock try digest
```

```text
Python 3.13.16, Linux, 4 CPUs
One layer: the same three files, with the same bytes, packed in different ways.

  how the layer was packed            digest
  as found                            sha256:07439f7f834b0954
  as found, packed again              sha256:07439f7f834b0954
  names in another order              sha256:89086aabaff33d5d
  app.py touched, bytes unchanged     sha256:5941e595746bed97
  mtime set to 0, names sorted        sha256:9ffe813e6cd84c53
  touched again, mtime set to 0       sha256:9ffe813e6cd84c53
  gzip of that, header time now       sha256:ad79097e9858ef08
  gzip of that, header time + 1 s     sha256:5a8a89cc39bee64d
  gzip of that, header time 0         sha256:96eb4231b89256f7
  gzip of that, header time 0 again   sha256:96eb4231b89256f7

Same bytes, different digest, whenever a timestamp or the order of the files changes.
Pin those (SOURCE_DATE_EPOCH, sorted files) and the digest only moves with the content.
```

Touching a file without changing it gives a new digest. Pinning the timestamps and the order gives the same digest every time, on any machine. This is what **reproducible builds** are about, and recent BuildKit versions can rewrite timestamps from `SOURCE_DATE_EPOCH` to get there. Note the difference from chapter 01: the build cache ignores timestamps when it hashes a `COPY`, but the layer it writes still records them.

Reproducibility is not needed to deploy safely. Pinning by digest is. Reproducibility lets you check that an image really came from the source it claims.

## Fix the case

Change what a deploy writes down, so that the history names the exact image that ran, and every node in the rollout runs that same image. A fresh deploy of `main` must still pick up the newest build.

## Check it works

```bash
uv run python -m dock check 4
```

```text
  PASS  the rollback runs a1f3 on every node (ran a1f3, a1f3, a1f3)
  PASS  one deploy runs one build on every node (11:05 ran 9c2e, 9c2e, 9c2e)
  PASS  a new deploy of :main picks up the newest build, c0de (ran c0de, c0de, c0de)
```

## Exercise

The 11:05 release was broken, and your fix makes every node run the same broken build. Explain why that is still better than the mixed rollout. Then design the tags for Tidepool Tea: what CI pushes for each commit, what a human types to deploy, and what the release history stores.

### More to try

- Hard-code the digest of the good build into `record` and run the check. Which line fails, and what would happen at the next real release?
- If you have Docker, run `docker image ls --digests` and pick an image with a tag. Pull the same tag next week and compare.
