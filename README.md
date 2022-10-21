Safe Transaction Batching

# Installation

```shell
python3 -m venv env
source ./env/bin/activate
pip install -r requirements.txt
cp .env.sample .env    <----- Copy your Dune credentials here!
```

## Add Owner(s)

This project has a script to add owners to safes which are owned by other safes (using the private key of a parent safe
owner)

For example, if you check these dune queries, you will find lists of safes owned by a single parent safe (this is not a
comprehensive list)

For all fleets check here: [https://dune.com/queries/1436503](https://dune.com/queries/1436503)

for your own put your parent safe address in here:
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
python -m src.add_owner 
  --parent PARENT \
  --new-owner NEW_OWNER \
  --sub-safes SUB_SAFES
```


### Airdrop Multi Exec


#### Redeem
```shell
python -m src.exec \
  --command REDEEM \ 
  --parent PARENT \
  --index-from INDEX_FROM \
  --index-to INDEX_FROM
```

#### Claim
```shell
python -m src.exec \
  --command CLAIM \ 
  --parent PARENT \
  --index-from INDEX_FROM \
  --index-to INDEX_FROM 
```

## Run Tests

```shell
python -m pytest tests
```
