import json
import logging
import os.path

from hbutils.string import plural_word
from natsort import natsorted

from hfutils.operate import get_hf_client
from hfutils.utils import tqdm


def main():
    hf_client = get_hf_client()

    logging.info('Scanning datasets')
    ir_datasets = []
    for item in tqdm(hf_client.list_datasets(), desc='Hf Datasets'):
        if item.id.count('/') != 1:
            ir_datasets.append(item.id)
    ir_datasets = natsorted(set(ir_datasets))
    logging.info(f'{plural_word(len(ir_datasets), "irregular dataset")} found.')

    ir_models = []
    for item in tqdm(hf_client.list_models(), desc='Hf Models'):
        if item.id.count('/') != 1:
            ir_models.append(item.id)
    ir_models = natsorted(set(ir_models))
    logging.info(f'{plural_word(len(ir_models), "irregular model")} found.')

    ir_spaces = []
    for item in tqdm(hf_client.list_spaces(), desc='Hf Spaces'):
        if item.id.count('/') != 1:
            ir_spaces.append(item.id)
    ir_spaces = natsorted(set(ir_spaces))
    logging.info(f'{plural_word(len(ir_spaces), "irregular space")} found.')

    target = os.path.join('hfutils', 'utils', 'irregular_repo.json')
    logging.info(f'Saving to {target!r} ...')
    with open(target, 'w') as f:
        json.dump({
            'datasets': ir_datasets,
            'models': ir_models,
            'spaces': ir_spaces,
        }, f, sort_keys=True, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
