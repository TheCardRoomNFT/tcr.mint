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

from typing import List, Set, Dict
from tcr.wallet import Wallet
from tcr.wallet import WalletExternal
from tcr.cardano import Cardano
from tcr.nft import Nft
import tcr.tcr
from tcr.database import Database
import json
import os
import logging
import argparse
import tcr.nftmint
import tcr.command
import time

def main():
    # Set parameters for the transactions
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--network', required=True,
                                     action='store',
                                     type=str,
                                     metavar='NAME',
                                     help='Which network to use, [mainnet | testnet]')

    parser.add_argument('--src', required=True,
                                  action='store',
                                  type=str,
                                  metavar='NAME',
                                  default=None,
                                  help='Wallet name to send from.')

    parser.add_argument('--dst', required=True,
                                  action='store',
                                  type=str,
                                  metavar='NAME',
                                  default=None,
                                  help='Wallet name to send to.')

    parser.add_argument('--amount', required=False,
                                    action='store',
                                    type=int,
                                    metavar='NAME',
                                    default=0,
                                    help='Amount of lovelace to send')

    parser.add_argument('--all', required=False,
                                 action='store_true',
                                 default=False,
                                 help='Confirm to send all')

    parser.add_argument('--repeat', required=False,
                                    action='store_true',
                                    default=False,
                                    help='Continuously send specified amount')

    parser.add_argument('--nft', required=False,
                                 action='store',
                                 type=str,
                                 metavar='NAME',
                                 default=None,
                                 help='Full name of NFT to send')
    parser.add_argument('--setup', required=False,
                                   action='store_true',
                                   default=False,
                                   help='Create wallet addresses')
    args = parser.parse_args()
    network = args.network
    src_name = args.src
    dst_name = args.dst
    amount = args.amount
    all = args.all
    nft = args.nft
    repeat = args.repeat
    setup = args.setup

    if not network in tcr.command.networks:
        raise Exception('Invalid Network: {}'.format(network))

    tcr.nftmint.setup_logging(network, 'buybot')
    logger = logging.getLogger(network)

    # Setup connection to cardano node, cardano wallet, and cardano db sync
    cardano = Cardano(network, '{}_protocol_parameters.json'.format(network))
    logger.info('{} Buy Bot'.format(network.upper()))
    logger.info('Copyright 2021-2022 The Card Room')
    logger.info('Network: {}'.format(network))

    tip = cardano.query_tip()
    cardano.query_protocol_parameters()
    tip_slot = tip['slot']

    database = Database('{}.ini'.format(network))
    database.open()
    meta = database.query_chain_metadata()
    db_size = database.query_database_size()
    latest_slot = database.query_latest_slot()
    sync_progress = database.query_sync_progress()
    logger.info('Database Chain Metadata: {} / {}'.format(meta[1], meta[2]))
    logger.info('Database Size: {}'.format(db_size))
    logger.info('Cardano Node Tip Slot: {}'.format(tip_slot))
    logger.info(' Database Latest Slot: {}'.format(latest_slot))
    logger.info('Sync Progress: {}'.format(sync_progress))

    src_wallet = Wallet(src_name, cardano.get_network())

    if dst_name.startswith('addr'):
        dst_wallet = WalletExternal('External', cardano.get_network(), dst_name)
    else:
        dst_wallet = Wallet(dst_name, cardano.get_network())

    if all == False and amount < 1000000 and nft == None and setup == False:
        logger.error("Amount too small: {}".format(amount))
        raise Exception("Amount too small: {}".format(amount))

    if setup:
        logger.info("SetUp Wallet: {}".format(src_wallet.get_name()))
        result = True
        if not src_wallet.address_exists(Wallet.ADDRESS_INDEX_PRESALE):
            result = result and src_wallet.setup_address(Wallet.ADDRESS_INDEX_PRESALE)

        if not src_wallet.address_exists(Wallet.ADDRESS_INDEX_ROYALTY):
            result = result and src_wallet.setup_address(Wallet.ADDRESS_INDEX_ROYALTY)

        if not src_wallet.address_exists(Wallet.ADDRESS_INDEX_MUTATE_REQUEST):
            result = result and src_wallet.setup_address(Wallet.ADDRESS_INDEX_MUTATE_REQUEST)

        if result:
            logger.info('Wallet addresses setup')
        else:
            logger.error('Failed to setup wallet addresses')

        return

    if not dst_wallet.exists():
        logger.error("Destination wallet missing: {}".format(dst_wallet.get_name()))
        raise Exception("Destination wallet missing: {}".format(dst_wallet.get_name()))

    if not src_wallet.exists():
        logger.error("Source wallet missing: {}".format(src_wallet.get_name()))
        raise Exception("Source wallet missing: {}".format(src_wallet.get_name()))

    if amount > 0 or (amount == 0 and all == True):
        send_payment = True
        while send_payment:
            if amount > 0:
                tx_id = tcr.tcr.transfer_ada(cardano, src_wallet, amount, dst_wallet)
            elif all == True:
                tx_id = tcr.tcr.transfer_all_assets(cardano, src_wallet, dst_wallet)
            else:
                logger.error("Nothing to Send")
                break

            if tx_id == None:
                repeat = False
            else:
                # It could be possible for the destination wallet to remove the
                # txid before we see it.  After 2 minutes, assume it's been received
                # and move on
                tries = 0
                while tries < 24 and not cardano.contains_txhash(dst_wallet, tx_id):
                    time.sleep(5)
                    tries += 1

            send_payment = repeat
    elif nft != None:
        if '.' not in nft:
            # send all the NFTs matching the policy ID with minimum ADA
            (utxos, total_lovelace) = cardano.query_utxos(src_wallet)
            tx_nfts = {}
            for utxo in utxos:
                for asset in utxo['assets']:
                    # TODO: figure out how to calculat the current size of a transaction
                    # and if it would be too big or not.  For now, 300 assets seems
                    # near the maximum.
                    if len(tx_nfts) > 300:
                        break

                    if asset.startswith(nft):
                        tx_nfts[asset] = utxo['assets'][asset]

            if len(tx_nfts) > 0:
                tx_id = tcr.tcr.transfer_nft(cardano, src_wallet, tx_nfts, dst_wallet)
            else:
                tx_id = None
                logger.error('No matching NFT assets found')
        else:
            tx_id = tcr.tcr.transfer_nft(cardano, src_wallet, {nft: 1}, dst_wallet)

        if tx_id == None:
            logger.error('Failed to submit transaction')
            return

        while not cardano.contains_txhash(dst_wallet, tx_id):
            time.sleep(5)

if __name__ == '__main__':
    main()

#python3 -m tcr.buybot --network=testnet --src=testnet1 --dst=testnet1 --all