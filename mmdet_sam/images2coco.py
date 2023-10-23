# Copyright (c) OpenMMLab. All rights reserved.
import argparse
import os

from mmengine.fileio import dump, list_from_file
from mmengine.utils import mkdir_or_exist, scandir, track_iter_progress
from PIL import Image


def parse_args():
    parser = argparse.ArgumentParser(
        description='Convert images to coco format without annotations')
    parser.add_argument('img_path', help='The root path of images')
    parser.add_argument(
        'classes', type=str, help='The text file name of storage class list')
    parser.add_argument(
        'out',
        type=str,
        help='The output annotation json file name, The save dir is in the '
        'same directory as img_path')
    parser.add_argument(
        '-e',
        '--exclude-extensions',
        type=str,
        nargs='+',
        help='The suffix of images to be excluded, such as "png" and "bmp"')
    return parser.parse_args()


def collect_image_infos(path, exclude_extensions=None):
    img_infos = []

    images_generator = scandir(path, recursive=True)
    for image_path in track_iter_progress(list(images_generator)):
        if exclude_extensions is None or (
                exclude_extensions is not None
                and not image_path.lower().endswith(exclude_extensions)):
            full_image_path = os.path.join(path, image_path)
            img_pillow = Image.open(full_image_path)
            img_info = {
                'filename': image_path,
                'width': img_pillow.width,
                'height': img_pillow.height,
            }
            img_infos.append(img_info)
    return img_infos


def cvt_to_coco_json(img_infos, classes):
    coco = dict()
    coco['images'] = []
    coco['type'] = 'instance'
    coco['categories'] = []
    coco['annotations'] = []
    coco['info'] = []
    coco['licenses'] = []
    image_set = set()

    for category_id, name in enumerate(classes):
        category_item = dict()
        category_item['supercategory'] = 'none'
        category_item['id'] = int(category_id)
        category_item['name'] = str(name)
        coco['categories'].append(category_item)

    for image_id, img_dict in enumerate(img_infos):
        file_name = img_dict['filename']
        assert file_name not in image_set
        image_item = dict()
        image_item['id'] = int(image_id)
        image_item['file_name'] = str(file_name)
        image_item['height'] = int(img_dict['height'])
        image_item['width'] = int(img_dict['width'])
        coco['images'].append(image_item)
        image_set.add(file_name)

    return coco


def main():
    args = parse_args()
    assert args.out.endswith(
        'json'), 'The output file name must be json suffix'

    # 1 load image list info
    img_infos = collect_image_infos(args.img_path, args.exclude_extensions)

    # 2 convert to coco format data
    classes = list_from_file(args.classes)
    coco_info = cvt_to_coco_json(img_infos, classes)

    # 3 dump
    save_dir = os.path.join(args.img_path, '..', 'annotations')
    mkdir_or_exist(save_dir)
    save_path = os.path.join(save_dir, args.out)
    dump(coco_info, save_path)
    print(f'save json file: {save_path}')


if __name__ == '__main__':
    main()
