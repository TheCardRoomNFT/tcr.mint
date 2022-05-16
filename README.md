# [The Card Room](https://thecardroom.io)

The Card Room is a Cardano based NFT platform, a unique gallery of collectable NFT playing cards, individually minted on the Cardano blockchain.  This codebase represents a collection of scripts we have created and found useful for minting NFTs on the Cardano blockchain.


# Utility Programs
- NFT art engine for creating metadata and layered images
- IPFS upload
- Vending machine
  - payment processing
  - NFT minting


# Prerequisites

These scripts assume that cardano-node, cardano-addresses, cardano-db-sync, and are installed and running on the system.  Please see details of
how to install and run these on the input-output-hk github account:
  - [cardano-node](https://github.com/input-output-hk/cardano-node)
  - [cardano-db-sync](https://github.com/input-output-hk/cardano-db-sync)
  - [cardano-addresses](https://github.com/input-output-hk/cardano-addresses)

The scripts also require some environment variables to be set (click the link below for detailed installation instructions):
  - CARDANO_NODE_SOCKET_PATH
  - TESTNET_CARDANO_NODE_SOCKET_PATH
  - MAINNET_CARDANO_NODE_SOCKET_PATH

If you don't want to build from source, the installation instructions below show
where to download pre-build binaries from.


# Installation

  Detailed [Installation Instructions](INSTALL.md)


# Create a NFT drop
Below is a list of commands used to create a 10k NFT drop from a set of image layers.  It is an example run on testnet using nft/testnet/tn_project1 as an example.  If starting from scratch, run the following commands to prepare everything for payment processing and minting.

Parameters used in this example are below  It is expected that these will be modified as necessary for a new project.
- network=testnet
- wallet name = tn_project_mint
- policy name = tn_project_policy1
- project name = tn_project1

1.  **Create a wallet:**  This wallet will be used to monitor incoming transactions.  The data for this wallet (addresses, private keys, seed phrase, and others) are stored in several files in the **wallet/testnet** directory.  It is of utmost importance to backup this data and keep it secure.  If this data is lost, there is no way to recover it.  It is your responsibility to understand the risks, backup the data, and keep it secure.
  - **~/cardano/tcr.mint$ python3 -m tcr.nftmint --network=testnet --create-wallet=tn_project_mint<br>**
    Log File: log/testnet/nftmint_20220515_105906.log<br>
    2022-05-15 10:59:06,941:INFO:testnet: TESTNET Payment Processor / NFT Minter<br>
    2022-05-15 10:59:06,941:INFO:testnet: Copyright 2021-2022 The Card Room<br>
    2022-05-15 10:59:06,941:INFO:testnet: Network: testnet<br>
    2022-05-15 10:59:07,281:INFO:testnet: Database Chain Metadata: 2019-07-24 20:20:16 / testnet<br>
    2022-05-15 10:59:07,281:INFO:testnet: Database Size: 16 GB<br>
    2022-05-15 10:59:07,281:INFO:testnet: Cardano Node Tip Slot: 58268308<br>
    2022-05-15 10:59:07,281:INFO:testnet:  Database Latest Slot: 58268308<br>
    2022-05-15 10:59:07,281:INFO:testnet: Sync Progress: 99.99997377865925<br>
    2022-05-15 10:59:08,966:INFO:testnet: Successfully created new wallet: <tn_project_mint><br>

2.  **Create a Policy ID**: Next, create a policy id.  The default is to lock in 12 months.  Use the --months parameter to override the default and specify in how many months the policy will be locked.  The policy also has sensitive data equal in importance to that of the wallet.  These files are stored in **policy/testnet** It is your responsibility to understand the risks, backup the data, and keep it secure.  The first example uses the default to lock the policy in 12 months.
  - **~/cardano/tcr.mint$ python3 -m tcr.nftmint --network=testnet --wallet=tn_project_mint --create-policy=tn_project_policy1<br>**
Log File: log/testnet/nftmint_20220515_110933.log<br>
2022-05-15 11:09:33,177:INFO:testnet: TESTNET Payment Processor / NFT Minter<br>
2022-05-15 11:09:33,177:INFO:testnet: Copyright 2021-2022 The Card Room<br>
2022-05-15 11:09:33,177:INFO:testnet: Network: testnet<br>
2022-05-15 11:09:33,442:INFO:testnet: Database Chain Metadata: 2019-07-24 20:20:16 / testnet<br>
2022-05-15 11:09:33,442:INFO:testnet: Database Size: 16 GB<br>
2022-05-15 11:09:33,442:INFO:testnet: Cardano Node Tip Slot: 58268918<br>
2022-05-15 11:09:33,442:INFO:testnet:  Database Latest Slot: 58268918<br>
2022-05-15 11:09:33,442:INFO:testnet: Sync Progress: 99.99995552731876<br>
2022-05-15 11:09:33,683:INFO:testnet: Successfully created new policy:<br> tn_project_policy1 / 34036f8c11712465a661aa058a30d6ead6ca8cd630ab97aac3fb8674<br>
2022-05-15 11:09:33,684:INFO:testnet: Expires at slot: 89804918<br>
2022-05-15 11:09:33,684:INFO:testnet: Expires in: 12 months<br>

  Modify the default with --months to lock in 3 months:
  - **~/cardano/tcr.mint$ python3 -m tcr.nftmint --network=testnet --wallet=tn_project_mint --create-policy=tn_project_policy2 --months=3**<br>
Log File: log/testnet/nftmint_20220515_111122.log<br>
2022-05-15 11:11:22,608:INFO:testnet: TESTNET Payment Processor / NFT Minter<br>
2022-05-15 11:11:22,608:INFO:testnet: Copyright 2021-2022 The Card Room<br>
2022-05-15 11:11:22,608:INFO:testnet: Network: testnet<br>
2022-05-15 11:11:22,773:INFO:testnet: Database Chain Metadata: 2019-07-24 20:20:16 / testnet<br>
2022-05-15 11:11:22,773:INFO:testnet: Database Size: 16 GB<br>
2022-05-15 11:11:22,773:INFO:testnet: Cardano Node Tip Slot: 58269055<br>
2022-05-15 11:11:22,773:INFO:testnet:  Database Latest Slot: 58269055<br>
2022-05-15 11:11:22,774:INFO:testnet: Sync Progress: 99.99998672149039<br>
2022-05-15 11:11:22,976:INFO:testnet: Successfully created new policy:<br> tn_project_policy2 / da9627b1e4b4ed53513658cdde296fc6c74565abd688189328cbe139<br>
2022-05-15 11:11:22,976:INFO:testnet: Expires at slot: 66153055<br>
2022-05-15 11:11:22,976:INFO:testnet: Expires in: 3 months<br>

3.  Create directories needed for NFT images and metadata.  Modify as appropriate for your project:
  - mkdir nft/testnet/tn_project1
  - mkdir nft/testnet/tn_project1/nft_img
  - mkdir nft/testnet/tn_project1/nft_metadata

4.  For your own project, create the metadata files that define all the layers and attributes for the drop.  Use **nft/testnet/tn_project1/tn_project1_metametadata.json** as an example.  Other files needed are **nft/testnet/tn_project1/layersetN.json** and **nft/testnet/tn_project1/layersetN_layerY.json**


5.  Create the NFT images from the layer definitions:
  - **:~/cardano/tcr.mint$ python3 -m tcr.nftmint --network=testnet --create-drop=tn_project1 --policy=tn_project_policy1**<br>
Log File: log/testnet/nftmint_20220515_160706.log<br>
2022-05-15 16:07:06,827:INFO:testnet: TESTNET Payment Processor / NFT Minter<br>
2022-05-15 16:07:06,827:INFO:testnet: Copyright 2021-2022 The Card Room<br>
2022-05-15 16:07:06,827:INFO:testnet: Network: testnet<br>
2022-05-15 16:07:06,828:INFO:testnet: Create RNG with SEED: 1652656027<br>
2022-05-15 16:07:06,829:INFO:testnet: Open MetaMetaData: nft/testnet/tn_project1/tn_project1_metametadata.json<br>
2022-05-15 16:07:06,829:INFO:nft: Opening Layer Set: layerset1.json<br>
2022-05-15 16:07:06,846:INFO:nft: layerset1.json = 2880<br>
2022-05-15 16:07:06,846:INFO:nft: Total Combinations: 2880 images, Layer Sets: 1 sets<br>
2022-05-15 16:07:06,847:INFO:nft: NFTs to generate: 100<br>
2022-05-15 16:07:06,847:INFO:nft: Created: 0<br>
2022-05-15 16:07:06,847:INFO:nft: Create: nft/testnet/tn_project1/nft_img/00001_layerset1__0_5_3_2_1_2.jpg<br>
2022-05-15 16:07:06,929:INFO:nft: Verify Unique: nft/testnet/tn_project1/nft_img/00001_layerset1__0_5_3_2_1_2.jpg<br>
2022-05-15 16:07:06,930:INFO:nft: Created: 1<br>
2022-05-15 16:07:06,931:INFO:nft: Create: nft/testnet/tn_project1/nft_img/00002_layerset1__0_4_3_1_1_0.jpg<br>
2022-05-15 16:07:06,954:INFO:nft: Verify Unique: nft/testnet/tn_project1/nft_img/00002_layerset1__0_4_3_1_1_0.jpg<br>
....<br>
....<br>
....<br>
2022-05-15 16:07:09,891:INFO:testnet: Save MetaMetaData: nft/testnet/tn_project1/tn_project1_metametadata.json<br>
2022-05-15 16:07:09,892:INFO:testnet: Successfully created new drop: nft/testnet/tn_project1/tn_project1.json<br>
  - Review the new files in **nft/testnet/tn_project1/nft_img** and **nft/testnet/tn_project1/nft_metadata**.  Verify the images and metadata are correct.  You may paste the contents of a nft_metadata file to https://pool.pm/test/metadata to view the NFT as it would be minted.  Note that at this point the 'image' attribute points to a file on the local filesystem.  Modify as appropriate to simulate the NFT image.  Also note the file **nft/testnet/tn_project1/tn_project1.json**.  This file is a list of all the NFTs available to mint.

6.  Create an account on https://infura.io to use as an IPFS pinning service.  Other services such as https://www.pinata.cloud/ or even your own IPFS node may be used.  However it will require modifying the code to integrate with this codebase.

7.  Upload the NFT images to the IPFS pinning service and modify the NFT metadata to point to the IPFS image instead of the locally stored file.  Note: it will take several hours or even a day to upload a large drop to the IPFS pinning service.
  - **:~/cardano/tcr.mint$ python3 -m tcr.ipfs --projectid=myprojectid --projectsecret=myprojectsecret --network=testnet --drop=tn_project1**<br>
Log File: log/testnet/ipfs_20220515_165824.log<br>
2022-05-15 16:58:24,073:INFO:testnet: TESTNET IPFS Uploader / Metadata Generator<br>
2022-05-15 16:58:24,073:INFO:testnet: Copyright 2021-2022 The Card Room<br>
2022-05-15 16:58:24,073:INFO:testnet: Network: testnet<br>
2022-05-15 16:58:24,073:INFO:testnet: Drop: tn_project1<br>
2022-05-15 16:58:24,075:INFO:testnet: Open NFT Metadata: nft/testnet/tn_project1/nft_metadata/TNx001x0001x1.json<br>
2022-05-15 16:58:24,076:INFO:testnet: Upload: nft/testnet/tn_project1/nft_img/00001_layerset1__0_5_3_2_1_2.jpg / nft/testnet/tn_project1/nft_metadata/TNx001x0001x1.json<br>
2022-05-15 16:58:25,523:INFO:testnet: PIN State: True<br>
2022-05-15 16:58:25,524:INFO:testnet: Saved MetaMetaData: nft/testnet/tn_project1/nft_metadata/TNx001x0001x1.json<br>
2022-05-15 16:58:25,524:INFO:testnet:    Verify: http://ipfs.io/ipfs/QmPBKA9bgZtE1XPcPzBAescdKgXFK8DCp2mpvJX8hz3VUq<br>
2022-05-15 16:58:25,524:INFO:testnet:<br>
  - Again review the new files in **nft/testnet/tn_project1/nft_img** and **nft/testnet/tn_project1/nft_metadata**.  Verify the images and metadata are correct.  This time the nft_metadata files have been modified to reference the IPFS location.  You may paste the contents of a nft_metadata file to https://pool.pm/test/metadata to view the NFT as it would be minted.

8.  Lookup the wallet address to receive payments.  Also make sure the Sync Progress is at least 99.999%
  - **:~/cardano/tcr.mint$ python3 -m tcr.status --network=testnet --wallet=tn_project_mint**<br>
Log File: log/testnet/status_20220515_170502.log<br>
2022-05-15 17:05:03,308:INFO:testnet: Database Chain Metadata: 2019-07-24 20:20:16 / testnet<br>
2022-05-15 17:05:03,308:INFO:testnet: Database Size: 16 GB<br>
2022-05-15 17:05:03,308:INFO:testnet: Cardano Node Tip Slot: 58290175<br>
2022-05-15 17:05:03,309:INFO:testnet:  Database Latest Slot: 58290175<br>
2022-05-15 17:05:03,309:INFO:testnet: Sync Progress: 99.99987338283928<br>
2022-05-15 17:05:03,326:INFO:testnet:    Root address = addr_test1qpvv9sk30rqafysvzwexvmlaenlgzpg260sdc6ccgzwym7gp86eu3ckadsyev5qwp3w99xc4h7y2u4w6w69xh8xkvyqq38lxe0<br>
2022-05-15 17:05:03,326:INFO:testnet:    **Mint address = addr_test1qr0c4lg3392s7tkur5san3lpnq9ky3n67ctj8gtxcsfj0hsp86eu3ckadsyev5qwp3w99xc4h7y2u4w6w69xh8xkvyqqnyu4w9**<br>
2022-05-15 17:05:03,327:INFO:testnet: Presale address = None<br>
2022-05-15 17:05:03,327:INFO:testnet:  Mutate address = None<br>
2022-05-15 17:05:03,327:INFO:testnet:   Stake address = None<br>
tn_project_mint UTXOS:<br>
Total: 0.0 ADA<br>

9.  Monitor incoming payments and mint NFTs
  - **:~/cardano/tcr.mint$ python3 -m tcr.nftmint --network=testnet --mint --drop=tn_project1**<br>
  - As NFTs are minted, the list of available NFTs will be updated: **nft/testnet/tn_project1/tn_project1.json**.


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

This code is released under the [MIT Opensource License](https://en.wikipedia.org/wiki/MIT_License) you may use and and modify this code as you see fit.  However, this license and all copyright attributions must remain in place.


# Commission

TCR has spent a significant amount of time, energy, and money creating this package.  As such, TCR has placed into the code a small comission for ourself.  When an NFT is minted to an external address the code will also transfer the min utxo value to the TCR wallet.  Currently this is just 1 ADA.  You can of course remove this from the code but it will be highly appreciated if you leave it in.  Consider it a small tip to the development team at TCR.


# Conclusion

We at TCR hope you find this software useful.  Feel free to provide suggestions on feature requests and submit PRs.
