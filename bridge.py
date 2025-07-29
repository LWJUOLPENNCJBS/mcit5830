from web3 import Web3
from web3.providers.rpc import HTTPProvider
from web3.middleware import ExtraDataToPOAMiddleware #Necessary for POA chains
from datetime import datetime
import json
import pandas as pd


def connect_to(chain):
    if chain == 'source':  # The source contract chain is avax
        api_url = f"https://api.avax-test.network/ext/bc/C/rpc" #AVAX C-chain testnet

    if chain == 'destination':  # The destination contract chain is bsc
        api_url = f"https://data-seed-prebsc-1-s1.binance.org:8545/" #BSC testnet

    if chain in ['source','destination']:
        w3 = Web3(Web3.HTTPProvider(api_url))
        # inject the poa compatibility middleware to the innermost layer
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    return w3


def get_contract_info(chain, contract_info):
    """
        Load the contract_info file into a dictionary
        This function is used by the autograder and will likely be useful to you
    """
    try:
        with open(contract_info, 'r')  as f:
            contracts = json.load(f)
    except Exception as e:
        print( f"Failed to read contract info\nPlease contact your instructor\n{e}" )
        return 0
    return contracts[chain]



def scan_blocks(chain, contract_info="contract_info.json"):
    """
        chain - (string) should be either "source" or "destination"
        Scan the last 5 blocks of the source and destination chains
        Look for 'Deposit' events on the source chain and 'Unwrap' events on the destination chain
        When Deposit events are found on the source chain, call the 'wrap' function the destination chain
        When Unwrap events are found on the destination chain, call the 'withdraw' function on the source chain
    """

    # This is different from Bridge IV where chain was "avax" or "bsc"
    if chain not in ['source','destination']:
        print( f"Invalid chain: {chain}" )
        return 0
    
    # Load contract information
    contracts = get_contract_info(chain, contract_info)
    if not contracts:
        return 0
    
    # Load private key
    try:
        with open('sk.txt', 'r') as f:
            private_key = f.read().strip()
    except Exception as e:
        print(f"Failed to read private key: {e}")
        return 0
    
    # Connect to both chains
    source_w3 = connect_to('source')
    destination_w3 = connect_to('destination')
    
    # Get contract info for both chains
    source_contracts = get_contract_info('source', contract_info)
    destination_contracts = get_contract_info('destination', contract_info)
    
    # Create contract instances
    source_contract = source_w3.eth.contract(
        address=source_contracts['address'], 
        abi=source_contracts['abi']
    )
    destination_contract = destination_w3.eth.contract(
        address=destination_contracts['address'], 
        abi=destination_contracts['abi']
    )
    
    # Get current block numbers
    source_current_block = source_w3.eth.get_block_number()
    destination_current_block = destination_w3.eth.get_block_number()
    
    # Scan last 5 blocks on source chain for Deposit events
    print(f"Scanning blocks {source_current_block-4} to {source_current_block} on source chain for Deposit events")
    for block_num in range(source_current_block-4, source_current_block+1):
        try:
            # Get Deposit events from source contract
            deposit_filter = source_contract.events.Deposit.create_filter(
                from_block=block_num, 
                to_block=block_num
            )
            deposit_events = deposit_filter.get_all_entries()
            
            for event in deposit_events:
                print(f"Found Deposit event: token={event.args['token']}, recipient={event.args['recipient']}, amount={event.args['amount']}")
                
                # Call wrap function on destination chain
                try:
                    # Get the account from private key
                    account = source_w3.eth.account.from_key(private_key)
                    
                    # Build the wrap transaction
                    wrap_txn = destination_contract.functions.wrap(
                        event.args['token'],
                        event.args['recipient'],
                        event.args['amount']
                    ).build_transaction({
                        'from': account.address,
                        'gas': 200000,
                        'gasPrice': destination_w3.eth.gas_price,
                        'nonce': destination_w3.eth.get_transaction_count(account.address),
                    })
                    
                    # Sign and send the transaction
                    signed_txn = destination_w3.eth.account.sign_transaction(wrap_txn, private_key)
                    tx_hash = destination_w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                    print(f"Sent wrap transaction: {tx_hash.hex()}")
                    
                except Exception as e:
                    print(f"Failed to call wrap function: {e}")
                    
        except Exception as e:
            print(f"Error scanning block {block_num} on source chain: {e}")
    
    # Scan last 5 blocks on destination chain for Unwrap events
    print(f"Scanning blocks {destination_current_block-4} to {destination_current_block} on destination chain for Unwrap events")
    for block_num in range(destination_current_block-4, destination_current_block+1):
        try:
            # Get Unwrap events from destination contract
            unwrap_filter = destination_contract.events.Unwrap.create_filter(
                from_block=block_num, 
                to_block=block_num
            )
            unwrap_events = unwrap_filter.get_all_entries()
            
            for event in unwrap_events:
                print(f"Found Unwrap event: underlying_token={event.args['underlying_token']}, wrapped_token={event.args['wrapped_token']}, frm={event.args['frm']}, to={event.args['to']}, amount={event.args['amount']}")
                
                # Call withdraw function on source chain
                try:
                    # Get the account from private key
                    account = source_w3.eth.account.from_key(private_key)
                    
                    # Build the withdraw transaction
                    withdraw_txn = source_contract.functions.withdraw(
                        event.args['underlying_token'],
                        event.args['to'],
                        event.args['amount']
                    ).build_transaction({
                        'from': account.address,
                        'gas': 200000,
                        'gasPrice': source_w3.eth.gas_price,
                        'nonce': source_w3.eth.get_transaction_count(account.address),
                    })
                    
                    # Sign and send the transaction
                    signed_txn = source_w3.eth.account.sign_transaction(withdraw_txn, private_key)
                    tx_hash = source_w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                    print(f"Sent withdraw transaction: {tx_hash.hex()}")
                    
                except Exception as e:
                    print(f"Failed to call withdraw function: {e}")
                    
        except Exception as e:
            print(f"Error scanning block {block_num} on destination chain: {e}")
    
    return 1
