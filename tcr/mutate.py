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

from tcr.wallet import Wallet
from tcr.cardano import Cardano
from tcr.database import Database
from tcr.sales import Sales
import logging
import argparse
import tcr.command
import tcr.nftmint
import tcr.ipfs
import tcr.tcr
import traceback
import json
import requests
import urllib
import PIL.Image
import io
import os
import datetime
import shutil
import pathlib
import pymongo
import tcr.addresses
import http

CONNECTION_STRING = tcr.addresses.addresses['mongodb']
MINT_PAYMENT = 12000000

potency_lut = {
    'low': 1,
    'medium-low': 2,
    'medium': 3,
    'medium-high': 4,
    'high': 5,
}

runtime_lut = {
    'low': '20 iterations',
    'medium-low': '50 iterations',
    'medium': '100 iterations',
    'medium-high': '200 iterations',
    'high': '400 iterations',
}

resolution_lut = {
    'low': '2x',
    'medium-low': '4x',
    'medium': '4x',
    'medium-high': '6x',
    'high': '8x',
}

mutation_type_lut = {
    'mother of mutation': 'acid',
    'chin swingers': 'capsule',
    'chin swingers': 'pill',
    'overdose': 'combo',
    'psilocybin paranoia': 'shroom',

    'purple haze': 'acid',
    'disco biscuit': 'capsule',
    'disco biscuit': 'pill',
    'the pink panther': 'combo',
    'purple passion': 'shroom',

    'acid rain': 'acid',
    'cuddle puddle': 'capsule',
    'cuddle puddle': 'pill',
    'the hulk': 'combo',
    'crypto caps': 'shroom',

    'orange wedges': 'acid',
    'molly mutant': 'capsule',
    'molly mutant': 'pill',
    'the trumps': 'combo',
    'mutant mushies': 'shroom',

    'micro dosing': 'acid',
    'vitamin e': 'capsule',
    'vitamin e': 'pill',
    'golden shower': 'combo',
    'mellow yellow': 'shroom'
}

def get_mutate_requests_collection():
    client = pymongo.MongoClient(CONNECTION_STRING)
    database = client['thecardroom']
    collection = database['mutate_requests']

    return collection

def get_mutants_collection():
    client = pymongo.MongoClient(CONNECTION_STRING)
    database = client['thecardroom']
    collection = database['mutants']

    return collection

def extract_cid(url: str) -> str:
    cid = url[7:]
    if cid.startswith('ipfs/'):
        cid = cid[5:]

    return cid

def download_normie_image(logger, url: str):
    image_file = None

    for i in range(0, 5):
        logger.info('Download attempt: {}'.format(i+1))

        try:
            fd = urllib.request.urlopen(url)
            if fd.status != 200:
                logger.error('HTTP Error: {}'.format(fd.status))
                continue
            image_file = io.BytesIO(fd.read())
        except urllib.error.HTTPError as e:
            logger.error('HTTPError: {}'.format(e))
            continue
        except http.client.IncompleteRead as ire:
            logger.error('Incomplete Read')
            continue

        break

    if image_file == None:
        raise Exception('Failed to download: {}'.format(url))

    return image_file

# Creates the normies package.
#
# This process requires cardano-node and cardano-db-sync to be running.
#
# @param network "mainnet" or "testnet"
# @param wallet_name A previously created wallet to search for incoming UTXOs.
def process_requests(network: str, wallet_name: str) -> None:
    if not network in tcr.command.networks:
        raise Exception('Invalid Network: {}'.format(network))

    # General setup
    logger = logging.getLogger(network)
    cardano = Cardano(network, '{}_protocol_parameters.json'.format(network))

    # Open the whitelist to make sure only approved projects are mutated.
    mutate_whitelist = {}
    with open('mutate_whitelist.json', 'r') as file:
        mutate_whitelist = json.load(file)
    if mutate_whitelist == None:
        logger.error('Unable to parse {}'.format("mutate_whitelist.json"))
        raise Exception('Unable to parse {}'.format("mutate_whitelist.json"))

    # Open the wallet to monitor for incoming payments and initialize the
    # payment address if necessary
    wallet = Wallet(wallet_name, network)
    if not wallet.exists():
        logger.error('Wallet: <{}> does not exist'.format(wallet_name))
        raise Exception('Wallet: <{}> does not exist'.format(wallet_name))

    addr_index = Wallet.ADDRESS_INDEX_MUTATE_REQUEST
    if wallet.get_payment_address(addr_index) == None:
        wallet.setup_address(addr_index)

    tip = cardano.query_tip()
    cardano.query_protocol_parameters()
    tip_slot = tip['slot']

    database = Database('{}.ini'.format(network))
    database.open()
    latest_slot = database.query_latest_slot()
    sync_progress = database.query_sync_progress()
    logger.info('Cardano Node Tip Slot: {}'.format(tip_slot))
    logger.info(' Database Latest Slot: {}'.format(latest_slot))
    logger.info('        Sync Progress: {}'.format(sync_progress))
    logger.info('')
    logger.info('Payment address: {}'.format(wallet.get_payment_address(Wallet.ADDRESS_INDEX_MUTATE_REQUEST)))

    # Populate UTXOs with the address of the sender and stake address of the
    # sender
    (utxos, total_lovelace) = cardano.query_utxos(wallet,
                                                  [wallet.get_payment_address(addr_index, delegated=True),
                                                   wallet.get_payment_address(addr_index, delegated=False)])
    for utxo in utxos:
        logger.info('UTXO: txid = {}, amount = {}'.format(utxo['tx-hash'], utxo['amount']))
        if utxo['amount'] == MINT_PAYMENT:
            # No need to query transactions that don't match the mint amount
            inputs = database.query_utxo_inputs(utxo['tx-hash'])
            utxo['from'] = inputs[0]['address']
            utxo['from_stake'] = database.query_stake_address(utxo['from'])
            logger.info('UTXO: from address: {}'.format(utxo['from']))
            logger.info('UTXO: from  stake: {}'.format(utxo['from_stake']))
        else:
            utxo['from'] = None
            utxo['from_stake'] = None

    # Setup directories for output files
    if not os.path.exists('normie_pkg'):
        os.mkdir('normie_pkg')

    subdir = 'normie_pkg/{}'.format(datetime.datetime.today().strftime('%Y_%m_%d'))
    if not os.path.exists(subdir):
        os.mkdir(subdir)

    # Process the request and build the mutation package
    normies_pkg = []
    mutate_requests_collection = get_mutate_requests_collection()
    requests = mutate_requests_collection.find({'processed': False})
    processed_ids = []
    for r in requests:
        logger.info('')
        logger.info('Request: {}'.format(r['_id']))
        logger.info('                  Date: {}'.format(r['date']))
        logger.info('       Normie Asset ID: {}'.format(r['normie_asset_id']))
        logger.info('     Mutation Asset ID: {}'.format(r['mutation_asset_id']))
        logger.info('                  From: {}'.format(r['from']))
        logger.info('             Processed: {}'.format(r['processed']))
        if r['processed'] == True:
            logger.error('Already processed: {}:\r\n{}/{}'.format(r['from'], r['normie_asset_id'], r['mutation_asset_id']))
            continue

        logger.info('Process: {}, from: {}'.format(r['_id'], r['from']))
        logger.info(' Assets: {}/{}'.format(r['normie_asset_id'], r['mutation_asset_id']))
        normie_owner = database.query_owner_by_fingerprint(r['normie_asset_id'])
        logger.info('Normie Owner: {}'.format(normie_owner))
        mutation_owner = database.query_owner_by_fingerprint(r['mutation_asset_id'])
        logger.info('Mutation Owner: {}'.format(mutation_owner))

        if normie_owner != mutation_owner:
            logger.error('Owner mismatch for {}: {} != {}'.format(r['from'], r['normie_asset_id'], r['mutation_asset_id']))
            continue

        (normie_policy, normie_token_name, normie_md) = database.query_nft_metadata(r['normie_asset_id'])
        logger.info('Normie Policy: {}'.format(normie_policy))
        if normie_policy == None or normie_md == None:
            logger.error('Normie asset policy / metadata not found: {}/{}'.format(normie_policy, normie_md))
            continue

        (mutation_policy, mutation_token_name, mutation_md) = database.query_nft_metadata(r['mutation_asset_id'])
        logger.info('Mutation Policy: {}'.format(mutation_policy))
        if mutation_policy == None or mutation_md == None:
            logger.error('Mutation asset policy / metadata not found: {}/{}'.format(mutation_policy, mutation_md))
            continue

        if mutation_policy != '7135025a3c23035cdcff4ef8ae3849248afd369466ea1abef61a4157':
            logger.error('Invalid mutation policy: {}'.format(mutation_policy))
            continue

        if normie_policy not in mutate_whitelist:
            logger.error('Unapproved normie policy: {}'.format(normie_policy))
            continue

        # search for a payment that matches the request
        payment = None
        for utxo in utxos:
            if utxo['from_stake'] == normie_owner:
                payment = utxo
                break

        if payment == None:
            logger.error('No payment found')
            continue

        # remove this one from the list so it doesn't get processed more than
        # once
        utxos.remove(payment)
        if payment['amount'] != MINT_PAYMENT or len(payment['assets']) != 0:
            logger.error('Invalid payment: {} / {}'.format(payment['amount'], payment['assets']))
            continue

        cid = extract_cid(normie_md[721][normie_policy][normie_token_name]['image'])
        if 'files' in normie_md[721][normie_policy][normie_token_name]:
            files = normie_md[721][normie_policy][normie_token_name]['files']
            for file in files:
                if file['mediaType'].startswith('image/'):
                    cid = extract_cid(file['src'])
                    break

        download_url = 'https://ipfs.io/ipfs/{}'.format(cid)
        logger.info('Download Normie: {}'.format(download_url))
        image_file = download_normie_image(logger, download_url)

        character = mutation_md[721][mutation_policy][mutation_token_name]['character']
        flavor = mutation_md[721][mutation_policy][mutation_token_name]['flavor']
        mutation = mutation_md[721][mutation_policy][mutation_token_name]['mutation']
        potency = mutation_md[721][mutation_policy][mutation_token_name]['potency']
        vqgan_text = character + ' ' + flavor + ' ' + mutation

        im = PIL.Image.open(image_file)
        im.save(subdir + '/' + r['normie_asset_id'] + '.png', format='png')
        normie = {
            'request_id': str(r['_id']),
            'from': payment['from'],
            'tx': '{}:{}'.format(payment['tx-hash'], payment['tx-ix']),
            'potency': potency_lut[potency],
            'normie-image': r['normie_asset_id']+'.png',
            'normie-asset-id': r['normie_asset_id'],
            'mutation-asset-id': r['mutation_asset_id'],
            'vqgan-text': vqgan_text,
            'runtime': runtime_lut[potency],
            'resolution': resolution_lut[potency]
        }

        # save database object id to update it later
        processed_ids.append(r['_id'])

        normies_pkg.append(normie)

    with open('{}/normies.json'.format(subdir), 'w') as f:
        f.write(json.dumps(normies_pkg, indent=4))

    # Update the database
    for id in processed_ids:
        logger.info('Mark Processed: {}'.format(id))
        mutate_requests_collection.update_one({'_id': id},
                                              {'$set': {'processed': True}})

def get_media_type(logger: logging.Logger, image_filename: str) -> str:
    media_type = None
    extension = None

    if image_filename.endswith('.jpg') or image_filename.endswith('.jpeg'):
        media_type = 'jpeg'
        extension = 'jpg'
    elif image_filename.endswith('.png'):
        media_type = 'png'
        extension = 'png'
    elif image_filename.endswith('.gif'):
        media_type = 'gif'
        extension = 'gif'
    else:
        logger.error('Unexpected file type: {}'.format(image_filename))
        raise Exception('Unexpected file type: {}'.format(image_filename))

    return (media_type, extension)

def get_thumbnail_source(logger: logging.Logger, file1: str, file2: str) -> str:
    (media_type, ext) = get_media_type(logger, file1)
    if ext == 'jpg' or ext == 'png':
        logger.info('Thumbnail Source: {}'.format(file1))
        return file1

    (media_type, ext) = get_media_type(logger, file2)
    if ext == 'jpg' or ext == 'png':
        logger.info('Thumbnail Source: {}'.format(file2))
        return file2

    logger.error('Thumbnail source not found')
    raise('Thumbnail source not found')

def mint_mutants(network: str, policy_name: str, mutants_file: str) -> None:
    # General setup
    logger = logging.getLogger(network)
    cardano = Cardano(network, '{}_protocol_parameters.json'.format(network))
    cardano.query_protocol_parameters()
    database = Database('{}.ini'.format(network))
    database.open()
    latest_slot = database.query_latest_slot()
    sync_progress = database.query_sync_progress()
    tip = cardano.query_tip()
    tip_slot = tip['slot']
    logger.info('Cardano Node Tip Slot: {}'.format(tip_slot))
    logger.info(' Database Latest Slot: {}'.format(latest_slot))
    logger.info('        Sync Progress: {}'.format(sync_progress))
    logger.info('')
    logger.info('  Mutants File: {}'.format(mutants_file))
    logger.info('   Policy Name: {}'.format(policy_name))
    logger.info('     Policy ID: {}'.format(cardano.get_policy_id(policy_name)))
    logger.info('Minting Wallet: {}'.format(cardano.get_policy_owner(policy_name)))

    sales = Sales(cardano.get_network(), policy_name)

    if cardano.get_policy_id(policy_name) == None:
        logger.error('Policy ID not found')
        raise Exception('Policy ID not found')

    minting_wallet = Wallet(cardano.get_policy_owner(policy_name), network)
    if not minting_wallet.exists():
        logger.error('Wallet not found: {}'.format(minting_wallet.get_name()))
        raise Exception('Wallet not found: {}'.format(minting_wallet.get_name()))

    relative_dir = os.path.dirname(mutants_file)
    policy_id = cardano.get_policy_id(policy_name)
    logger.info('Relative Dir: {}'.format(relative_dir))

    addr_index = Wallet.ADDRESS_INDEX_MUTATE_REQUEST
    (utxos, total_lovelace) = cardano.query_utxos(minting_wallet,
                                                  [minting_wallet.get_payment_address(addr_index, delegated=True)])
    for utxo in utxos:
        inputs = database.query_utxo_inputs(utxo['tx-hash'])
        utxo['from'] = inputs[0]['address']
        utxo['from_stake'] = database.query_stake_address(utxo['from'])

    mutants = {}
    with open(mutants_file, 'r') as file:
        mutants = json.load(file)

    for mutant in mutants:
        logger.info('Processing: {}'.format(mutant['mutant-name']))

        # upload fullsize image 1 to ipfs
        projectid = tcr.addresses.addresses['ipfs'][policy_name]['project-id']
        projectsecret = tcr.addresses.addresses['ipfs'][policy_name]['project-secret']
        full_filename_1 = '{}/{}'.format(relative_dir, mutant['mutant-image-1'])
        logger.info('Uploading Mutant 1: {}'.format(full_filename_1))
        fullsize_ipfs_hash_1 = tcr.ipfs.ipfs_upload(projectid, projectsecret, full_filename_1)
        pin_state = tcr.ipfs.ipfs_pin(projectid, projectsecret, fullsize_ipfs_hash_1)
        logger.info('Fullsize IPFS Hash 1: {}, pin = {}'.format(fullsize_ipfs_hash_1, pin_state))

        # upload fullsize image 2 to ipfs if it exists
        fullsize_ipfs_hash_2 = None
        full_filename_2 = None
        if mutant['mutant-image-2'] != None:
            full_filename_2 = '{}/{}'.format(relative_dir, mutant['mutant-image-2'])
            logger.info('Uploading Mutant 2: {}'.format(full_filename_2))
            fullsize_ipfs_hash_2 = tcr.ipfs.ipfs_upload(projectid, projectsecret, full_filename_2)
            pin_state = tcr.ipfs.ipfs_pin(projectid, projectsecret, fullsize_ipfs_hash_2)
            logger.info('Fullsize IPFS Hash 2: {}, pin = {}'.format(fullsize_ipfs_hash_2, pin_state))

        # create thumbnail image
        thumbnail_source = get_thumbnail_source(logger, full_filename_1, full_filename_2)
        im = PIL.Image.open(thumbnail_source)
        width, height = im.size
        logger.info('Original Size: {} x {}'.format(width, height))
        new_width = 512
        new_height = int(height * new_width / width)
        newsize = (new_width, new_height)
        thumbnail_filename = '{}/thumbnail_{}'.format(relative_dir, os.path.basename(thumbnail_source))
        logger.info('Generating Thumbnail: {}'.format(thumbnail_filename))
        im = im.resize(newsize)
        (media_type, extension) = get_media_type(logger, thumbnail_source)
        im.save(thumbnail_filename, format=media_type)
        width, height = im.size
        logger.info('Thumbnail Size: {} x {}'.format(width, height))

        # upload thumbnail image to ipfs
        logger.info('Uploading Thumbnail: {}'.format(thumbnail_filename))
        thumbnail_ipfs_hash = tcr.ipfs.ipfs_upload(projectid, projectsecret, thumbnail_filename)
        pin_state = tcr.ipfs.ipfs_pin(projectid, projectsecret, thumbnail_ipfs_hash)
        logger.info('Thumbnail IPFS Hash: {}, pin = {}'.format(thumbnail_ipfs_hash, pin_state))

        # generate metadata
        (fullsize_media_type_1, fullsize_ext_1) = get_media_type(logger, full_filename_1)
        (thumbnail_media_type, thumbnail_ext) = get_media_type(logger, thumbnail_filename)
        token_name = mutant['mutant-name'].replace(' ', '').replace('#', '')
        metadata_file = '{}/{}.json'.format(relative_dir, token_name)
        mutant_metadata = {
            '721': {
                policy_id: {
                    token_name: {
                        'name': mutant['mutant-name'],
                        'files': [
                            {
                                'name': '{}.{}'.format(token_name.lower(), fullsize_ext_1),
                                'src': 'ipfs://{}'.format(fullsize_ipfs_hash_1),
                                'mediaType': 'image/{}'.format(fullsize_media_type_1)
                            }
                        ],
                        'image': 'ipfs://{}'.format(thumbnail_ipfs_hash),
                        'mediaType': 'image/{}'.format(thumbnail_media_type),
                        'description': 'The Card Room - Mutants',
                        'algorithm': mutant['algorithm'],
                        'normie': mutant['normie-asset-id'],
                        'mutation': mutant['mutation-asset-id'],
                        'website': 'https://thecardroom.io/'
                    }
                },
                'version': '1.0'
            }
        }

        if full_filename_2 != None:
            (fullsize_media_type_2, fullsize_ext_2) = get_media_type(logger, full_filename_2)
            mutant_metadata['721'][policy_id][token_name]['files'].append({
                'name': '{}.{}'.format(token_name.lower(), fullsize_ext_2),
                'src': 'ipfs://{}'.format(fullsize_ipfs_hash_2),
                'mediaType': 'image/{}'.format(fullsize_media_type_2)
            })

        logger.info('Writing Metadata: {}'.format(metadata_file))
        with open(metadata_file, 'w') as file:
            file.write(json.dumps(mutant_metadata, indent=4))

        # Search for the utxo found / specified in the normies file
        input_utxo = None
        for utxo in utxos:
            if utxo['amount'] == MINT_PAYMENT and '{}:{}'.format(utxo['tx-hash'], utxo['tx-ix']) == mutant['tx']:
                input_utxo = {'utxo': utxo, 'count': 1, 'refund': 0}
                utxos.remove(utxo)
                logger.info('Input UTXO: {}#{}'.format(utxo['tx-hash'], utxo['tx-ix']))
                break

        if input_utxo == None:
            logger.error('Input UTXO not found.  Already minted? ')
            continue

        # mint
        dst = None
        if 'destination' in mutant and mutant['destination'] != None:
            dst = mutant['destination']

        txid = tcr.tcr.mint_nft(cardano, database, minting_wallet,
                                Wallet.ADDRESS_INDEX_MUTATE_REQUEST,
                                policy_name, input_utxo, metadata_file, sales,
                                destination=dst)
        logger.info('NFT Minted, TXID: {}'.format(txid))
        if txid == None:
            logger.error('txid == None')
            break

        entry = {
            'request_id': mutant['request_id'],
            'payment_txid': input_utxo['utxo']['tx-hash'],
            'normie': mutant['normie-asset-id'],
            'mutation': mutant['mutation-asset-id'],
            'mutant_thumbnail': 'ipfs://{}'.format(thumbnail_ipfs_hash),
            'mutant_full': 'ipfs://{}'.format(fullsize_ipfs_hash_1),
            'mint_txid': txid
        }
        mutants = get_mutants_collection()
        result = mutants.insert_one(entry)
        logger.info('Inserted ID = {}'.format(result.inserted_id))
        logger.info('')

#
# python3 -m tcr.mutate --wallet=tcr_mint
# python3 -m tcr.mutate --policy=mutants --mutants=./normie_pkg/file
#
def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--wallet', required=False,
                                    action='store',
                                    type=str,
                                    metavar='NAME',
                                    help='Wallet name to check payments.')
    parser.add_argument('--policy', required=False,
                                     action='store',
                                     type=str,
                                     metavar='NAME',
                                     help='Policy name to use to mint mutant NFTs.')
    parser.add_argument('--mutants', required=False,
                                     action='store',
                                     type=str,
                                     metavar='NAME',
                                     help='Mutant NFTs to mint.')

    network = 'mainnet'
    tcr.nftmint.setup_logging(network, 'mutate')

    args = parser.parse_args()

    if args.mutants != None and args.policy != None:
        mint_mutants(network, args.policy, args.mutants)
    elif args.wallet != None:
        process_requests(network, args.wallet)
    else:
        raise Exception('Invalid parameters')

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('')
        print('')
        print('EXCEPTION: {}'.format(e))
        print('')
        traceback.print_exc()
