import argparse

from sd_wallet import SDWallet as Wallet

def create_command(args):
    wallet = Wallet.create()
    address = wallet.consume_address()
    print("wallet created")
    print("your first receiving address:", address)

def balance_command(args):
    wallet = Wallet.open()
    balance = wallet.balance()
    print(balance)

def address_command(args):
    wallet = Wallet.open()
    address = wallet.consume_address()
    print(address)

def unspent_command(wallet):
    wallet = Wallet.open()
    unspent = wallet.unspent()
    print(unspent)

def send_command(args):
    wallet = Wallet.open()
    response = wallet.send(args.address, args.amount, args.fee)
    print(response)

def transactions_command(args):
    wallet = Wallet.open()
    transactions = wallet.transactions()
    print(transactions)

def parse():
    parser = argparse.ArgumentParser(description='SD CLI Wallet')
    subparsers = parser.add_subparsers(help='sub-command help')

    # create
    create = subparsers.add_parser('create', help='create wallet')
    create.set_defaults(func=create_command)

    # transactions
    transactions = subparsers.add_parser('transactions', help='transaction history')
    transactions.set_defaults(func=transactions_command)

    # unspent
    unspent = subparsers.add_parser('unspent', help='unspent transaction outputs')
    unspent.set_defaults(func=unspent_command)

    # balance
    balance = subparsers.add_parser('balance', help='wallet balance')
    balance.set_defaults(func=balance_command)

    # address
    address = subparsers.add_parser('address', help='generate new address')
    address.set_defaults(func=address_command)

    # "send"
    send = subparsers.add_parser('send', help='send bitcoins')
    send.add_argument('address', help='recipient\'s bitcoin address')
    send.add_argument('amount', type=int, help='how many satoshis to send')
    send.add_argument('fee', type=int, help='fee in satoshis')
    send.set_defaults(func=send_command)

    return parser.parse_args()

def main():
    args = parse()
    args.func(args)

if __name__ == '__main__':
    main()
