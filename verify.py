from web3 import Web3
from eth_account.messages import encode_defunct
import random

def sign_challenge( challenge ):

    w3 = Web3()

    """ To actually claim the NFT you need to write code in your own file, or use another claiming method
    Once you have claimed an NFT you can come back to this file, update the "sk" and submit to codio to 
    prove that you have claimed your NFT.
    
    INSTRUCTIONS:
    1. Run one of the claiming scripts:
       - python claim_nft.py (interactive, finds smallest available token)
       - python claim_token_zero.py (specifically targets token 0)
       - python advanced_nft_strategies.py (combine/repossess strategies)
    
    2. Fund your account with AVAX from a faucet:
       - Chainlink Faucet: https://faucets.chain.link/fuji
       - Avalanche Faucet: https://faucet.avax.network/
    
    3. After successfully claiming an NFT, replace the line below with your private key
    
    This is the only line you need to modify in this file before you submit """
    sk = "YOUR SECRET KEY HERE"  # Replace with your private key after claiming NFT

    acct = w3.eth.account.from_key(sk)

    signed_message = w3.eth.account.sign_message( challenge, private_key = acct.key )

    return acct.address, signed_message.signature


def verify_sig():
    """
        This is essentially the code that the autograder will use to test signChallenge
        We've added it here for testing 
    """
    
    challenge_bytes = random.randbytes(32)

    challenge = encode_defunct(challenge_bytes)
    address, sig = sign_challenge( challenge )

    w3 = Web3()

    return w3.eth.account.recover_message( challenge , signature=sig ) == address


if __name__ == '__main__':
    """
        Test your function
    """
    if verify_sig():
        print( f"You passed the challenge!" )
    else:
        print( f"You failed the challenge!" )
