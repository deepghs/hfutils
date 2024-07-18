Search.setIndex({"docnames": ["api_doc/archive/index", "api_doc/cache/delete", "api_doc/cache/index", "api_doc/config/index", "api_doc/config/meta", "api_doc/entry/base", "api_doc/entry/cli", "api_doc/entry/dispatch", "api_doc/entry/download", "api_doc/entry/index", "api_doc/entry/ls", "api_doc/entry/ls_repo", "api_doc/entry/upload", "api_doc/entry/whoami", "api_doc/index/fetch", "api_doc/index/index", "api_doc/index/make", "api_doc/index/validate", "api_doc/operate/base", "api_doc/operate/download", "api_doc/operate/index", "api_doc/operate/upload", "api_doc/operate/validate", "api_doc/utils/binary", "api_doc/utils/download", "api_doc/utils/index", "api_doc/utils/path", "api_doc/utils/tqdm_", "api_doc/utils/walk", "index", "information/environment", "information/environment.result", "tutorials/installation/index", "tutorials/quick_start/index"], "filenames": ["api_doc/archive/index.rst", "api_doc/cache/delete.rst", "api_doc/cache/index.rst", "api_doc/config/index.rst", "api_doc/config/meta.rst", "api_doc/entry/base.rst", "api_doc/entry/cli.rst", "api_doc/entry/dispatch.rst", "api_doc/entry/download.rst", "api_doc/entry/index.rst", "api_doc/entry/ls.rst", "api_doc/entry/ls_repo.rst", "api_doc/entry/upload.rst", "api_doc/entry/whoami.rst", "api_doc/index/fetch.rst", "api_doc/index/index.rst", "api_doc/index/make.rst", "api_doc/index/validate.rst", "api_doc/operate/base.rst", "api_doc/operate/download.rst", "api_doc/operate/index.rst", "api_doc/operate/upload.rst", "api_doc/operate/validate.rst", "api_doc/utils/binary.rst", "api_doc/utils/download.rst", "api_doc/utils/index.rst", "api_doc/utils/path.rst", "api_doc/utils/tqdm_.rst", "api_doc/utils/walk.rst", "index.rst", "information/environment.ipynb", "information/environment.result.ipynb", "tutorials/installation/index.rst", "tutorials/quick_start/index.rst"], "titles": ["hfutils.archive", "hfutils.cache.delete", "hfutils.cache", "hfutils.config", "hfutils.config.meta", "hfutils.entry.base", "hfutils.entry.cli", "hfutils.entry.dispatch", "hfutils.entry.download", "hfutils.entry", "hfutils.entry.ls", "hfutils.entry.ls_repo", "hfutils.entry.upload", "hfutils.entry.whoami", "hfutils.index.fetch", "hfutils.index", "hfutils.index.make", "hfutils.index.validate", "hfutils.operate.base", "hfutils.operate.download", "hfutils.operate", "hfutils.operate.upload", "hfutils.operate.validate", "hfutils.utils.binary", "hfutils.utils.download", "hfutils.utils", "hfutils.utils.path", "hfutils.utils.tqdm", "hfutils.utils.walk", "Welcome to hfutils\u2019s Documentation", "Run Environment Information", "Run Environment Information", "Installation", "Quick Start"], "terms": {"overview": [0, 2, 4], "pack": 0, "unpack": 0, "manag": [0, 2], "support": 0, "format": 0, "extens": 0, "name": [0, 5], "7z": 0, "bztar": 0, "tar": [0, 14, 16, 17], "bz2": 0, "tbz2": 0, "gztar": 0, "gz": 0, "tgz": 0, "rar": 0, "xztar": 0, "xz": 0, "txz": 0, "zip": 0, "If": [0, 1, 5, 17, 19, 21, 24, 26, 27], "you": [0, 14, 32], "requir": [0, 32], "simpli": [0, 32], "instal": [0, 29], "us": [0, 1, 5, 14, 16, 17, 18, 19, 21, 24, 29, 32], "follow": [0, 10, 32], "code": [0, 5, 8, 12], "pip": [0, 32], "The": [0, 1, 5, 8, 10, 12, 14, 16, 17, 18, 19, 21, 22, 23, 24, 26, 28, 32], "creation": 0, "file": [0, 5, 8, 10, 12, 14, 16, 17, 18, 19, 21, 22, 23, 24, 28], "i": [0, 1, 8, 11, 12, 14, 16, 17, 19, 22, 23, 26, 29, 30, 31, 32], "we": 0, "util": [0, 29, 32], "rarfil": 0, "librari": [0, 24], "which": [0, 14, 30, 31, 32], "doe": [0, 14], "offer": 0, "function": [0, 5, 14, 16, 17, 23, 24, 27], "creat": [0, 16], "str": [0, 1, 5, 8, 10, 11, 12, 14, 16, 17, 18, 19, 21, 22, 23, 24, 26, 28], "ext": 0, "list": [0, 5, 10, 14, 18, 19, 21], "fn_pack": 0, "callabl": [0, 5], "fn_unpack": 0, "sourc": [0, 1, 5, 7, 8, 10, 11, 12, 14, 16, 17, 18, 19, 21, 22, 23, 24, 26, 27, 28], "regist": 0, "custom": [0, 5, 8, 12], "type": [0, 1, 5, 10, 14, 16, 17, 18, 19, 21, 22, 23, 24, 26, 27, 28], "associ": 0, "paramet": [0, 1, 5, 7, 8, 10, 12, 14, 16, 17, 18, 19, 21, 22, 23, 24, 26, 27, 28], "A": [0, 18], "take": 0, "directori": [0, 1, 10, 16, 17, 19, 21, 28], "an": [0, 14, 16, 17, 19, 21, 24, 27, 28], "filenam": [0, 24, 26], "input": 0, "extract": [0, 19], "type_nam": 0, "archive_fil": 0, "silent": [0, 16, 19, 21, 24, 27], "bool": [0, 7, 14, 16, 17, 19, 21, 22, 23, 24, 27], "fals": [0, 14, 16, 17, 19, 21, 22, 23, 24, 27], "clear": [0, 21], "specifi": [0, 1, 17, 21, 24], "result": 0, "true": [0, 14, 16, 17, 19, 21, 22, 23, 24, 27], "suppress": [0, 16, 19, 21, 24], "warn": [0, 5], "dure": 0, "process": 0, "remov": [0, 21], "exist": [0, 14, 19], "when": [0, 11, 14, 16, 19], "return": [0, 5, 14, 16, 17, 18, 22, 23, 24, 26, 27, 28], "path": [0, 8, 12, 14, 16, 17, 18, 19, 21, 22, 23, 24, 25, 28, 29], "password": [0, 19], "none": [0, 1, 5, 7, 8, 12, 14, 16, 17, 18, 19, 21, 22, 24, 26], "content": [0, 27], "option": [0, 1, 5, 7, 8, 12, 14, 16, 17, 18, 19, 21, 22, 24, 26, 27], "determin": 0, "base": [0, 9, 10, 17, 20, 29], "rais": [0, 11, 14, 17, 26], "valueerror": [0, 26], "ani": [0, 1, 7, 23, 26], "get": [0, 14, 16, 18, 24, 26], "repo_id": [1, 14, 16, 17, 18, 19, 21, 22, 26], "repo_typ": [1, 14, 16, 17, 18, 19, 21, 22, 26], "cache_dir": 1, "all": [1, 14, 19, 28], "detach": 1, "revis": [1, 14, 16, 17, 18, 19, 21, 22, 26], "from": [1, 5, 14, 16, 17, 18, 19, 24, 30, 31, 32], "match": [1, 14, 17, 22], "repositori": [1, 8, 12, 14, 16, 17, 18, 19, 21, 22, 26], "id": [1, 17, 26], "where": [1, 17, 24], "store": [1, 17], "default": [1, 16, 17, 19, 22, 26], "huggingfac": [2, 17, 18, 19, 21, 26, 29, 32], "local": [2, 11, 14, 16, 19, 21, 22, 24, 30, 31], "can": [2, 14, 17, 32], "quickli": 2, "make": [2, 15, 17, 29], "disk": 2, "space": [2, 14, 16, 17, 18, 19, 21, 22, 26], "under": [2, 32], "control": 2, "delet": [2, 29], "delete_detached_cach": 2, "delete_cach": 2, "meta": [3, 14, 29, 32], "__title__": [3, 32], "__version__": [3, 32], "__description__": [3, 32], "__author__": [3, 32], "__author_email__": 3, "inform": [4, 5, 7, 14, 16, 17], "packag": 4, "titl": 4, "thi": [4, 5, 8, 12, 14, 16, 17, 23, 24, 26, 27, 30, 31], "project": 4, "should": [4, 24, 32], "version": [4, 7, 27, 32], "short": 4, "descript": [4, 24], "includ": [4, 5, 14, 16], "setup": 4, "py": 4, "author": 4, "email": 4, "help_option_nam": 5, "h": 5, "help": 5, "dict": [5, 14, 16], "new": 5, "empti": 5, "dictionari": [5, 14], "map": 5, "initi": 5, "object": [5, 10, 14, 18, 19, 21, 24], "": [5, 7, 14], "kei": [5, 14], "valu": [5, 7, 10, 16], "pair": 5, "iter": [5, 28], "via": 5, "d": 5, "k": 5, "v": 5, "kwarg": [5, 7, 24, 27], "keyword": [5, 24, 27], "argument": [5, 14, 24, 27], "For": 5, "exampl": [5, 14], "one": 5, "1": [5, 10, 16, 17, 30, 31], "two": 5, "2": [5, 10, 32], "class": [5, 8, 10, 11, 12, 14, 26], "messag": [5, 8, 11, 12, 16, 21], "except": [5, 8, 11, 12, 14], "displai": [5, 8, 12, 24, 27], "yellow": 5, "color": 5, "error": [5, 8, 12], "exit_cod": [5, 8, 12], "exit": [5, 8, 12], "show": [5, 8, 12], "io": [5, 8, 12, 32], "write": [5, 8, 12], "output": [5, 8, 12, 19, 21, 24, 27, 32], "red": [5, 8, 12], "err": 5, "baseexcept": 5, "print": [5, 7, 30, 31, 32], "traceback": 5, "provid": [5, 24], "built": 5, "msg": 5, "handl": 5, "keyboard": 5, "interrupt": 5, "__init__": 5, "7": 5, "decor": 5, "wrap": 5, "click": [5, 7], "command": [5, 32], "catch": 5, "consist": 5, "group": 6, "hfutilcli": [6, 9], "ctx": 7, "context": 7, "param": 7, "cli": [7, 9, 29], "current": [7, 30, 31, 32], "metadata": 7, "arg": [7, 27], "indic": [8, 12], "remot": [8, 12], "assign": [8, 12, 14, 18, 19, 21], "17": 8, "context_set": 9, "clickwarningexcept": 9, "clickerrorexcept": 9, "print_except": 9, "keyboardinterrupt": 9, "command_wrap": 9, "dispatch": [9, 29], "print_vers": 9, "download": [9, 14, 17, 20, 25, 29], "noremotepathassignedwithdownload": 9, "l": [9, 29], "listitemtyp": 9, "listitem": 9, "ls_repo": [9, 29], "nolocalauthent": 9, "upload": [9, 16, 20, 29], "noremotepathassignedwithupload": 9, "whoami": [9, 29], "enum": 10, "repres": [10, 14], "differ": [10, 14, 30, 31], "item": [10, 17], "valid": [10, 15, 20, 29], "ar": [10, 14], "folder": 10, "imag": [10, 14], "3": [10, 30, 31, 32], "archiv": [10, 14, 16, 17, 19, 21, 29], "4": [10, 30, 31], "model": [10, 14, 16, 17, 18, 19, 21, 22, 26], "5": [10, 19, 30, 31], "data": [10, 14, 30, 31], "6": [10, 30, 31], "repofold": 10, "repofil": [10, 17], "base_dir": 10, "union": [10, 14], "authent": [11, 17], "token": [11, 14, 16, 17, 18, 19, 21, 22], "33": 12, "standalon": 14, "incomplet": 14, "hash": [14, 16, 17, 18, 19, 21], "archive_in_repo": [14, 16, 17, 21], "liter": [14, 16, 17, 18, 19, 21, 22, 26], "dataset": [14, 16, 17, 18, 19, 21, 22, 26], "main": [14, 16, 17, 18, 19, 21, 22, 32], "idx_repo_id": [14, 16, 17], "idx_file_in_repo": [14, 16, 17], "idx_repo_typ": [14, 16, 17], "idx_revis": [14, 16, 17], "hf_token": [14, 16, 17, 18, 19, 21, 22], "hug": [14, 16, 17, 18, 19, 21, 22], "face": [14, 16, 17, 18, 19, 21, 22], "identifi": [14, 16, 18, 19, 21, 22], "repotypetyp": [14, 16, 17, 18, 19, 21, 22, 26], "access": [14, 16], "import": [14, 30, 31, 32], "idx": 14, "deepgh": [14, 32], "danbooru_newest": 14, "0000": 14, "dict_kei": 14, "files": 14, "hash_lf": [14, 17], "7507000": 14, "jpg": 14, "7506000": 14, "7505000": 14, "besid": 14, "also": [14, 24, 32], "explicitli": 14, "nyanko7": 14, "danbooru2023": 14, "danbooru2023_index": 14, "origin": 14, "1000": 14, "png": 14, "10000": 14, "100000": 14, "insid": 14, "file_in_arch": 14, "check": [14, 17, 22, 23, 24, 32], "otherwis": [14, 17, 22, 24], "17506000": 14, "10000000001000": 14, "int": [14, 16, 17, 19, 24], "size": [14, 16, 17, 24, 30, 31], "integ": 14, "filenotfounderror": 14, "435671": 14, "11966": 14, "detail": 14, "offset": 14, "sha256": 14, "265728": 14, "ef6a4e031fdffb705c8ce2c64e8cb8d993f431a887d7c1c0b1e6fa56e6107fcd": 14, "1024": [14, 23], "478d3313860519372f6a75ede287d4a7c18a2d851bbc79b3dd65caff4c716858": 14, "local_fil": [14, 19, 21, 22], "proxi": 14, "user_ag": 14, "header": 14, "endpoint": 14, "save": [14, 16, 19, 24], "http": [14, 32], "request": [14, 24], "user": 14, "agent": 14, "addit": [14, 24, 27], "api": [14, 17, 18, 19, 21, 22], "test_exampl": 14, "destin": 14, "given": [14, 18, 23, 24, 26], "fetch": [15, 29], "archivestandalonefileincompletedownload": 15, "archivestandalonefilehashnotmatch": 15, "hf_tar_get_index": 15, "hf_tar_list_fil": 15, "hf_tar_file_exist": 15, "hf_tar_file_s": 15, "hf_tar_file_info": 15, "hf_tar_file_download": 15, "tar_create_index": 15, "hf_tar_create_index": [15, 17], "tar_get_index_info": 15, "hf_tar_create_from_directori": 15, "hf_tar_item_valid": 15, "hf_tar_valid": 15, "src_tar_fil": 16, "dst_index_fil": 16, "chunk_for_hash": 16, "1048576": 16, "with_hash": 16, "chunk": 16, "20": 16, "mb": 16, "whether": 16, "progress": [16, 19, 21, 24, 27], "bar": [16, 19, 21, 24, 27], "log": 16, "skip_when_sync": 16, "skip": 16, "sync": 16, "readi": [16, 22], "directli": 16, "json": [16, 17], "local_directori": [16, 19, 21], "file_item": 17, "hash_": 17, "expect": [17, 24], "sha": 17, "256": 17, "lf": 17, "entrynotfounderror": 17, "entri": [17, 29], "found": 17, "isadirectoryerror": 17, "mean": [17, 32], "expir": 17, "need": 17, "re": 17, "gener": 17, "so": 17, "togeth": 17, "gracefulli": 17, "refresh": 17, "hfapi": 18, "client": [18, 19, 21], "variabl": [18, 19, 21], "hffilesystem": 18, "system": 18, "subdir": 18, "ignore_pattern": [18, 19, 21], "subdirectori": 18, "e": [18, 19, 21], "g": [18, 19, 21], "branch": [18, 19, 21], "tag": [18, 19, 21], "commit": [18, 19, 21], "pattern": [18, 19, 21], "ignor": [18, 19, 21], "file_in_repo": [19, 21, 22], "resume_download": 19, "within": [19, 21], "resum": 19, "dir_in_repo": 19, "max_work": 19, "8": [19, 30, 31, 32], "max_retri": 19, "max": 19, "worker": 19, "retri": 19, "time": 19, "get_hf_client": 20, "get_hf_f": 20, "list_files_in_repositori": 20, "download_file_to_fil": 20, "download_archive_as_directori": 20, "download_directory_as_directori": 20, "upload_file_to_fil": 20, "upload_directory_as_arch": 20, "upload_directory_as_directori": 20, "is_local_file_readi": 20, "path_in_repo": 21, "time_suffix": 21, "its": 21, "append": 21, "timestamp": 21, "present": 21, "compar": 22, "hub": 22, "read": 23, "first": 23, "byte": [23, 24], "contain": 23, "non": 23, "text": 23, "charact": 23, "url": 24, "expected_s": 24, "desc": 24, "session": 24, "tqdm": [24, 25, 29], "It": [24, 32], "perform": [24, 30, 31], "ensur": 24, "ha": [24, 30, 31], "pass": [24, 27], "binari": [25, 29], "is_binary_fil": 25, "download_fil": 25, "hf_normpath": 25, "hf_fs_path": 25, "parse_hf_fs_path": 25, "hffilesystempath": 25, "walk": [25, 29], "walk_fil": 25, "normal": 26, "filesystem": 26, "pars": 26, "invalid": 26, "tqdm_": 27, "enhanc": 27, "silenc": 27, "modifi": 27, "behavior": 27, "allow": 27, "posit": 27, "std": 27, "recurs": 28, "through": [28, 32], "yield": 28, "rel": 28, "root": 28, "start": [28, 29], "modul": 29, "quick": 29, "run": 29, "environ": 29, "register_archive_typ": 29, "archive_pack": 29, "archive_unpack": 29, "get_archive_typ": 29, "get_archive_extnam": 29, "cach": 29, "config": [29, 32], "index": [29, 32], "oper": 29, "here": [30, 31], "o": [30, 31], "platform": [30, 31], "shutil": [30, 31], "cpuinfo": [30, 31], "psutil": [30, 31], "hbutil": [30, 31], "scale": [30, 31], "size_to_bytes_str": [30, 31], "python": [30, 31, 32], "python_implement": [30, 31], "python_vers": [30, 31], "cpu": [30, 31], "brand": [30, 31], "get_cpu_info": [30, 31], "brand_raw": [30, 31], "count": [30, 31], "cpu_count": [30, 31], "freq": [30, 31], "cpu_freq": [30, 31], "mhz": [30, 31], "memori": [30, 31], "virtual_memori": [30, 31], "total": [30, 31], "precis": [30, 31], "cuda": [30, 31], "ye": [30, 31], "nvidia": [30, 31], "smi": [30, 31], "els": [30, 31], "No": [30, 31], "linux": [30, 31], "0": [30, 31, 32], "1023": [30, 31], "azur": [30, 31], "x86_64": [30, 31], "glibc2": [30, 31], "34": [30, 31], "cpython": [30, 31], "18": [30, 31], "amd": [30, 31], "epyc": [30, 31], "7763": [30, 31], "64": [30, 31], "core": [30, 31], "processor": [30, 31], "2722": 30, "1997499999998": 30, "15": [30, 31], "606": [30, 31], "gib": [30, 31], "pleas": [30, 31], "note": [30, 31], "deploi": [30, 31], "document": [30, 31, 32], "automat": [30, 31], "execut": [30, 31], "github": [30, 31, 32], "action": [30, 31], "therefor": [30, 31], "some": [30, 31], "mai": [30, 31], "your": [30, 31, 32], "2809": 31, "74575": 31, "hfutil": 32, "host": 32, "pypi": 32, "newest": 32, "u": 32, "git": 32, "com": 32, "script": 32, "__name__": 32, "__main__": 32, "develop": 32, "maintain": 32, "like": 32, "below": 32, "success": 32, "9": 32, "narugo1992": 32, "still": 32, "out": 32, "stabl": 32, "html": 32, "faq": 33}, "objects": {"hfutils": [[0, 0, 0, "-", "archive"], [2, 0, 0, "-", "cache"], [3, 0, 0, "-", "config"], [9, 0, 0, "-", "entry"], [15, 0, 0, "-", "index"], [20, 0, 0, "-", "operate"], [25, 0, 0, "-", "utils"]], "hfutils.archive": [[0, 1, 1, "", "archive_pack"], [0, 1, 1, "", "archive_unpack"], [0, 1, 1, "", "get_archive_extname"], [0, 1, 1, "", "get_archive_type"], [0, 1, 1, "", "register_archive_type"]], "hfutils.cache": [[1, 0, 0, "-", "delete"]], "hfutils.cache.delete": [[1, 1, 1, "", "delete_cache"], [1, 1, 1, "", "delete_detached_cache"]], "hfutils.config": [[4, 0, 0, "-", "meta"]], "hfutils.config.meta": [[4, 2, 1, "", "__AUTHOR_EMAIL__"], [4, 2, 1, "", "__AUTHOR__"], [4, 2, 1, "", "__DESCRIPTION__"], [4, 2, 1, "", "__TITLE__"], [4, 2, 1, "", "__VERSION__"]], "hfutils.entry": [[5, 0, 0, "-", "base"], [6, 0, 0, "-", "cli"], [7, 0, 0, "-", "dispatch"], [8, 0, 0, "-", "download"], [10, 0, 0, "-", "ls"], [11, 0, 0, "-", "ls_repo"], [12, 0, 0, "-", "upload"], [13, 0, 0, "-", "whoami"]], "hfutils.entry.base": [[5, 2, 1, "", "CONTEXT_SETTINGS"], [5, 3, 1, "", "ClickErrorException"], [5, 3, 1, "", "ClickWarningException"], [5, 3, 1, "", "KeyboardInterrupted"], [5, 1, 1, "", "command_wrap"], [5, 1, 1, "", "print_exception"]], "hfutils.entry.base.ClickErrorException": [[5, 4, 1, "", "exit_code"], [5, 5, 1, "", "show"]], "hfutils.entry.base.ClickWarningException": [[5, 4, 1, "", "exit_code"], [5, 5, 1, "", "show"]], "hfutils.entry.base.KeyboardInterrupted": [[5, 5, 1, "", "__init__"], [5, 4, 1, "", "exit_code"], [5, 5, 1, "", "show"]], "hfutils.entry.cli": [[6, 2, 1, "", "cli"]], "hfutils.entry.dispatch": [[7, 1, 1, "", "hfutilcli"], [7, 1, 1, "", "print_version"]], "hfutils.entry.download": [[8, 3, 1, "", "NoRemotePathAssignedWithDownload"]], "hfutils.entry.download.NoRemotePathAssignedWithDownload": [[8, 4, 1, "", "exit_code"], [8, 5, 1, "", "show"]], "hfutils.entry.ls": [[10, 3, 1, "", "ListItem"], [10, 6, 1, "", "ListItemType"]], "hfutils.entry.ls.ListItemType": [[10, 4, 1, "", "ARCHIVE"], [10, 4, 1, "", "DATA"], [10, 4, 1, "", "FILE"], [10, 4, 1, "", "FOLDER"], [10, 4, 1, "", "IMAGE"], [10, 4, 1, "", "MODEL"]], "hfutils.entry.ls_repo": [[11, 3, 1, "", "NoLocalAuthentication"]], "hfutils.entry.upload": [[12, 3, 1, "", "NoRemotePathAssignedWithUpload"]], "hfutils.entry.upload.NoRemotePathAssignedWithUpload": [[12, 4, 1, "", "exit_code"], [12, 5, 1, "", "show"]], "hfutils.index": [[14, 0, 0, "-", "fetch"], [16, 0, 0, "-", "make"], [17, 0, 0, "-", "validate"]], "hfutils.index.fetch": [[14, 3, 1, "", "ArchiveStandaloneFileHashNotMatch"], [14, 3, 1, "", "ArchiveStandaloneFileIncompleteDownload"], [14, 1, 1, "", "hf_tar_file_download"], [14, 1, 1, "", "hf_tar_file_exists"], [14, 1, 1, "", "hf_tar_file_info"], [14, 1, 1, "", "hf_tar_file_size"], [14, 1, 1, "", "hf_tar_get_index"], [14, 1, 1, "", "hf_tar_list_files"]], "hfutils.index.make": [[16, 1, 1, "", "hf_tar_create_from_directory"], [16, 1, 1, "", "hf_tar_create_index"], [16, 1, 1, "", "tar_create_index"], [16, 1, 1, "", "tar_get_index_info"]], "hfutils.index.validate": [[17, 1, 1, "", "hf_tar_item_validate"], [17, 1, 1, "", "hf_tar_validate"]], "hfutils.operate": [[18, 0, 0, "-", "base"], [19, 0, 0, "-", "download"], [21, 0, 0, "-", "upload"], [22, 0, 0, "-", "validate"]], "hfutils.operate.base": [[18, 1, 1, "", "get_hf_client"], [18, 1, 1, "", "get_hf_fs"], [18, 1, 1, "", "list_files_in_repository"]], "hfutils.operate.download": [[19, 1, 1, "", "download_archive_as_directory"], [19, 1, 1, "", "download_directory_as_directory"], [19, 1, 1, "", "download_file_to_file"]], "hfutils.operate.upload": [[21, 1, 1, "", "upload_directory_as_archive"], [21, 1, 1, "", "upload_directory_as_directory"], [21, 1, 1, "", "upload_file_to_file"]], "hfutils.operate.validate": [[22, 1, 1, "", "is_local_file_ready"]], "hfutils.utils": [[23, 0, 0, "-", "binary"], [24, 0, 0, "-", "download"], [26, 0, 0, "-", "path"], [27, 0, 0, "-", "tqdm_"], [28, 0, 0, "-", "walk"]], "hfutils.utils.binary": [[23, 1, 1, "", "is_binary_file"]], "hfutils.utils.download": [[24, 1, 1, "", "download_file"]], "hfutils.utils.path": [[26, 3, 1, "", "HfFileSystemPath"], [26, 1, 1, "", "hf_fs_path"], [26, 1, 1, "", "hf_normpath"], [26, 1, 1, "", "parse_hf_fs_path"]], "hfutils.utils.tqdm_": [[27, 1, 1, "", "tqdm"]], "hfutils.utils.walk": [[28, 1, 1, "", "walk_files"]]}, "objtypes": {"0": "py:module", "1": "py:function", "2": "py:data", "3": "py:class", "4": "py:attribute", "5": "py:method", "6": "py:enum"}, "objnames": {"0": ["py", "module", "Python module"], "1": ["py", "function", "Python function"], "2": ["py", "data", "Python data"], "3": ["py", "class", "Python class"], "4": ["py", "attribute", "Python attribute"], "5": ["py", "method", "Python method"], "6": ["py", "enum", "Python enum"]}, "titleterms": {"hfutil": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29], "archiv": 0, "register_archive_typ": 0, "archive_pack": 0, "archive_unpack": 0, "get_archive_typ": 0, "get_archive_extnam": 0, "cach": [1, 2], "delet": 1, "delete_detached_cach": 1, "delete_cach": 1, "config": [3, 4], "meta": 4, "__title__": 4, "__version__": 4, "__description__": 4, "__author__": 4, "__author_email__": 4, "entri": [5, 6, 7, 8, 9, 10, 11, 12, 13], "base": [5, 18], "context_set": 5, "clickwarningexcept": 5, "clickerrorexcept": 5, "print_except": 5, "keyboardinterrupt": 5, "command_wrap": 5, "cli": 6, "dispatch": 7, "print_vers": 7, "hfutilcli": 7, "download": [8, 19, 24], "noremotepathassignedwithdownload": 8, "l": 10, "listitemtyp": 10, "listitem": 10, "ls_repo": 11, "nolocalauthent": 11, "upload": [12, 21], "noremotepathassignedwithupload": 12, "whoami": 13, "index": [14, 15, 16, 17], "fetch": 14, "archivestandalonefileincompletedownload": 14, "archivestandalonefilehashnotmatch": 14, "hf_tar_get_index": 14, "hf_tar_list_fil": 14, "hf_tar_file_exist": 14, "hf_tar_file_s": 14, "hf_tar_file_info": 14, "hf_tar_file_download": 14, "make": 16, "tar_create_index": 16, "hf_tar_create_index": 16, "tar_get_index_info": 16, "hf_tar_create_from_directori": 16, "valid": [17, 22], "hf_tar_item_valid": 17, "hf_tar_valid": 17, "oper": [18, 19, 20, 21, 22], "get_hf_client": 18, "get_hf_f": 18, "list_files_in_repositori": 18, "download_file_to_fil": 19, "download_archive_as_directori": 19, "download_directory_as_directori": 19, "upload_file_to_fil": 21, "upload_directory_as_arch": 21, "upload_directory_as_directori": 21, "is_local_file_readi": 22, "util": [23, 24, 25, 26, 27, 28], "binari": 23, "is_binary_fil": 23, "download_fil": 24, "path": 26, "hf_normpath": 26, "hf_fs_path": 26, "parse_hf_fs_path": 26, "hffilesystempath": 26, "tqdm": 27, "walk": 28, "walk_fil": 28, "welcom": 29, "": 29, "document": 29, "overview": 29, "tutori": 29, "inform": [29, 30, 31], "api": 29, "run": [30, 31], "environ": [30, 31], "instal": 32, "quick": 33, "start": 33}, "envversion": {"sphinx.domains.c": 3, "sphinx.domains.changeset": 1, "sphinx.domains.citation": 1, "sphinx.domains.cpp": 9, "sphinx.domains.index": 1, "sphinx.domains.javascript": 3, "sphinx.domains.math": 2, "sphinx.domains.python": 4, "sphinx.domains.rst": 2, "sphinx.domains.std": 2, "sphinx.ext.viewcode": 1, "sphinx.ext.todo": 2, "nbsphinx": 4, "sphinx": 58}, "alltitles": {"hfutils.archive": [[0, "module-hfutils.archive"]], "register_archive_type": [[0, "register-archive-type"]], "archive_pack": [[0, "archive-pack"]], "archive_unpack": [[0, "archive-unpack"]], "get_archive_type": [[0, "get-archive-type"]], "get_archive_extname": [[0, "get-archive-extname"]], "hfutils.cache.delete": [[1, "module-hfutils.cache.delete"]], "delete_detached_cache": [[1, "delete-detached-cache"]], "delete_cache": [[1, "delete-cache"]], "hfutils.cache": [[2, "module-hfutils.cache"]], "hfutils.config": [[3, "module-hfutils.config"]], "hfutils.config.meta": [[4, "module-hfutils.config.meta"]], "__TITLE__": [[4, "title"]], "__VERSION__": [[4, "version"]], "__DESCRIPTION__": [[4, "description"]], "__AUTHOR__": [[4, "author"]], "__AUTHOR_EMAIL__": [[4, "author-email"]], "hfutils.entry.base": [[5, "module-hfutils.entry.base"]], "CONTEXT_SETTINGS": [[5, "context-settings"]], "ClickWarningException": [[5, "clickwarningexception"]], "ClickErrorException": [[5, "clickerrorexception"]], "print_exception": [[5, "print-exception"]], "KeyboardInterrupted": [[5, "keyboardinterrupted"]], "command_wrap": [[5, "command-wrap"]], "hfutils.entry.cli": [[6, "module-hfutils.entry.cli"]], "cli": [[6, "cli"]], "hfutils.entry.dispatch": [[7, "module-hfutils.entry.dispatch"]], "print_version": [[7, "print-version"]], "hfutilcli": [[7, "hfutilcli"]], "hfutils.entry.download": [[8, "module-hfutils.entry.download"]], "NoRemotePathAssignedWithDownload": [[8, "noremotepathassignedwithdownload"]], "hfutils.entry": [[9, "module-hfutils.entry"]], "hfutils.entry.ls": [[10, "module-hfutils.entry.ls"]], "ListItemType": [[10, "listitemtype"]], "ListItem": [[10, "listitem"]], "hfutils.entry.ls_repo": [[11, "module-hfutils.entry.ls_repo"]], "NoLocalAuthentication": [[11, "nolocalauthentication"]], "hfutils.entry.upload": [[12, "module-hfutils.entry.upload"]], "NoRemotePathAssignedWithUpload": [[12, "noremotepathassignedwithupload"]], "hfutils.entry.whoami": [[13, "module-hfutils.entry.whoami"]], "hfutils.index.fetch": [[14, "module-hfutils.index.fetch"]], "ArchiveStandaloneFileIncompleteDownload": [[14, "archivestandalonefileincompletedownload"]], "ArchiveStandaloneFileHashNotMatch": [[14, "archivestandalonefilehashnotmatch"]], "hf_tar_get_index": [[14, "hf-tar-get-index"]], "hf_tar_list_files": [[14, "hf-tar-list-files"]], "hf_tar_file_exists": [[14, "hf-tar-file-exists"]], "hf_tar_file_size": [[14, "hf-tar-file-size"]], "hf_tar_file_info": [[14, "hf-tar-file-info"]], "hf_tar_file_download": [[14, "hf-tar-file-download"]], "hfutils.index": [[15, "module-hfutils.index"]], "hfutils.index.make": [[16, "module-hfutils.index.make"]], "tar_create_index": [[16, "tar-create-index"]], "hf_tar_create_index": [[16, "hf-tar-create-index"]], "tar_get_index_info": [[16, "tar-get-index-info"]], "hf_tar_create_from_directory": [[16, "hf-tar-create-from-directory"]], "hfutils.index.validate": [[17, "module-hfutils.index.validate"]], "hf_tar_item_validate": [[17, "hf-tar-item-validate"]], "hf_tar_validate": [[17, "hf-tar-validate"]], "hfutils.operate.base": [[18, "module-hfutils.operate.base"]], "get_hf_client": [[18, "get-hf-client"]], "get_hf_fs": [[18, "get-hf-fs"]], "list_files_in_repository": [[18, "list-files-in-repository"]], "hfutils.operate.download": [[19, "module-hfutils.operate.download"]], "download_file_to_file": [[19, "download-file-to-file"]], "download_archive_as_directory": [[19, "download-archive-as-directory"]], "download_directory_as_directory": [[19, "download-directory-as-directory"]], "hfutils.operate": [[20, "module-hfutils.operate"]], "hfutils.operate.upload": [[21, "module-hfutils.operate.upload"]], "upload_file_to_file": [[21, "upload-file-to-file"]], "upload_directory_as_archive": [[21, "upload-directory-as-archive"]], "upload_directory_as_directory": [[21, "upload-directory-as-directory"]], "hfutils.operate.validate": [[22, "module-hfutils.operate.validate"]], "is_local_file_ready": [[22, "is-local-file-ready"]], "hfutils.utils.binary": [[23, "module-hfutils.utils.binary"]], "is_binary_file": [[23, "is-binary-file"]], "hfutils.utils.download": [[24, "module-hfutils.utils.download"]], "download_file": [[24, "download-file"]], "hfutils.utils": [[25, "module-hfutils.utils"]], "hfutils.utils.path": [[26, "module-hfutils.utils.path"]], "hf_normpath": [[26, "hf-normpath"]], "hf_fs_path": [[26, "hf-fs-path"]], "parse_hf_fs_path": [[26, "parse-hf-fs-path"]], "HfFileSystemPath": [[26, "hffilesystempath"]], "hfutils.utils.tqdm": [[27, "module-hfutils.utils.tqdm_"]], "tqdm": [[27, "tqdm"]], "hfutils.utils.walk": [[28, "module-hfutils.utils.walk"]], "walk_files": [[28, "walk-files"]], "Welcome to hfutils\u2019s Documentation": [[29, "welcome-to-hfutils-s-documentation"]], "Overview": [[29, "overview"]], "Tutorials": [[29, null]], "Information": [[29, null]], "API Documentation": [[29, null]], "Run Environment Information": [[30, "Run-Environment-Information"], [31, "Run-Environment-Information"]], "Installation": [[32, "installation"]], "Quick Start": [[33, "quick-start"]]}, "indexentries": {"archive_pack() (in module hfutils.archive)": [[0, "hfutils.archive.archive_pack"]], "archive_unpack() (in module hfutils.archive)": [[0, "hfutils.archive.archive_unpack"]], "get_archive_extname() (in module hfutils.archive)": [[0, "hfutils.archive.get_archive_extname"]], "get_archive_type() (in module hfutils.archive)": [[0, "hfutils.archive.get_archive_type"]], "hfutils.archive": [[0, "module-hfutils.archive"]], "module": [[0, "module-hfutils.archive"], [1, "module-hfutils.cache.delete"], [2, "module-hfutils.cache"], [3, "module-hfutils.config"], [4, "module-hfutils.config.meta"], [5, "module-hfutils.entry.base"], [6, "module-hfutils.entry.cli"], [7, "module-hfutils.entry.dispatch"], [8, "module-hfutils.entry.download"], [9, "module-hfutils.entry"], [10, "module-hfutils.entry.ls"], [11, "module-hfutils.entry.ls_repo"], [12, "module-hfutils.entry.upload"], [13, "module-hfutils.entry.whoami"], [14, "module-hfutils.index.fetch"], [15, "module-hfutils.index"], [16, "module-hfutils.index.make"], [17, "module-hfutils.index.validate"], [18, "module-hfutils.operate.base"], [19, "module-hfutils.operate.download"], [20, "module-hfutils.operate"], [21, "module-hfutils.operate.upload"], [22, "module-hfutils.operate.validate"], [23, "module-hfutils.utils.binary"], [24, "module-hfutils.utils.download"], [25, "module-hfutils.utils"], [26, "module-hfutils.utils.path"], [27, "module-hfutils.utils.tqdm_"], [28, "module-hfutils.utils.walk"]], "register_archive_type() (in module hfutils.archive)": [[0, "hfutils.archive.register_archive_type"]], "delete_cache() (in module hfutils.cache.delete)": [[1, "hfutils.cache.delete.delete_cache"]], "delete_detached_cache() (in module hfutils.cache.delete)": [[1, "hfutils.cache.delete.delete_detached_cache"]], "hfutils.cache.delete": [[1, "module-hfutils.cache.delete"]], "hfutils.cache": [[2, "module-hfutils.cache"]], "hfutils.config": [[3, "module-hfutils.config"]], "__author_email__ (in module hfutils.config.meta)": [[4, "hfutils.config.meta.__AUTHOR_EMAIL__"]], "__author__ (in module hfutils.config.meta)": [[4, "hfutils.config.meta.__AUTHOR__"]], "__description__ (in module hfutils.config.meta)": [[4, "hfutils.config.meta.__DESCRIPTION__"]], "__title__ (in module hfutils.config.meta)": [[4, "hfutils.config.meta.__TITLE__"]], "__version__ (in module hfutils.config.meta)": [[4, "hfutils.config.meta.__VERSION__"]], "hfutils.config.meta": [[4, "module-hfutils.config.meta"]], "context_settings (in module hfutils.entry.base)": [[5, "hfutils.entry.base.CONTEXT_SETTINGS"]], "clickerrorexception (class in hfutils.entry.base)": [[5, "hfutils.entry.base.ClickErrorException"]], "clickwarningexception (class in hfutils.entry.base)": [[5, "hfutils.entry.base.ClickWarningException"]], "keyboardinterrupted (class in hfutils.entry.base)": [[5, "hfutils.entry.base.KeyboardInterrupted"]], "__init__() (hfutils.entry.base.keyboardinterrupted method)": [[5, "hfutils.entry.base.KeyboardInterrupted.__init__"]], "command_wrap() (in module hfutils.entry.base)": [[5, "hfutils.entry.base.command_wrap"]], "exit_code (hfutils.entry.base.clickerrorexception attribute)": [[5, "hfutils.entry.base.ClickErrorException.exit_code"]], "exit_code (hfutils.entry.base.clickwarningexception attribute)": [[5, "hfutils.entry.base.ClickWarningException.exit_code"]], "exit_code (hfutils.entry.base.keyboardinterrupted attribute)": [[5, "hfutils.entry.base.KeyboardInterrupted.exit_code"]], "hfutils.entry.base": [[5, "module-hfutils.entry.base"]], "print_exception() (in module hfutils.entry.base)": [[5, "hfutils.entry.base.print_exception"]], "show() (hfutils.entry.base.clickerrorexception method)": [[5, "hfutils.entry.base.ClickErrorException.show"]], "show() (hfutils.entry.base.clickwarningexception method)": [[5, "hfutils.entry.base.ClickWarningException.show"]], "show() (hfutils.entry.base.keyboardinterrupted method)": [[5, "hfutils.entry.base.KeyboardInterrupted.show"]], "cli (in module hfutils.entry.cli)": [[6, "hfutils.entry.cli.cli"]], "hfutils.entry.cli": [[6, "module-hfutils.entry.cli"]], "hfutilcli() (in module hfutils.entry.dispatch)": [[7, "hfutils.entry.dispatch.hfutilcli"]], "hfutils.entry.dispatch": [[7, "module-hfutils.entry.dispatch"]], "print_version() (in module hfutils.entry.dispatch)": [[7, "hfutils.entry.dispatch.print_version"]], "noremotepathassignedwithdownload (class in hfutils.entry.download)": [[8, "hfutils.entry.download.NoRemotePathAssignedWithDownload"]], "exit_code (hfutils.entry.download.noremotepathassignedwithdownload attribute)": [[8, "hfutils.entry.download.NoRemotePathAssignedWithDownload.exit_code"]], "hfutils.entry.download": [[8, "module-hfutils.entry.download"]], "show() (hfutils.entry.download.noremotepathassignedwithdownload method)": [[8, "hfutils.entry.download.NoRemotePathAssignedWithDownload.show"]], "hfutils.entry": [[9, "module-hfutils.entry"]], "archive (hfutils.entry.ls.listitemtype attribute)": [[10, "hfutils.entry.ls.ListItemType.ARCHIVE"]], "data (hfutils.entry.ls.listitemtype attribute)": [[10, "hfutils.entry.ls.ListItemType.DATA"]], "file (hfutils.entry.ls.listitemtype attribute)": [[10, "hfutils.entry.ls.ListItemType.FILE"]], "folder (hfutils.entry.ls.listitemtype attribute)": [[10, "hfutils.entry.ls.ListItemType.FOLDER"]], "image (hfutils.entry.ls.listitemtype attribute)": [[10, "hfutils.entry.ls.ListItemType.IMAGE"]], "listitem (class in hfutils.entry.ls)": [[10, "hfutils.entry.ls.ListItem"]], "model (hfutils.entry.ls.listitemtype attribute)": [[10, "hfutils.entry.ls.ListItemType.MODEL"]], "hfutils.entry.ls": [[10, "module-hfutils.entry.ls"]], "nolocalauthentication (class in hfutils.entry.ls_repo)": [[11, "hfutils.entry.ls_repo.NoLocalAuthentication"]], "hfutils.entry.ls_repo": [[11, "module-hfutils.entry.ls_repo"]], "noremotepathassignedwithupload (class in hfutils.entry.upload)": [[12, "hfutils.entry.upload.NoRemotePathAssignedWithUpload"]], "exit_code (hfutils.entry.upload.noremotepathassignedwithupload attribute)": [[12, "hfutils.entry.upload.NoRemotePathAssignedWithUpload.exit_code"]], "hfutils.entry.upload": [[12, "module-hfutils.entry.upload"]], "show() (hfutils.entry.upload.noremotepathassignedwithupload method)": [[12, "hfutils.entry.upload.NoRemotePathAssignedWithUpload.show"]], "hfutils.entry.whoami": [[13, "module-hfutils.entry.whoami"]], "archivestandalonefilehashnotmatch (class in hfutils.index.fetch)": [[14, "hfutils.index.fetch.ArchiveStandaloneFileHashNotMatch"]], "archivestandalonefileincompletedownload (class in hfutils.index.fetch)": [[14, "hfutils.index.fetch.ArchiveStandaloneFileIncompleteDownload"]], "hf_tar_file_download() (in module hfutils.index.fetch)": [[14, "hfutils.index.fetch.hf_tar_file_download"]], "hf_tar_file_exists() (in module hfutils.index.fetch)": [[14, "hfutils.index.fetch.hf_tar_file_exists"]], "hf_tar_file_info() (in module hfutils.index.fetch)": [[14, "hfutils.index.fetch.hf_tar_file_info"]], "hf_tar_file_size() (in module hfutils.index.fetch)": [[14, "hfutils.index.fetch.hf_tar_file_size"]], "hf_tar_get_index() (in module hfutils.index.fetch)": [[14, "hfutils.index.fetch.hf_tar_get_index"]], "hf_tar_list_files() (in module hfutils.index.fetch)": [[14, "hfutils.index.fetch.hf_tar_list_files"]], "hfutils.index.fetch": [[14, "module-hfutils.index.fetch"]], "hfutils.index": [[15, "module-hfutils.index"]], "hf_tar_create_from_directory() (in module hfutils.index.make)": [[16, "hfutils.index.make.hf_tar_create_from_directory"]], "hf_tar_create_index() (in module hfutils.index.make)": [[16, "hfutils.index.make.hf_tar_create_index"]], "hfutils.index.make": [[16, "module-hfutils.index.make"]], "tar_create_index() (in module hfutils.index.make)": [[16, "hfutils.index.make.tar_create_index"]], "tar_get_index_info() (in module hfutils.index.make)": [[16, "hfutils.index.make.tar_get_index_info"]], "hf_tar_item_validate() (in module hfutils.index.validate)": [[17, "hfutils.index.validate.hf_tar_item_validate"]], "hf_tar_validate() (in module hfutils.index.validate)": [[17, "hfutils.index.validate.hf_tar_validate"]], "hfutils.index.validate": [[17, "module-hfutils.index.validate"]], "get_hf_client() (in module hfutils.operate.base)": [[18, "hfutils.operate.base.get_hf_client"]], "get_hf_fs() (in module hfutils.operate.base)": [[18, "hfutils.operate.base.get_hf_fs"]], "hfutils.operate.base": [[18, "module-hfutils.operate.base"]], "list_files_in_repository() (in module hfutils.operate.base)": [[18, "hfutils.operate.base.list_files_in_repository"]], "download_archive_as_directory() (in module hfutils.operate.download)": [[19, "hfutils.operate.download.download_archive_as_directory"]], "download_directory_as_directory() (in module hfutils.operate.download)": [[19, "hfutils.operate.download.download_directory_as_directory"]], "download_file_to_file() (in module hfutils.operate.download)": [[19, "hfutils.operate.download.download_file_to_file"]], "hfutils.operate.download": [[19, "module-hfutils.operate.download"]], "hfutils.operate": [[20, "module-hfutils.operate"]], "hfutils.operate.upload": [[21, "module-hfutils.operate.upload"]], "upload_directory_as_archive() (in module hfutils.operate.upload)": [[21, "hfutils.operate.upload.upload_directory_as_archive"]], "upload_directory_as_directory() (in module hfutils.operate.upload)": [[21, "hfutils.operate.upload.upload_directory_as_directory"]], "upload_file_to_file() (in module hfutils.operate.upload)": [[21, "hfutils.operate.upload.upload_file_to_file"]], "hfutils.operate.validate": [[22, "module-hfutils.operate.validate"]], "is_local_file_ready() (in module hfutils.operate.validate)": [[22, "hfutils.operate.validate.is_local_file_ready"]], "hfutils.utils.binary": [[23, "module-hfutils.utils.binary"]], "is_binary_file() (in module hfutils.utils.binary)": [[23, "hfutils.utils.binary.is_binary_file"]], "download_file() (in module hfutils.utils.download)": [[24, "hfutils.utils.download.download_file"]], "hfutils.utils.download": [[24, "module-hfutils.utils.download"]], "hfutils.utils": [[25, "module-hfutils.utils"]], "hffilesystempath (class in hfutils.utils.path)": [[26, "hfutils.utils.path.HfFileSystemPath"]], "hf_fs_path() (in module hfutils.utils.path)": [[26, "hfutils.utils.path.hf_fs_path"]], "hf_normpath() (in module hfutils.utils.path)": [[26, "hfutils.utils.path.hf_normpath"]], "hfutils.utils.path": [[26, "module-hfutils.utils.path"]], "parse_hf_fs_path() (in module hfutils.utils.path)": [[26, "hfutils.utils.path.parse_hf_fs_path"]], "hfutils.utils.tqdm_": [[27, "module-hfutils.utils.tqdm_"]], "tqdm() (in module hfutils.utils.tqdm_)": [[27, "hfutils.utils.tqdm_.tqdm"]], "hfutils.utils.walk": [[28, "module-hfutils.utils.walk"]], "walk_files() (in module hfutils.utils.walk)": [[28, "hfutils.utils.walk.walk_files"]]}})