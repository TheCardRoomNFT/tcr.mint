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
import logging
import argparse
import tcr.command
import tcr.nftmint
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

# Provide the mongodb atlas url to connect python to mongodb using pymongo
CONNECTION_STRING = tcr.addresses.addresses['mongodb']

MINT_PAYMENT = 10000000

potency_lut = {
    'low': 1,
    'medium-low': 2,
    'medium': 3,
    'medium-high': 4,
    'high': 5,
}

runtime_lut = {
    'low': 'short',
    'medium-low': 'short',
    'medium': 'medium',
    'medium-high': 'long',
    'high': 'extra long',
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

def get_collection():
    client = pymongo.MongoClient(CONNECTION_STRING)
    database = client['thecardroom']
    collection = database['mutate_requests']

    return collection.find()

# Creates the normies package.
#
# This process requires cardano-node and cardano-db-sync to be running.
#
# @param network "mainnet" or "testnet"
# @param wallet_name A previously created wallet to search for incoming UTXOs.
# @param requests_file JSON file of requests
def process_requests(network: str, wallet_name: str) -> None:
    if not network in tcr.command.networks:
        raise Exception('Invalid Network: {}'.format(network))

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

    # General setup
    logger = logging.getLogger(network)
    cardano = Cardano(network, '{}_protocol_parameters.json'.format(network))

    tip = cardano.query_tip()
    cardano.query_protocol_parameters()
    tip_slot = tip['slot']

    database = Database('{}.ini'.format(network))
    database.open()
    latest_slot = database.query_latest_slot()
    sync_progress = database.query_sync_progress()
    logger.info('Cardano Node Tip Slot: {}'.format(tip_slot))
    logger.info(' Database Latest Slot: {}'.format(latest_slot))
    logger.info('Sync Progress: {}'.format(sync_progress))
    logger.info('')
    logger.info('Payment address: {}'.format(wallet.get_payment_address(Wallet.ADDRESS_INDEX_MUTATE_REQUEST)))

    # Populate UTXOs with the address of the sender and stake address of the
    # sender
    (utxos, total_lovelace) = cardano.query_utxos(wallet,
                                                  [wallet.get_payment_address(addr_index, delegated=True),
                                                   wallet.get_payment_address(addr_index, delegated=False)])
    for utxo in utxos:
        inputs = database.query_utxo_inputs(utxo['tx-hash'])
        utxo['from'] = inputs[0]['address']
        utxo['from_stake'] = database.query_stake_address(utxo['from'])

    # Setup directories for output files
    if not os.path.exists('normie_pkg'):
        os.mkdir('normie_pkg')

    subdir = 'normie_pkg/{}'.format(datetime.datetime.today().strftime('%Y_%m_%d'))
    if not os.path.exists(subdir):
        os.mkdir(subdir)

    normies_pkg = []
    # Process the request and build the mutation package
    logger.info('Mutation Address: {}'.format(wallet.get_payment_address(addr_index)))
    requests = get_collection()

    for r in requests:
        logger.info('Process: {}:\r\n{}/{}'.format(r['from'], r['normie_asset_id'], r['mutation_asset_id']))
        normie_owner = database.query_owner_by_fingerprint(r['normie_asset_id'])
        mutation_owner = database.query_owner_by_fingerprint(r['mutation_asset_id'])

        if normie_owner != mutation_owner:
            logger.error('Owner mismatch for {}: {} != {}'.format(r['from'], r['normie_asset_id'], r['mutation_asset_id']))
            continue

        (normie_policy, normie_token_name, normie_md) = database.query_nft_metadata(r['normie_asset_id'])
        if normie_policy == None or normie_md == None:
            logger.error('Normie asset policy / metadata not found: {}/{}'.format(normie_policy, normie_md))
            continue

        (mutation_policy, mutation_token_name, mutation_md) = database.query_nft_metadata(r['mutation_asset_id'])
        if mutation_policy == None or mutation_md == None:
            logger.error('Normie asset policy / metadata not found: {}/{}'.format(mutation_policy, mutation_md))
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

        cid = normie_md[721][normie_policy][normie_token_name]['image'][7:]
        download_url = 'https://infura-ipfs.io/ipfs/{}'.format(cid)
        logger.info('Download Normie: {}'.format(download_url))

        fd = urllib.request.urlopen(download_url)
        if fd.status != 200:
            logger.info('HTTP Error: {}'.format(fd.status))
            continue

        character = mutation_md[721][mutation_policy][mutation_token_name]['character']
        flavor = mutation_md[721][mutation_policy][mutation_token_name]['flavor']
        mutation = mutation_md[721][mutation_policy][mutation_token_name]['mutation']
        potency = mutation_md[721][mutation_policy][mutation_token_name]['potency']
        base_text = character + ' ' + flavor + ' ' + mutation

        vqgan_text = ''
        if mutation_type_lut[mutation] == 'acid':
            vqgan_text = base_text + ' vibrant detailed'
        elif mutation_type_lut[mutation] == 'capsule' or mutation_type_lut[mutation] == 'pill':
            vqgan_text = base_text
        elif mutation_type_lut[mutation] == 'combo':
            vqgan_text = base_text + ' psychedelic 3d'
        elif mutation_type_lut[mutation] == 'shroom':
            vqgan_text = base_text + ' unreal engine'
        else:
            logger.error('WUT?')
            continue

        image_file = io.BytesIO(fd.read())
        im = PIL.Image.open(image_file)
        im.save(subdir + '/' + r['normie_asset_id'] + '.png', format='png')
        normie = {
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
        normies_pkg.append(normie)

    with open('{}/normies.json'.format(subdir), 'w') as f:
        f.write(json.dumps(normies_pkg, indent=4))

    #shutil.make_archive(subdir, 'zip', subdir)
    #logger.info('Normies Package: {}.zip'.format(subdir))

def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--wallet', required=False,
                                    action='store',
                                    type=str,
                                    metavar='NAME',
                                    help='Wallet name to check payments.')

    network = 'mainnet'
    tcr.nftmint.setup_logging(network, 'mutate')

    args = parser.parse_args()
    if args.wallet == None:
        raise Exception('--wallet required with --requests')
    process_requests(network, args.wallet)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('')
        print('')
        print('EXCEPTION: {}'.format(e))
        print('')
        traceback.print_exc()
