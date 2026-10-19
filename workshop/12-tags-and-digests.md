# Tags, digests and registries

> A tag is a name that the next push can move. A digest is the hash of one exact image. Deploy and roll back by digest.

**Time:** 25 minutes

## Goal

By the end of this chapter you can push to a registry, explain how tags and digests differ, ask a registry for a tag's digest over its HTTP API, and make a rollback run exactly what ran before. The chapter ends with a checklist for production images.

## The idea

### What a registry stores

A registry stores three kinds of things, all addressed by the SHA-256 hash of their content:

- **blobs**: each layer, and the image config
- **manifests**: a small JSON document that lists one image's config and layers
- **indexes** (manifest lists): one manifest per platform, such as `linux/amd64` and `linux/arm64`

A **tag** is a pointer from a name to a manifest or index. `docker push app:stable` uploads the blobs and manifest, then moves the `stable` tag to point at it. The previous image is still there, but nothing called `stable` leads to it any more.

### Digests

The hash of a manifest is its **digest**: `sha256:3245cc83...`. A reference with a digest, `localhost:5000/dockerlab/api@sha256:3245cc83...`, can only ever mean those exact bytes. If anyone changed one byte of one layer, the digest would change.

The registry tells you a tag's current digest in a response header. This is the Docker Registry HTTP API, the same one `docker pull` uses:

```bash
curl -sI -H "Accept: application/vnd.oci.image.index.v1+json, application/vnd.oci.image.manifest.v1+json, application/vnd.docker.distribution.manifest.list.v2+json, application/vnd.docker.distribution.manifest.v2+json" \
  http://localhost:5000/v2/dockerlab/api/manifests/stable
```

```text
Content-Type: application/vnd.docker.distribution.manifest.v2+json
Docker-Content-Digest: sha256:0848ae1e8f60d116809b374327f055809de198ca7b2ff62bef6e1c27a1e88c2a
```

### Why mutable tags hurt

- **Rollbacks.** If a release recorded `app:stable` and someone pushed since, "roll back" runs the new image.
- **Drift.** Two servers that pulled `app:stable` an hour apart can run different code.
- **Base images.** `FROM python:3.13-slim` is rebuilt upstream every few weeks. Two builds of the same commit can differ.

## The exercise

Open `lab/exercises/12-tags-and-digests/`. The pipeline builds the API, pushes it as `stable`, and calls `pin()` in `release.py` to decide what to record for that release. A rollback runs whatever was recorded. Only change `pin()`:

```python
def pin(reference: str) -> str:
    """The reference to record for an image that was just pushed."""
    return reference
```

`dock run 12` starts a real registry (`registry:3.0.0`) in a container, releases 1.4.0, then releases 1.5.0 under the same tag, then rolls back:

```bash
uv run python -m dock run 12
```

```text
release 1.4.0 recorded as  localhost:56579/dockerlab/api:stable
release 1.5.0 recorded as  localhost:56579/dockerlab/api:stable

1.5.0 has a bug. Roll back: run the image recorded for 1.4.0.
$ docker run localhost:56579/dockerlab/api:stable
the running version is 1.5.0
```

The registry port changes on every run, because the lab lets the system pick a free one.

## Reasoning towards the fix

Both records are the same string, and that string now points at 1.5.0. The record has to name the image itself, not the tag.

Right after the push, ask the registry which manifest the tag points at: a `HEAD` request to `/v2/<repository>/manifests/<tag>`, with an `Accept` header listing the manifest types, returns it in `Docker-Content-Digest`. Return `name@digest`. Python's `urllib.request` is enough.

## Check your fix

```bash
uv run python -m dock check 12
```

As shipped:

```text
  FAIL  the recorded reference names a digest (localhost:56590/dockerlab/api:stable)
  FAIL  rolling back to the first release runs 1.4.0 (it ran 1.5.0)
  FAIL  each release recorded a different image
```

The checker deletes every local copy of both images before the rollback, so `docker run` has to pull exactly what was recorded. Reading the digest that Docker stored locally after the push (`RepoDigests` in `docker image inspect`) is another correct fix, and the tests accept it.

## In production

- **Build once, promote the digest.** Test the image built from a commit, then deploy that same digest to staging and production. Do not rebuild per environment.
- **Pin base images by digest** too: `FROM python:3.13.16-slim-trixie@sha256:...`, and let Renovate or Dependabot propose updates, so base image changes are reviewed commits.
- **Multi-platform images.** `docker buildx build --platform linux/amd64,linux/arm64 --push` pushes an index. Its digest covers every platform, and each node pulls its own.
- **Immutable tags.** Most hosted registries can refuse pushes that would move an existing tag. Turn it on for release tags.
- **Sign and attest.** `cosign sign` and build provenance attestations let a cluster refuse images that your pipeline did not build.

## Production checklist

Ten questions to ask of every image before it ships:

1. Does the main process run in the foreground as PID 1, and handle SIGTERM? (chapters 01 and 09)
2. Does `.dockerignore` keep secrets, `.git` and test data out of the context? (chapter 02)
3. Are dependency manifests copied and installed before the code? (chapter 03)
4. Does the server listen on 0.0.0.0, and are only the needed ports published? (chapter 04)
5. Does it run as a non-root user, with data in volumes it owns? (chapter 05)
6. Do dependent services wait for real readiness, and retry anyway? (chapter 06)
7. Are build secrets mounted, never passed as `ARG` or `ENV`? (chapter 07)
8. Is the runtime image built in its own stage, without compilers or package caches? (chapter 08)
9. Is there a health check that fails when the service is broken? (chapter 10)
10. Are CPU and memory limits set, and does the app size itself from them? Is every deploy and rollback by digest? (chapters 11 and 12)

## Key points

- A registry stores content by hash. A tag is a movable pointer to a manifest.
- A digest names one exact image forever.
- Record digests for releases, and roll back by digest.
- The registry reports a tag's digest in the `Docker-Content-Digest` header.
