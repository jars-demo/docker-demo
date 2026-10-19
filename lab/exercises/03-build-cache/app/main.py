"""A small FastAPI service. VERSION changes with every release."""

from fastapi import FastAPI

VERSION = "1"

app = FastAPI()


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@app.get("/version")
def version() -> dict:
    return {"version": VERSION}
