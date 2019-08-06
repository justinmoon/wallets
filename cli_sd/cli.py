import argparse
import logging

from pprint import pprint
from wallet_final import Wallet

def create_command(args):
    wallet = Wallet.create(args.size)
    address = wallet.consume_address()
    print("wallet created")
    print("your first receiving address:", address)

def address_command(args):
    address = args.wallet.consume_address()
    print(address)

def balance_command(args):
    unconfirmed, confirmed = args.wallet.balance()
    print(f'unconfirmed: {unconfirmed}')
    print(f'confirmed: {confirmed}')

def unspent_command(args):
    unspent = args.wallet.unspent()
    pprint(unspent)

def transactions_command(args):
    transactions = args.wallet.transactions()
    ids = [tx['txid'] for tx in transactions]
    pprint(ids)

def send_command(args, wallet):
    response = wallet.send(args.address, args.amount, args.fee)
    print(response)

def parse_args():
    parser = argparse.ArgumentParser(description='Simple CLI Wallet')
    parser.add_argument('--debug', help='Print debug statements', action='store_true')
    subparsers = parser.add_subparsers(help='sub-command help')

    # create
    create = subparsers.add_parser('create', help='create wallet')
    create.add_argument('size', type=int, help='size of wallet keypool')
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

    return args

def main():
    args = parse_args()

    # configure logger
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.WARNING)

    # exercise callback
    args.func(args)

if __name__ == '__main__':
    main()
