from web3 import Web3
from web3.providers.rpc import HTTPProvider
from web3.middleware import ExtraDataToPOAMiddleware #Necessary for POA chains
from datetime import datetime
import json
import pandas as pd
import time


def connect_to(chain):
    if chain == 'avax':  # The source contract chain is avax
        api_url = f"https://api.avax-test.network/ext/bc/C/rpc" #AVAX C-chain testnet
    elif chain == 'bsc':  # The destination contract chain is bsc
        api_url = f"https://data-seed-prebsc-1-s1.binance.org:8545/" #BSC testnet
    else:
        raise ValueError(f"Invalid chain: {chain}")
    
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


def sign_and_send(contract, function, signer, argdict, confirm=True, force_nonce=0):
    """
    Helper function to sign and send transactions
    """
    w3 = contract.w3
    nonce = w3.eth.get_transaction_count(signer.address)
    if nonce <= force_nonce:
        nonce = force_nonce + 1
    
    contract_func = getattr(contract.functions, function)
    try:
        tx = contract_func(**argdict).build_transaction(
            {'nonce': nonce, 'gasPrice': w3.eth.gas_price, 'from': signer.address,
             'gas': 10 ** 6})
    except Exception as e:
        print(f"ERROR: in sign_and_send, failed to build transaction (function = {function})\n{e}")
        return None, nonce
    
    signed_tx = w3.eth.account.sign_transaction(tx, signer.key)

    try:
        w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    except Exception as e:
        print(f"ERROR: in sign_and_send, failed to send transaction (function = {function})\n{e}")
        return None, nonce

    if confirm:
        tx_receipt = w3.eth.wait_for_transaction_receipt(signed_tx.hash)
        if tx_receipt.status:
            print(f"SUCCESS: Transaction confirmed for '{function}' at block {tx_receipt.blockNumber}")
        else:
            print(f"ERROR: Transaction failed '{function}'\n{signed_tx.hash.hex()}")

    return signed_tx.hash.hex(), nonce


def scan_blocks(chain, contract_info="contract_info.json"):
    """
        chain - (string) should be either "source" or "destination"
        Scan the last 5 blocks of the specified chain
        Look for 'Deposit' events on the source chain and 'Unwrap' events on the destination chain
        When Deposit events are found on the source chain, call the 'wrap' function the destination chain
        When Unwrap events are found on the destination chain, call the 'withdraw' function on the source chain
    """

    # This is different from Bridge IV where chain was "avax" or "bsc"
    if chain not in ['source','destination']:
        print( f"Invalid chain: {chain}" )
        return 0
    
    # Load contract information
    source_contracts = get_contract_info('source', contract_info)
    destination_contracts = get_contract_info('destination', contract_info)
    if not source_contracts or not destination_contracts:
        return 0
    
    # Load private key
    try:
        with open('sk.txt', 'r') as f:
            private_key = f.read().strip()
    except Exception as e:
        print(f"Failed to read private key: {e}")
        return 0
    
    # Connect to both chains
    source_w3 = connect_to('avax')
    destination_w3 = connect_to('bsc')
    
    # Create contract instances
    source_contract = source_w3.eth.contract(
        address=source_contracts['address'], 
        abi=source_contracts['abi']
    )
    destination_contract = destination_w3.eth.contract(
        address=destination_contracts['address'], 
        abi=destination_contracts['abi']
    )
    
    # Get the account from private key
    account = source_w3.eth.account.from_key(private_key)
    
    # Get current block numbers
    source_current_block = source_w3.eth.get_block_number()
    destination_current_block = destination_w3.eth.get_block_number()
    
    print(f"Current blocks - Source: {source_current_block}, Destination: {destination_current_block}")
    
    if chain == 'source':
        # Scan last 20 blocks on source chain for Deposit events
        start_block = max(0, source_current_block - 19)
        end_block = source_current_block
        print(f"Scanning blocks {start_block} to {end_block} on source chain for Deposit events")
        
        try:
            # Get Deposit events from source contract
            deposit_filter = source_contract.events.Deposit.create_filter(
                from_block=start_block, 
                to_block=end_block
            )
            deposit_events = deposit_filter.get_all_entries()
            
            print(f"Found {len(deposit_events)} Deposit events")
            
            for event in deposit_events:
                print(f"Processing Deposit event: token={event.args['token']}, recipient={event.args['recipient']}, amount={event.args['amount']}")
                
                # Call wrap function on destination chain
                try:
                    # Get current nonce for destination chain
                    current_destination_nonce = destination_w3.eth.get_transaction_count(account.address)
                    
                    # Build the wrap transaction
                    wrap_txn = destination_contract.functions.wrap(
                        event.args['token'],
                        event.args['recipient'],
                        event.args['amount']
                    ).build_transaction({
                        'from': account.address,
                        'gas': 300000,
                        'gasPrice': destination_w3.eth.gas_price,
                        'nonce': current_destination_nonce,
                    })
                    
                    # Sign and send the transaction
                    signed_txn = destination_w3.eth.account.sign_transaction(wrap_txn, private_key)
                    tx_hash = destination_w3.eth.send_raw_transaction(signed_txn.raw_transaction)
                    print(f"Sent wrap transaction: {tx_hash.hex()}")
                    
                    # Wait for confirmation
                    tx_receipt = destination_w3.eth.wait_for_transaction_receipt(tx_hash)
                    if tx_receipt.status:
                        print(f"Wrap transaction confirmed at block {tx_receipt.blockNumber}")
                    else:
                        print(f"Wrap transaction failed!")
                    
                except Exception as e:
                    print(f"Failed to call wrap function: {e}")
                    
        except Exception as e:
            print(f"Error scanning source chain: {e}")
    
    elif chain == 'destination':
        # Scan last 20 blocks on destination chain for Unwrap events
        start_block = max(0, destination_current_block - 19)
        end_block = destination_current_block
        print(f"Scanning blocks {start_block} to {end_block} on destination chain for Unwrap events")
        
        try:
            # Get Unwrap events from destination contract
            unwrap_filter = destination_contract.events.Unwrap.create_filter(
                from_block=start_block, 
                to_block=end_block
            )
            unwrap_events = unwrap_filter.get_all_entries()
            
            print(f"Found {len(unwrap_events)} Unwrap events")
            
            for event in unwrap_events:
                print(f"Processing Unwrap event: underlying_token={event.args['underlying_token']}, wrapped_token={event.args['wrapped_token']}, frm={event.args['frm']}, to={event.args['to']}, amount={event.args['amount']}")
                
                # Call withdraw function on source chain
                try:
                    # Get current nonce for source chain
                    current_source_nonce = source_w3.eth.get_transaction_count(account.address)
                    
                    # Build the withdraw transaction
                    withdraw_txn = source_contract.functions.withdraw(
                        event.args['underlying_token'],
                        event.args['to'],
                        event.args['amount']
                    ).build_transaction({
                        'from': account.address,
                        'gas': 300000,
                        'gasPrice': source_w3.eth.gas_price,
                        'nonce': current_source_nonce,
                    })
                    
                    # Sign and send the transaction
                    signed_txn = source_w3.eth.account.sign_transaction(withdraw_txn, private_key)
                    tx_hash = source_w3.eth.send_raw_transaction(signed_txn.raw_transaction)
                    print(f"Sent withdraw transaction: {tx_hash.hex()}")
                    
                    # Wait for confirmation
                    tx_receipt = source_w3.eth.wait_for_transaction_receipt(tx_hash)
                    if tx_receipt.status:
                        print(f"Withdraw transaction confirmed at block {tx_receipt.blockNumber}")
                    else:
                        print(f"Withdraw transaction failed!")
                    
                except Exception as e:
                    print(f"Failed to call withdraw function: {e}")
                    
        except Exception as e:
            print(f"Error scanning destination chain: {e}")
    
    return 1


def register_tokens(contract_info="contract_info.json"):
    """
    Register tokens on both source and destination contracts
    """
    try:
        with open('sk.txt', 'r') as f:
            private_key = f.read().strip()
    except Exception as e:
        print(f"Failed to read private key: {e}")
        return 0
    
    # Load token addresses from CSV
    try:
        df = pd.read_csv('erc20s.csv')
    except Exception as e:
        print(f"Failed to read erc20s.csv: {e}")
        return 0
    
    # Connect to both chains
    source_w3 = connect_to('avax')
    destination_w3 = connect_to('bsc')
    
    # Get contract info
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
    
    account = source_w3.eth.account.from_key(private_key)
    
    # Register tokens on source chain (Avalanche)
    avax_tokens = df[df['chain'] == 'avax']['address'].tolist()
    for token_address in avax_tokens:
        try:
            nonce = source_w3.eth.get_transaction_count(account.address)
            register_txn = source_contract.functions.registerToken(token_address).build_transaction({
                'from': account.address,
                'gas': 200000,
                'gasPrice': source_w3.eth.gas_price,
                'nonce': nonce,
            })
            
            signed_txn = source_w3.eth.account.sign_transaction(register_txn, private_key)
            tx_hash = source_w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            print(f"Registered token {token_address} on source chain: {tx_hash.hex()}")
            
            tx_receipt = source_w3.eth.wait_for_transaction_receipt(tx_hash)
            if tx_receipt.status:
                print(f"Token registration confirmed on source chain")
            
        except Exception as e:
            print(f"Failed to register token {token_address} on source chain: {e}")
    
    # Create tokens on destination chain (BSC)
    bsc_tokens = df[df['chain'] == 'bsc']['address'].tolist()
    current_nonce = destination_w3.eth.get_transaction_count(account.address)
    
    for i, token_address in enumerate(bsc_tokens):
        try:
            # Use sequential nonce
            nonce = current_nonce + i
            create_txn = destination_contract.functions.createToken(
                token_address,
                "Wrapped Token",
                "wTOKEN"
            ).build_transaction({
                'from': account.address,
                'gas': 500000,
                'gasPrice': destination_w3.eth.gas_price,
                'nonce': nonce,
            })
            
            signed_txn = destination_w3.eth.account.sign_transaction(create_txn, private_key)
            tx_hash = destination_w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            print(f"Created wrapped token for {token_address} on destination chain: {tx_hash.hex()}")
            
            tx_receipt = destination_w3.eth.wait_for_transaction_receipt(tx_hash)
            if tx_receipt.status:
                print(f"Token creation confirmed on destination chain")
            
        except Exception as e:
            print(f"Failed to create token for {token_address} on destination chain: {e}")
    
    return 1


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python bridge.py [source|destination|register]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "register":
        register_tokens()
    elif command in ["source", "destination"]:
        scan_blocks(command)
    else:
        print("Invalid command. Use 'source', 'destination', or 'register'")
        sys.exit(1)
