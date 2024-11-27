import pandas as pd

from hfutils.archive.base import _KNOWN_ARCHIVE_TYPES

if __name__ == '__main__':
    columns = ['Format', 'Extension Name']
    rows = []
    for key, (exts, _, _, _) in sorted(_KNOWN_ARCHIVE_TYPES.items()):
        rows.append((key, ', '.join(f'``{v}``' for v in exts)))

    df = pd.DataFrame(columns=columns, data=rows)
    print(df.to_markdown(headers='keys', tablefmt='rst', index=False))
