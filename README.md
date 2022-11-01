# SubSafe Commander for Safe Transaction Batching

Control your Fleet of safes from the command line! Claim your $SAFE token airdrop in style. 

## TLDR;

To Claim $SAFE Airdrop on behalf of a family of sub-safes (with signing threshold 1) all of which
are owned by a single "parent" safe, do this:

Create an `.env` file with the following values:

```shell
INFURA_KEY=
PARENT_SAFE=
# Private key of Parent Owner
PROPOSER_PK=
DUNE_API_KEY=
```

Run the following (full-claim script)

```shell
docker run --pull=always -it --rm \
  --env-file .env \
  ghcr.io/bh2smith/subsafe-commander:main \
  --command FullClaim \
  --parent $PARENT_SAFE
```

If you don't have a `DUNE_API_KEY`, you can also provide an additional argument `--sub-safes` with a
comma separated list of safes owned by `$PARENT_SAFE`.

## Find your Sub-Safes

For example, the following dune query shows "fleets" of Safes owned by a single parent
(this is not a comprehensive list)

For all fleets on all networks check
here: [https://dune.com/queries/1436503](https://dune.com/queries/1436503)

## General Usage

With environment variables

```shell
# General defaults
NETWORK=mainnet
INDEX_FROM=0
NUM_SAFES=90 <-- This is the CAP.
# Must be provided
INFURA_KEY=
PARENT_SAFE=
# Private key of Parent Owner
PROPOSER_PK=
DUNE_API_KEY=
```

this project exposes the following contract method calls:

```shell
docker run --pull=always -it --rm \
  --env-file .env \
  ghcr.io/bh2smith/subsafe-commander:main \
  --command $COMMAND \
  --parent $PARENT_SAFE \
  --index-from $INDEX_FROM \ 
  --num-safes $NUM_SAFES \
  [--sub-safes SUB_SAFES]
```

with currently supported commands

```shell
--command {CLAIM,REDEEM,ADD_OWNER,setDelegate,clearDelegate}
```

Note that `--sub-safes` is optional. If not provided then a `DUNE_API_KEY` will be expected (to
fetch them).

## Safe: Add Owner

Requires additional arguments `--new-owner NEW_OWNER`

## Airdrop

Individual commands are supported as well as "Full Claim" (--command FullClaim)
which combines delegate, redeem and claim into a single transaction.
Note: that this is **not** recommended for more than 26 SubSafes at a time

#### Redeem

Requires no additional arguments. Note that no token transfers are expected to occur during
redemption, these happen on claim (and claim comes after redeem).

#### Claim

Requires no additional arguments. It sets the beneficiary of the SAFE tokens to `$PARENT_SAFE`.

#### Examples

- REDEEM with 5
  sub-safes: [0x0b1af8434e9ac016f4412f12c87bfd7b3a05ca3f0d23ac60b263aaf42a76db4a](https://etherscan.io/tx/0x0b1af8434e9ac016f4412f12c87bfd7b3a05ca3f0d23ac60b263aaf42a76db4a)
- CLAIM with 5
  sub-safes: [0xa3cf9ad343d167d1036d466733727713af0c730ce4dd9032168439448031c0d1](https://etherscan.io/tx/0xa3cf9ad343d167d1036d466733727713af0c730ce4dd9032168439448031c0d1)
- REDEEM with 75
  sub-safes: [0x8f14a5681e805b5ab6e7d7d62393fa37de594c17b8d0d6563adaf7f7150d6377](https://etherscan.io/tx/0x8f14a5681e805b5ab6e7d7d62393fa37de594c17b8d0d6563adaf7f7150d6377)

For more examples, see some gas
benchmarking [here](https://github.com/bh2smith/subsafe-commander/issues/4)

### Full Claim

This project also supports a full claim cycle, which is the combination of (delegate, redeem and
claim). However, due to gas limitations this is restricted to a maximum of 30 safes.

## Snapshot

#### setDelegate

Requires no additional arguments. It sets the delegate of "safe.eth" namespace to `$PARENT_SAFE`.

#### clearDelegate

Requires no additional arguments.

# Installation & Local Development

```shell
python3 -m venv env
source ./env/bin/activate
pip install -r requirements.txt
cp .env.sample .env    <----- Copy your Dune credentials here!
```

## Run Tests

```shell
python -m pytest tests
```

## Docker

### Build Locally & Run

```shell
git clone git@github.com:bh2smith/subsafe-commander.git
cd subsafe-commander
docker build . -t subsafe-commander
docker run -it --rm --env-file .env --command $COMMAND --parent $PARENT_SAFE --index-from $INDEX_FROM --num-safes $NUM_SAFES
```

### Pull From Anywhere & Run

```shell
docker run --pull=always -it --rm \
  --env-file .env \
  ghcr.io/bh2smith/subsafe-commander:main \
  --command $COMMAND \
  --parent $PARENT_SAFE \
  --index-from $INDEX_FROM \
  --num-safes $NUM_SAFES
```

Note, this commands expects you to have a `.env` file in your present working directory!
 