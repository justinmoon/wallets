import argparse
import logging

from pprint import pprint
from wallet import Wallet

def create_command(args):
    mnemonic, wallet = Wallet.create(args.account)
    print("wallet created. here is your mnemonic.")
    print(mnemonic)
    address = wallet.consume_address(args.account, False)
    print("your first receiving address:", address)

def address_command(args):
    address = args.wallet.consume_address(args.account, False)
    print(address)

def balance_command(args):
    unconfirmed, confirmed = args.wallet.balance(args.account)
    print(f'unconfirmed: {unconfirmed}')
    print(f'confirmed: {confirmed}')

def unspent_command(args):
    unspent = args.wallet.unspent(args.account)
    pprint(unspent)

def transactions_command(args):
    transactions = args.wallet.transactions(args.account)
    ids = [tx['txid'] for tx in transactions]
    pprint(ids)

def register_command(args):
    args.wallet.register_account(args.name)
    pprint(args.wallet.accounts)

def send_command(args):
    response = args.wallet.send(args.account, args.address, args.amount, args.fee)
    print(response)

def parse_args():
    parser = argparse.ArgumentParser(description='Simple CLI Wallet')
    parser.add_argument('--debug', help='print debug statements', action='store_true')
    parser.add_argument('--account', help='which account to use', default=argparse.SUPPRESS)
    subparsers = parser.add_subparsers(help='sub-command help')

    # create
    create = subparsers.add_parser('create', help='create wallet')
    create.set_defaults(func=create_command)

    # address
    address = subparsers.add_parser('address', help='generate new address')
    address.set_defaults(func=address_command)

    # balance
    balance = subparsers.add_parser('balance', help='wallet balance')
    balance.set_defaults(func=balance_command)

    # transactions
    transactions = subparsers.add_parser('transactions', help='transaction history')
    transactions.set_defaults(func=transactions_command)

    # unspent
    unspent = subparsers.add_parser('unspent', help='unspent transaction outputs')
    unspent.set_defaults(func=unspent_command)

    # register
    register_account = subparsers.add_parser('register', help='register a new account')
    register_account.add_argument('name', help='what to call this account')
    register_account.set_defaults(func=register_command)

    # "send"
    send = subparsers.add_parser('send', help='send bitcoins')
    send.add_argument('address', help='recipient\'s bitcoin address')
    send.add_argument('amount', type=int, help='how many satoshis to send')
    send.add_argument('fee', type=int, help='fee in satoshis')
    send.set_defaults(func=send_command)

    # parse
    args = parser.parse_args()

    # load wallet if there should be one
    if args.func != create_command:
        args.wallet = Wallet.open()
    
    # if --account wasn't passed
    if 'account' not in args:

        # if there aren't any wallets, set it to 'default'
        if not hasattr(args, 'wallet'):
            args.account = 'default'

        # if there's just 1 account we can safely guess it
        elif len(args.wallet.accounts) == 1:
            args.account = list(args.wallet.accounts.keys())[0]

        # otherwise display an error telling them to pass --account and return
        else:
            options = ','.join(args.wallet.accounts.keys())
            msg = f'--account must be set for wallets with more than 1 account (options: {options})'
            return parser.error(msg)
    
    return args

def main():
    # parse CLI arguments
    args = parse_args()

    # configure logger
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.WARNING)

    # exercise callback
    args.func(args)

if __name__ == '__main__':
    main()
