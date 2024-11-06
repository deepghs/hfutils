import logging
import os.path

import importlib_metadata
from hbutils.reflection import quick_import_object


def get_resource_files_from_package(package):
    try:
        path, _, _ = quick_import_object(f'{package}.__file__')
    except ImportError:
        logging.warning(f'Cannot check {package!r} directory, skipped.')
        return

    if os.path.splitext(os.path.basename(path))[0] != '__init__':  # single file package
        return
    root_dir = os.path.dirname(path)

    for root, _, files in os.walk(root_dir):
        for file in files:
            src_file = os.path.abspath(os.path.join(root, file))
            _, ext = os.path.splitext(os.path.basename(src_file))
            if not ext.startswith('.py') and ext not in {'.so', '.ddl'}:
                yield src_file, os.path.relpath(os.path.dirname(src_file), os.path.dirname(os.path.abspath(root_dir)))


def list_installed_packages():
    installed_packages = importlib_metadata.distributions()
    for dist in installed_packages:
        yield dist.metadata['Name']


def get_resource_files():
    yield from get_resource_files_from_package('random_user_agent')
    # for pack_name in list_installed_packages():
    #     yield from get_resource_files_from_package(pack_name)


def print_resource_mappings():
    for rfile, dst_file in get_resource_files():
        t = f'{rfile}{os.pathsep}{dst_file}'
        print(f'--add-data {t!r}')


if __name__ == '__main__':
    # print(list_installed_packages())
    print_resource_mappings()
