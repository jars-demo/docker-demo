"""Release records.

After the pipeline pushes an image, it calls pin() and stores the result as this release's
image. A rollback runs exactly what was stored. Only change pin().
"""


def pin(reference: str) -> str:
    """The reference to record for an image that was just pushed.

    reference is what the pipeline pushed, such as localhost:5000/dockerlab/api:stable.
    """
    return reference
