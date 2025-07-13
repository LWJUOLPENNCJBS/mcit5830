#!/usr/bin/env python3
"""
Please complete the following fields and run the student tests to verify
that you are ready to make a faucet request and the faucet is online

Once you have successfully completed the "run tests" you can submit this
assignment to have funds transferred to your account. This assignment
does not count towards your grade, and you only have to complete it if
you want an AVAX or BNB funds "drip" from the course account.

***NOTE***
Please keep the account and private key somewhere safe so that you can
reuse this account for future assignments that require you to use a
"funded" account.

***Please do not use an account that you use for real funds.***
"""

# Do you need an account? (True or False)
create_account = False

# If you have an account you want to use make sure 'create_account' is False,
# complete the following fields and 'run tests' again to verify the information
name = 'Weijie Li'  # Your name
e_mail = 'liweijie@seas.upenn.edu'  # this should be your e-mail in ed-stem
account = '0xc4576742b18E3802E13fDc395595021e4209661C'  # The account you want the funds in
secret_key = '0x05c508ed09c805f39ca2001e781ed639b45c607cf1e7e6cd1abaafdc9c93038d'  # The secret key for your account

# Networks you want funding from (True or False)
AVAX = True
BNB = True

'''
# For your personal use, the entirety of the account creation code is included here

import eth_account
 
def create_account():
    eth_account.Account.enable_unaudited_hdwallet_features()
    acct, nmemonic = eth_account.Account.create_with_mnemonic(num_words=12)

    print(f"Below is your new account information!\n\nAddress:     {acct.address}"
          f"\nPrivate key: 0x{acct.key.hex()}\nNmemonic phrase: {nmemonic}\n\nSave"
          f" this keypair and the nmemonic so that you can complete the faucet "
          f"request,\nand use this account in upcoming assignments.\n\nAlso, you "
          f"can view your account on the AVAX block explorer at:"
          f"\nhttps://testnet.snowtrace.io/address/{acct.address}\nand the BSC "
          f"block explorer at:\nhttps://testnet.bscscan.com/address/{acct.address}")
    
'''
