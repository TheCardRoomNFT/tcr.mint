# [The Card Room](https://thecardroom.io)

The Card Room is a Cardano based NFT platform, a unique gallery of collectable
NFT playing cards, individually minted on the Cardano blockchain.  This codebase
represents a collection of scripts we have created and found useful for minting
NFTs on the Cardano blockchain.


# Prerequisites

These scripts assume that cardano-node, cardano-addresses, cardano-db-sync, and
are installed and running on the system.  Please see details of
how to install and run these on the input-output-hk github account:
  - [cardano-node](https://github.com/input-output-hk/cardano-node)
  - [cardano-db-sync](https://github.com/input-output-hk/cardano-db-sync)
  - [cardano-addresses](https://github.com/input-output-hk/cardano-addresses)

The scripts also require some environment variables to be set (click the link
below for detailed installation instructions):
  - CARDANO_NODE_SOCKET_PATH
  - TESTNET_CARDANO_NODE_SOCKET_PATH
  - MAINNET_CARDANO_NODE_SOCKET_PATH

If you don't want to build from source, the installation instructions below show
where to download pre-build binaries from.


# Installation

  Detailed [Installation Instructions](INSTALL.md)


# Running

Before NFTs can be minted, some basic setup and initialization needs to be done.
"testnet" can be replaced with "mainnet" to run everything on mainnet.

  - Create a wallet
    > nftmint --network=testnet --create-wallet=project_mint

  - Using the wallet just created, create a new policy ID
    > nftmint --network=testnet --create-policy=project_policy --wallet=project_mint

  - Create a metadata template
    > nftmint --network=testnet --create-drop-template=project_series_1
    > Edit nft/testnet/project_series_1_metametadata.json

  - Create metadata that defines the artwork and NFTs to be created.  This creates
  metadata for each individual NFT
    > nftmint --network=testnet --create-drop=project_series_1 --policy=project_policy

  - Upload assets into IPFS:
    > ipfs --projectid=myprojectid --projectsecret=myprojectsecret --network=testnet --drop=project_series_1

  - Lookup your wallet payment address in wallet/testnet/project_mint_1_delegated_payment.addr
    > Publish the payment address for community members to transfer ADA to

  - Accept payments and mint NFTs
    > nftmint --network=testnet --mint --wallet=project_mint --policy=project_policy --drop=project_series_1

# Other Use Cases

1.  Query Network Status:
    > python3 -m tcr.status --network=testnet
    > python3 -m tcr.status --network=mainnet

2.  Query Wallet Holdings:
The applications know about three different addresses.
    * Address Index 0: ROOT, Default address where outputs are sent
    * Address Index 1: MINT, Monitor for incoming payments
    * Address Index 2: PRESALE, Monitor for presale payments
Display UTXOs for all three known addresses (delegated and undelegated):
    > python3 -m tcr.status --network=testnet --wallet=testnet1

3.  Transfer ADA (lovelace) from one wallet to another:
    > python3 -m tcr.buybot --network=testnet --src=testnet1 --dst=testnet2 --amount=430000000

4.  Get the Presale address & confirm by generating whitelist (which should be empty):
    > python3 -m tcr.status --network=mainnet --wallet=tcr_mint
    > python3 -m tcr.genwhitelist --network=testnet --drop=tn_series_3 --output=whitelist.json

5.  Generate a drop:
New drop with random data (seed written to log file):
    > python3 -m tcr.nftmint --network=testnet --create-drop=tn_series_3 --policy=tn_policy1
    > python3 -m tcr.nftmint --network=mainnet --create-drop=tcr_series_2 --policy=tcr_series_2 --seed=1634027967

Set a seed to recreate a drop:
    > python3 -m tcr.nftmint --network=testnet --create-drop=tn_series_3 --policy=tn_policy1 --seed=1634631884

6.  Upload images to IPFS via infura.io
For "cards" do this before generating the drop
Updates metadata in series metametadata or nft metadata depending on "cards" or "layers"
    > python3 -m tcr.ipfs --network=testnet --drop=tn_series_3 --projectid=<id> --projectsecret=<secret>

7.  Transfer some ADA for presale:
    > python3 -m tcr.buybot --network=testnet --src=testnet2 --dst=addr_test1qqmd54x5tqlj4mw7rtfjmec40eetjm595kjezyc3mxhthuy75v3zsngxtma9ul5efvwuut80dsgqv76zdu8fc72472hsqqzw0p --amount=9000000

8.  Generate the whitelist again:
    > python3 -m tcr.genwhitelist --network=testnet --drop=tn_series_3 --output=whitelist.json

9.  Mint tokens from the whitelist (and continue to general sale):
    > python3 -m tcr.nftmint --network=testnet --mint --whitelist=whitelist.json --drop=tn_series_3

10.  Transfer all tokens to another wallet:
    > python3 -m tcr.buybot --network=testnet --dst=testnet1 --src=testnet2 --all

11.  Burn tokens held by the minting wallet:
    > python3 -m tcr.nftmint --network=testnet --burn --policy=tn_policy1 --confirm

12.  Refund a payment:
    > python3 -m tcr.refund --network=mainnet --src=tcr_mint --utxo=559b16940536fe9b91ab77b391afdb2ed576e3a17179a8cb7acde724e1dd835a

13.  Refund another payment:
    > python3 -m tcr.refund --network=mainnet --src=tcr_mint --utxo=6c869968950ee4e3469d744e8bd33d58f6c327b6430e11db4e2b42149ae57267


# License

This code is released under the [MIT Opensource License](https://en.wikipedia.org/wiki/MIT_License)
you may use and and modify this code as you see fit.  However, this license and
all copyright attributions must remain in place.


# Commission

TCR has spent a significant amount of time, energy, and money creating this package.
As such, TCR has placed into the code a small comission for ourself.  When an NFT
is minted to an external address the code will also transfer the min utxo value to
the TCR wallet.  Currently this is just 1 ADA.  You can of course remove this
from the code but it will be highly appreciated if you leave it in.  Consider it
a small tip to the development team at TCR.


# Conclusion

We at TCR hope you find this software useful.  Feel free to provide suggestions
on feature requests and other ways to improve it.
