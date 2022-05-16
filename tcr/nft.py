#
# Copyright 2021-2022 The Card Room
#
# MIT License:
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is furnished
# to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
File: nft.py
Author: SuperKK
"""

from typing import Dict, List
import json
import os
import time
import random
from tcr.command import Command
import logging
import hashlib
import numpy

from PIL import Image

logger = logging.getLogger('nft')

class Nft:
    @staticmethod
    def parse_metadata_file(metadata_file: str) -> Dict:
        """
        Parse a NFT metadata file.  The metadata file can define a single asset
        or multiple assets.

        The returned dictionary will look like this:
        {
            'policy-id': 'the-policy-id,
            'token-names': ['tname1', 'tname2', ..., 'tnamen'],
            'properties': {
                'tname1': {...},
                'tname2': {...},
                'tnamen': {...}
            }
        }

        """
        metadata = {}
        with open(metadata_file, 'r') as file:
            raw_md = json.load(file)
            if '721' in raw_md:
                policy_id = list(raw_md['721'].keys())[0]
                token_names = list(raw_md['721'][policy_id].keys())
                metadata['policy-id'] = policy_id
                metadata['token-names'] = token_names
                metadata['properties'] = {}
                for token_name in token_names:
                    metadata['properties'][token_name] = raw_md['721'][policy_id][token_name]
            elif '777' in raw_md:
                metadata['policy-id'] = '777'
                metadata['token-names'] = ['']
                metadata['properties'] = {'': {}}

        return metadata

    @staticmethod
    def merge_metadata_files(policy_id: str, nft_metadata_files: List[str]) -> str:
        directory = os.path.dirname(nft_metadata_files[0])
        merged_file = os.path.join(directory, 'nft_merged_metadata_{}.json'.format(round(time.time())))

        nft_merged_metadata = {}
        nft_merged_metadata['721'] = {}
        nft_merged_metadata['721'][policy_id] = {}
        for fname in nft_metadata_files:
            nftmd = Nft.parse_metadata_file(fname)
            token_name = nftmd['token-names'][0]
            nft_merged_metadata['721'][policy_id][token_name] = nftmd['properties'][token_name]

        with open(merged_file, 'w') as file:
            file.write(json.dumps(nft_merged_metadata, indent=4))

        return merged_file

    @staticmethod
    def create_metadata(network: str,
                        policy_id: str,
                        drop_name: str,
                        token_name: str,
                        nft_name: str,
                        mdin: Dict) -> str:
        """
        Write JSON metadata according to the Cardano NFT metadata format proposal.

        Test the output at https://pool.pm/test/metadata
        """

        md_dir = 'nft/{}/{}/nft_metadata'.format(network, drop_name)
        metadata_file = '{}/{}.json'.format(md_dir, token_name)

        if not os.path.exists(md_dir):
            os.makedirs(md_dir)

        metadata = {}
        metadata["721"] = {}
        metadata["721"][policy_id] = {}
        metadata["721"][policy_id][token_name] = {}
        metadata["721"][policy_id][token_name]["name"] = nft_name
        if 'image' in mdin:
            metadata["721"][policy_id][token_name]["image"] = mdin['image']
        if 'description' in mdin:
            metadata["721"][policy_id][token_name]["description"] = mdin['description']

        for key in mdin['properties']:
            metadata["721"][policy_id][token_name][key] = mdin['properties'][key]

        with open(metadata_file, 'w') as file:
            file.write(json.dumps(metadata, indent=4))

        return metadata_file

    @staticmethod
    def create_card_metadata_set(network: str,
                                 policy_id: str,
                                 series_name: str,
                                 base_nft_id: int,
                                 token_name: str,
                                 nft_name: str,
                                 metadata: Dict) -> List[str]:
        count = metadata['count']
        fnames = []
        for i in range(0, count):
            if 'id' in metadata['properties']:
                metadata['properties']['id'] = base_nft_id + i

            if 'code' in metadata['properties']:
                metadata['properties']['code'] = random.randint(0, 0xFFFFFFFF)

            fname = Nft.create_metadata(network,
                                        policy_id,
                                        series_name,
                                        token_name.format(i+1),
                                        nft_name.format(i+1),
                                        metadata)
            fnames.append(fname)
        return fnames

    @staticmethod
    def count_layer_options(dir: str, file: str):
        num_options = 0
        with open(os.path.join(dir, file), 'r') as file:
            layer = json.load(file)
            num_options = len(layer['images'])

        return num_options

    @staticmethod
    def verify_layer_images(dir: str, file: str):
        layer = {}
        with open(os.path.join(dir, file), 'r') as file:
            layer = json.load(file)

        width = layer['width']
        height = layer['height']
        total_weight = 0
        for image in layer['images']:
            total_weight += image['weight']
            if image['image'] == None:
                continue

            im = Image.open(os.path.join(dir, image['image']))
            (imwidth, imheight) = im.size
            if width != imwidth or height != imheight:
                logger.error('{} != {} x {}'.format(image['image'], width, height))
                raise Exception('{} != {} x {}'.format(image['image'], width, height))

        if abs(100 - total_weight) > 0.0001:
            logger.error('{} weight: {}, must equal 100'.format(layer['name'], total_weight))
            raise Exception('{} weight: {}, must equal 100'.format(layer['name'], total_weight))

    @staticmethod
    def calculate_total_combinations(metametadata: Dict):
        total = 0
        layer_sets = metametadata['layer-sets']
        layer_set_weight = 0
        dir = os.path.dirname(os.path.abspath(metametadata['self']))
        for layer_set in layer_sets:
            layer_set_file = os.path.join(dir, layer_set['file'])
            with open(layer_set_file, 'r') as file:
                logger.info("Opening Layer Set: {}".format(layer_set['file']))
                layers = json.load(file)

            layer_set_weight += layer_set['weight']
            combos = 1

            for layer in layers['layers']:
                combos = combos * Nft.count_layer_options(dir, layer)
                Nft.verify_layer_images(dir, layer)

            logger.info('{} = {}'.format(layer_set['file'], combos))
            total += combos

        if layer_set_weight != 100:
            logger.error('Layer Set weight {} != 100'.format(layer_set_weight))
            raise Exception('Layer Set weight {} != 100'.format(layer_set_weight))

        return total

    @staticmethod
    def calc_sha256(filepath) :
        BLOCKSIZE = 65536
        hasher = hashlib.sha256()
        with open(filepath, 'rb') as afile:
            buf = afile.read(BLOCKSIZE)
            while len(buf) > 0:
                hasher.update(buf)
                buf = afile.read(BLOCKSIZE)
        return hasher.hexdigest()

    @staticmethod
    def create_cards_set(network: str,
                         policy_id: str,
                         metametadata: Dict,
                         rng: numpy.random.RandomState) -> List[str]:
        series = metametadata['series']
        drop_name = metametadata['drop-name']
        init_nft_id = metametadata['init-nft-id']
        base_token_name = metametadata['token-name']
        base_nft_name = metametadata['nft-name']

        card_lists = []
        total = 0
        for card in metametadata['cards']:
            token_name = base_token_name.format(series, card['id'], '{:03}')
            nft_name = base_nft_name.format(series, card['id'], '{}', card['count'])
            files = Nft.create_card_metadata_set(network,
                                                    policy_id,
                                                    drop_name,
                                                    init_nft_id,
                                                    token_name,
                                                    nft_name,
                                                    card)
            card_lists.append(files)
            total += card['count']
            init_nft_id += card['count']

        fnames = []
        while total > 0:
            num = rng.randint(0, total)
            for l in card_lists:
                if num > len(l):
                    num -= len(l)
                elif len(l) > 0:
                    item = l.pop(0)
                    fnames.append(item)
                    break
            total -=1

        return fnames

    @staticmethod
    def get_geometry(offset_x: int, offset_y: int) -> str:
        if offset_x >= 0:
            geometry = '+{}'.format(offset_x)
        else:
            geometry = '{}'.format(offset_x)

        if offset_y >= 0:
            geometry += '+{}'.format(offset_y)
        else:
            geometry += '{}'.format(offset_y)

        return geometry

    @staticmethod
    def get_random_object(rng: numpy.random.RandomState,
                          dir: str,
                          choices: Dict) -> Dict:
        sum = 0
        idx = 0
        num = rng.random() * 100
        for obj in choices:
            if num <= sum + obj['weight']:
                return (idx, obj)
            sum += obj['weight']
            idx += 1

        logger.error('Error selecting weighted object')
        raise Exception('Error selecting weighted object')

    @staticmethod
    def open_json(dir: str, file: str) -> Dict:
        data = None
        with open(os.path.join(dir, file), 'r') as file:
            data = json.load(file)

        if data == None:
            logger.error('Error opening: {}'.format(file))
            raise Exception('Error opening: {}'.format(file))

        return data

    @staticmethod
    def create_image(network: str, drop_name: str,
                     result_name: str, images: List, size: Dict) -> None:
        logger.info('Create: {}'.format(result_name))
        command = ['convert']
        for image in images:
            if 'offset-x' in image:
                if image['offset-x'] >= 0:
                    geometry = '+{}'.format(image['offset-x'])
                else:
                    geometry = '{}'.format(image['offset-x'])
            else:
                geometry = '+0'

            if 'offset-y' in image:
                if image['offset-y'] >= 0:
                    geometry += '+{}'.format(image['offset-y'])
                else:
                    geometry += '{}'.format(image['offset-y'])
            else:
                geometry += '+0'

            if len(command) == 1:
                command.extend(['nft/{}/{}/{}'.format(network, drop_name, image['image']), '-geometry', geometry])
            else:
                command.extend(['nft/{}/{}/{}'.format(network, drop_name, image['image']), '-geometry', geometry, '-composite'])

        # Resize if requested in the metametadata
        if size != None:
            command.extend(['-resize', '{}x{}'.format(size['width'], size['height'])])

        # Set output name and run the command
        command.append(result_name)
        Command.run_generic(command)

        # Make sure it got created
        if not os.path.isfile(result_name):
            logger.error('File is missing: {}'.format(result_name))
            raise Exception('File is missing: {}'.format(result_name))

    @staticmethod
    def verify_image_unique(image_hashes: Dict, image_path: str):
        logger.info('Verify Unique: {}'.format(image_path))
        hash = Nft.calc_sha256(image_path)
        if hash in image_hashes:
            logger.error('Found Duplicate NFT Image: {} exists at {} for {}'.format(image_hashes[hash], hash, result_name))
            raise Exception('Found Duplicate NFT Image: {} exists at {} for {}'.format(image_hashes[hash], hash, result_name))
        image_hashes[hash] = image_path

    @staticmethod
    def create_random_drop_set(network: str,
                         policy_id: str,
                         metametadata: Dict,
                         rng: numpy.random.RandomState) -> List[str]:
        series = metametadata['series']
        drop_name = metametadata['drop-name']
        init_nft_id = metametadata['init-nft-id']
        base_token_name = metametadata['token-name']
        base_nft_name = metametadata['nft-name']

        image_hashes = {}
        image_names = {}

        total_combinations = Nft.calculate_total_combinations(metametadata)
        logger.info('Total Combinations: {} images, Layer Sets: {} sets'.format(total_combinations, len(metametadata['layer-sets'])))
        logger.info('NFTs to generate: {}'.format(metametadata['total']))

        total_to_generate = metametadata['total']
        fnames = []

        dir = os.path.dirname(os.path.abspath(metametadata['self']))
        while len(fnames) < total_to_generate:
            images = []
            metadata = {}
            properties = {}

            logger.info('Created: {}'.format(len(fnames)))
            (layer_set_idx, layer_set) = Nft.get_random_object(rng, dir, metametadata['layer-sets'])
            layer_set_data = Nft.open_json(dir, layer_set['file'])

            card_number = len(fnames) + 1
            image_name = '{}_'.format(layer_set_data['name'])

            for layer in layer_set_data['layers']:
                layer_data = Nft.open_json(dir, layer)

                (img_idx, img_obj) = Nft.get_random_object(rng, dir, layer_data['images'])
                image_name = image_name + '_{}'.format(img_idx)
                if img_obj['image'] != None:
                    images.append(img_obj)

                # Add any metadata / properties associated with the image layer.
                # Later layers could override some properties from previous layers
                if 'properties' in img_obj:
                    layer_properties = img_obj['properties']
                    for k in layer_properties:
                        properties[k] = layer_properties[k]

            # Verify the image hasn't been created before
            if image_name in image_names:
                logger.info('Already exists, try again: {}'.format(image_name))
                continue

            # Create the nft image
            output_size = None
            if 'output-width' in metametadata and 'output-height' in metametadata:
                output_size = {'width': metametadata['output-width'],
                               'height': metametadata['output-height']}

            result_name = 'nft/{}/{}/nft_img/{:05}_'.format(network, drop_name, card_number)
            nft_image_path = result_name + image_name + '.jpg'
            Nft.create_image(network, drop_name, nft_image_path, images, output_size)
            Nft.verify_image_unique(image_hashes, nft_image_path)
            image_names[image_name] = True

            # Create the nft metadata
            metadata['image'] = nft_image_path
            if 'id' in properties:
                properties['id'] = init_nft_id + card_number - 1
            metadata['properties'] = properties
            token_name = base_token_name.format(series, card_number, 1)
            nft_name = base_nft_name.format(series, card_number, 1, 1)
            metadata_file = Nft.create_metadata(network,
                                                policy_id,
                                                drop_name,
                                                token_name,
                                                nft_name,
                                                metadata)

            fnames.append(metadata_file)

        return fnames

    @staticmethod
    def create_series_metadata_set(network: str,
                                   policy_id: str,
                                   metametadata: Dict,
                                   rng: numpy.random.RandomState) -> List[str]:
        if "cards" in metametadata:
            fnames = Nft.create_cards_set(network,
                                          policy_id,
                                          metametadata,
                                          rng)
        else:
            fnames = Nft.create_random_drop_set(network,
                                                policy_id,
                                                metametadata,
                                                rng)

        return fnames
