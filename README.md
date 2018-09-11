# Create Private Ethereum Blockchain

Quickly set up and run a local private Ethereum blockchain.

Customizable Genesis block (difficulty, initial balance, ...)

Connected to Ethereum/Mist Wallet, where you can deploy and test your contracts.
Note : Open your wallet after starting your blockchain

## This script provides easy functions to pilot geth:

 * ./pgeth.py init: this function create the blockchain with an account. Use it the first time.
 * ./pgeth.py start: this function starts geth daemon and mining. Use it when you want to use geth.
 * ./pgeth.py stop: this functions stops geth. Use it not to burn your CPU on stupid blocks.
 * ./pgeth.py destroy: A function to delete quickly your private blockchain.

## Config

You can create a pgeth_config.json file (or created for you on first run) with 
the following keys:

* datadir  : Location of where to put all required files and chaindata
* password : secret key password to use
* geth     : location of geth executable 

Example: 

```
{
  "datadir": "~/private_ethereum_blockchain",
  "password": "apasswordtochange"
}
```

## Contributors

Laurent MALLET
Regis PIETRASZEWSKI
Chris Griffith (cdgriffith)
