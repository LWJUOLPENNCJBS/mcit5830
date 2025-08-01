from web3 import Web3
from web3.providers.rpc import HTTPProvider
from web3.middleware import ExtraDataToPOAMiddleware #Necessary for POA chains
from pathlib import Path
import json
from datetime import datetime
import pandas as pd


def scan_blocks(chain, start_block, end_block, contract_address, eventfile='deposit_logs.csv'):
    """
    chain - string (Either 'bsc' or 'avax')
    start_block - integer first block to scan
    end_block - integer last block to scan
    contract_address - the address of the deployed contract

	This function reads "Deposit" events from the specified contract, 
	and writes information about the events to the file "deposit_logs.csv"
    """
    if chain == 'avax':
        api_url = f"https://api.avax-test.network/ext/bc/C/rpc" #AVAX C-chain testnet

    if chain == 'bsc':
        api_url = f"https://data-seed-prebsc-1-s1.binance.org:8545/" #BSC testnet

    if chain in ['avax','bsc']:
        w3 = Web3(Web3.HTTPProvider(api_url))
        # inject the poa compatibility middleware to the innermost layer
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    else:
        w3 = Web3(Web3.HTTPProvider(api_url))

    DEPOSIT_ABI = json.loads('[ { "anonymous": false, "inputs": [ { "indexed": true, "internalType": "address", "name": "token", "type": "address" }, { "indexed": true, "internalType": "address", "name": "recipient", "type": "address" }, { "indexed": false, "internalType": "uint256", "name": "amount", "type": "uint256" } ], "name": "Deposit", "type": "event" }]')
    contract = w3.eth.contract(address=contract_address, abi=DEPOSIT_ABI)

    arg_filter = {}

    if start_block == "latest":
        start_block = w3.eth.get_block_number()
    if end_block == "latest":
        end_block = w3.eth.get_block_number()

    if end_block < start_block:
        print( f"Error end_block < start_block!" )
        print( f"end_block = {end_block}" )
        print( f"start_block = {start_block}" )

    if start_block == end_block:
        print( f"Scanning block {start_block} on {chain}" )
    else:
        print( f"Scanning blocks {start_block} - {end_block} on {chain}" )

    # List to store all events data
    all_events_data = []

    if end_block - start_block < 30:
        event_filter = contract.events.Deposit.create_filter(from_block=start_block,to_block=end_block,argument_filters=arg_filter)
        events = event_filter.get_all_entries()
        print( f"Got {len(events)} entries for blocks {start_block}-{end_block}" )
        
        # Process events
        for evt in events:
            data = {
                'chain': chain,
                'token': evt.args['token'],
                'recipient': evt.args['recipient'],
                'amount': evt.args['amount'],
                'transactionHash': evt.transactionHash.hex(),
                'address': evt.address,
                'date': datetime.now().strftime("%m/%d/%Y %H:%M:%S")
            }
            all_events_data.append(data)
    else:
        for block_num in range(start_block,end_block+1):
            event_filter = contract.events.Deposit.create_filter(from_block=block_num,to_block=block_num,argument_filters=arg_filter)
            events = event_filter.get_all_entries()
            print( f"Got {len(events)} entries for block {block_num}" )
            
            # Process events for this block
            for evt in events:
                data = {
                    'chain': chain,
                    'token': evt.args['token'],
                    'recipient': evt.args['recipient'],
                    'amount': evt.args['amount'],
                    'transactionHash': evt.transactionHash.hex(),
                    'address': evt.address,
                    'date': datetime.now().strftime("%m/%d/%Y %H:%M:%S")
                }
                all_events_data.append(data)

    # Create DataFrame and write to CSV
    if all_events_data:
        df = pd.DataFrame(all_events_data)
        df.to_csv(eventfile, index=False)
        print(f"Wrote {len(all_events_data)} events to {eventfile}")
    else:
        print("No events found in the specified block range")
        # Create empty CSV with headers if no events found
        empty_df = pd.DataFrame(columns=['chain', 'token', 'recipient', 'amount', 'transactionHash', 'address', 'date'])
        empty_df.to_csv(eventfile, index=False)
