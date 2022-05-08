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
from tcr.wallet import WalletExternal
from tcr.cardano import Cardano
from tcr.database import Database
import logging
import argparse
import tcr.command
import tcr.nftmint
import traceback
import json

# Simple application to query db-sync for the metadata associated with the NFT
# in a mint transaction.  Note that it's possible for a NFT or token to have
# multiple mint transactions.  In case of multiples, the newest metadata is
# returned.
def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--network', required=True,
                                    action='store',
                                    type=str,
                                    metavar='NAME',
                                    help='Which network to use, [mainnet | testnet]')
    parser.add_argument('--fingerprint', required=False,
                                         action='store',
                                         type=str,
                                         default=None,
                                         metavar='ID',
                                         help='Fingerprint of desired NFT')
    parser.add_argument('--policy-id', required=False,
                                       action='store',
                                       type=str,
                                       default=None,
                                       metavar='ID',
                                       help='Policy ID')
    args = parser.parse_args()
    network = args.network
    fingerprint = args.fingerprint
    policy_id = args.policy_id

    if not network in tcr.command.networks:
        raise Exception('Invalid Network: {}'.format(network))

    tcr.nftmint.setup_logging(network, 'nftquery')
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

    if fingerprint != None:
        (policy, metadata) = database.query_nft_metadata(fingerprint)
        logger.info(json.dumps(metadata, indent=4))

    if policy_id != None:
        transactions = database.query_mint_transactions(policy_id)
        logger.info('Len Transactions: {}'.format(len(transactions)))
        if '' in transactions:
            logger.info('royalty token ' + json.dumps(transactions[''], indent=4))
            (policy, name, metadata) = database.query_nft_metadata(transactions['']['fingerprint'])
            logger.info('royalty metadata ' + json.dumps(metadata, indent=4))
        else:
            logger.info('royalty token not found')

        policies = policy_id.split(',')
        logger.info('')

        by_address = {}
        for policy in policies:
            tokens = database.query_current_owner(policy)
            logger.info('{} = {} tokens'.format(policy, len(tokens)))

            keys = list(tokens.keys())
            keys.sort()
            for name in keys:
                address = tokens[name]['address']
                if address in by_address:
                    by_address[address].append(name)
                else:
                    by_address[address] = [name]

        holders = list(by_address.items())

        def sort_by_length(item):
            return len(item[1])
        holders.sort(key=sort_by_length)
        logger.info('By Owner ({}):'.format(len(holders)))
        i = 1
        for holder in holders:
            logger.info('{: 4}.  {}({})'.format(i, holder[0], len(holder[1])))
            tokens = holder[1]

            token_str = ''
            j = 0
            for token in tokens:
                if len(token_str) == 0:
                    token_str += token
                else:
                    token_str += ', ' + token
                j += 1
                if j == 5:
                    logger.info('       {}'.format(token_str))
                    j = 0
                    token_str = ''

            if j > 0:
                logger.info('       {}'.format(token_str))
            i += 1



if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('')
        print('')
        print('EXCEPTION: {}'.format(e))
        print('')
        traceback.print_exc()
