import argparse

from hd_wallet import HDWallet as Wallet

def create_command(args):
    mnemonic, wallet = Wallet.create()
    print("wallet created. Here is your mnemonic:")
    print(mnemonic)
    address = wallet.consume_address(args.account)
    print("your first receiving address:", address)

def balance_command(args):
    wallet = Wallet.open()
    balance = wallet.balance(args.account)
    print(balance)

def address_command(args):
    wallet = Wallet.open()
    address = wallet.consume_address(args.account)
    print(address)

def unspent_command(args):
    wallet = Wallet.open()
    unspent = wallet.unspent(args.account)
    print(unspent)

def send_command(args):
    wallet = Wallet.open()
    response = wallet.send(args.address, args.amount, args.fee, args.account)
    print(response)

def transactions_command(args):
    wallet = Wallet.open()
    transactions = wallet.transactions(args.account)
    print(transactions)

def accounts_command(args):
    wallet = Wallet.open()
    print(wallet.accounts)

def register_account_command(args):
    wallet = Wallet.open()
    wallet.register_account(args.name)
    print(wallet.accounts)

def parse():
    parser = argparse.ArgumentParser(description='SD CLI Wallet')
    parser.add_argument('--account', help='which account to use', default='default')
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

    # accounts
    accounts = subparsers.add_parser('accounts', help='list wallet accounts')
    accounts.set_defaults(func=accounts_command)

    # register-account
    register_account = subparsers.add_parser('register-account', help='register a new account')
    register_account.add_argument('name', help='what to call this account')
    register_account.set_defaults(func=register_account_command)

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
