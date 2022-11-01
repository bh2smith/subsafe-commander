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
 