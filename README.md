Safe Transaction Batching

# Installation

```shell
python3 -m venv env
source ./env/bin/activate
pip install -r requirements.txt
cp .env.sample .env    <----- Copy your Dune credentials here!
```

## Add Owner(s)

This project has a script to add owners to safes which are owned by other safes
(using the private key of a parent safe's owner)

For example, the following dune queries show "fleets" of Safes owned by a single parent Safe
(this is not a comprehensive)

For all fleets check here: [https://dune.com/queries/1436503](https://dune.com/queries/1436503)

For your own, put your parent safe address in here:

- [Mainnet](https://dune.com/queries/1436503?Blockchain=ethereum)
- [Gnosis Chain](https://dune.com/queries/1436503?Blockchain=gnosis)

With environment variables

```shell
# General defaults
NETWORK=mainnet
INDEX_FROM=0
NUM_SAFES=80 <-- This is the CAP.
# Must be provided
INFURA_KEY=
PARENT_SAFE=
# Private key of Parent Owner
PROPOSER_PK=
DUNE_API_KEY=
```

## General Usage

```shell
python -m src.exec --command $COMMAND --parent $PARENT_SAFE --index-from $INDEX_FROM --num-safes $NUM_SAFES [--sub-safes SUB_SAFES]
```

with currently supported commands

```shell
--command {CLAIM,REDEEM,ADD_OWNER,setDelegate,clearDelegate}
```

Note that `--sub-safes` is optional. If not provided then a `DUNE_API_KEY` will be expected (to
fetch them).

### Add Owner

Requires additional arguments `--new-owner NEW_OWNER`

### Airdrop

Individual commands are supported as well as "Full Claim" (--command FullClaim)
which combines delegate, redeem and claim into a single transaction. 
Note: that this is **not** recommended for more than 26 SubSafes at a time

#### Redeem

Requires no additional arguments

#### Claim

Requires no additional arguments. It sets the beneficiary of the SAFE tokens to `$PARENT_SAFE`.

### Snapshot

#### setDelegate

Requires no additional arguments. It sets the delegate of "safe.eth" namespace to `$PARENT_SAFE`.

#### clearDelegate

Requires no additional arguments.

## Run Tests

```shell
python -m pytest tests
```

## Docker

### Build & Run

```shell
docker build . -t subsafe-commander
docker run -it --rm --env-file .env --command $COMMAND --parent $PARENT_SAFE --index-from $INDEX_FROM --num-safes $NUM_SAFES
```

### Pull & Run

```shell
docker run --pull=always -it --rm \
  --env-file .env \
  ghcr.io/bh2smith/subsafe-commander:main \
  --command $COMMAND \
  --parent $PARENT_SAFE \
  --index-from $INDEX_FROM \
  --num-safes $NUM_SAFES
```
 