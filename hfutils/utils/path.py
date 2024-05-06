import os
import re


def hf_normpath(path) -> str:
    return re.sub(
        r'[\\/]+', '/',
        os.path.relpath(
            os.path.normpath(os.path.join(os.path.pathsep, path)),
            os.path.pathsep
        )
    )
