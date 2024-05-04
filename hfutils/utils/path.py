import os


def hf_normpath(path):
    return os.path.normpath(path).replace('\\', '/')
