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
PROPOSER_PK=
INFURA_KEY=
NETWORK=
```

### Add Owner

```shell
python -m src.add_owner --parent PARENT --index-from INDEX_FROM --num-safes NUM_SAFES --new-owner NEW_OWNER --sub-safes SUB_SAFES
```

### Airdrop Multi Exec

#### Redeem

```shell
python -m src.exec --command REDEEM --parent PARENT --index-from INDEX_FROM --num-safes NUM_SAFES
```

#### Claim

```shell
python -m src.exec --command CLAIM --parent PARENT --index-from INDEX_FROM --num-safes NUM_SAFES
```

## Run Tests

```shell
python -m pytest tests
```


## Docker


### Build & Run
```shell
docker build . -t subsafe-commander
docker run -it --rm --env-file .env --command CLAIM --parent PARENT --index-from INDEX_FROM --num-safes NUM_SAFES
```

### Pull & Run

```shell
docker run --pull=always -it --rm --env-file .env ghcr.io/bh2smith/subsafe-commander:main --command CLAIM --parent PARENT --index-from INDEX_FROM --num-safes NUM_SAFES
```
 