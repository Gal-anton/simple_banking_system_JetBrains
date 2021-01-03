# Write your code here
import random
import sqlite3


class BankDBConnection:
    conn = sqlite3.connect('card.s3db')

    def __init__(self):
        self.cur = self.conn.cursor()
        self.cur.execute('CREATE TABLE IF NOT EXISTS `card` (' +
                         'id INTEGER PRIMARY KEY,' +
                         'number TEXT,' +
                         'pin TEXT,' +
                         'balance INTEGER DEFAULT 0)')

    def save(self, number, pin):
        self.cur.execute('INSERT INTO `card`(`number`, `pin`) VALUES ' +
                         f'({number}, {pin})')
        self.conn.commit()

    def get_account(self, card_number, account_password):
        self.cur.execute('SELECT `id`, `number`, `pin`, `balance` ' +
                         'FROM `card` ' +
                         f'WHERE `number` = {card_number} AND ' +
                         f'`pin` = {account_password}')
        return self.cur.fetchone()

    def update_account(self, card_number, balance):
        self.cur.execute('UPDATE `card` ' +
                         f'SET balance = {balance} ' +
                         f'WHERE number = {card_number}')
        self.conn.commit()

    def is_card_exists(self, card):
        self.cur.execute('SELECT `number`, `balance`' +
                         'FROM `card`' +
                         f'WHERE `number` = {card}')
        return self.cur.fetchone()

    def delete_account(self, account_id):
        self.cur.execute('DELETE FROM `card`' +
                         f'WHERE id = {account_id}')
        self.conn.commit()


def get_sum_luhn(card_number):
    summary = 0
    for index, digit_char in enumerate(card_number, start=1):
        digit = int(digit_char)
        double_odd_digit = digit * 2 if index % 2 else digit
        reduced_digit = double_odd_digit - 9 if double_odd_digit // 10 else double_odd_digit
        summary += reduced_digit
    return summary


def check_number_luhn(card_number):
    summary = get_sum_luhn(card_number)
    return summary % 10 == 0


class Account:
    bik = "400000"

    def __init__(self, id=None, number=None, password=None, balance=None):
        self.conn = BankDBConnection()
        self.id = id
        self.number = number
        self.password = password
        self.balance = balance

    def create(self):
        self.number = self.generate_number()
        self.password = "".join([str(random.randint(0, 9)) for _ in range(4)])

        self.conn.save(self.number, self.password)

    def log_in(self, card_number, account_password):
        new_account = False
        card_info = self.conn.get_account(card_number, account_password)
        if card_info:
            new_account = Account(card_info[0],
                                  card_info[1],
                                  card_info[2],
                                  card_info[3])
        return new_account

    def add_income(self, income):
        new_balance = self.balance + income
        self.conn.update_account(self.number, new_balance)
        card_info = self.conn.get_account(self.number, self.password)
        if card_info:
            self.id = card_info[0]
            self.number = card_info[1]
            self.password = card_info[2]
            self.balance = card_info[3]

    def generate_number(self):
        number_first_part = self.bik + "".join([str(random.randint(0, 9)) for _ in range(9)])
        summary = get_sum_luhn(number_first_part)

        number_second_part = str(10 - summary % 10) if summary % 10 else "0"
        return number_first_part + number_second_part

    def get_balance(self):
        return self.balance

    def do_transfer(self, card_to, count):
        new_account = False
        card_to_info = self.conn.is_card_exists(card_to)
        if count > self.balance:
            print("Not enough money!")
        else:
            self.conn.update_account(self.number, self.balance - count)
            self.conn.update_account(card_to_info[0], card_to_info[1] + count)
            card_info = self.conn.get_account(self.number, self.password)
            if card_info:
                new_account = Account(card_info[0],
                                      card_info[1],
                                      card_info[2],
                                      card_info[3])
        return new_account

    def close(self):
        self.conn.delete_account(self.id)

    def check_card_to_transfer(self, card_to):
        status = True
        card_to_info = self.conn.is_card_exists(card_to)
        if card_to == self.number:
            print("You can't transfer money to the same account!")
            status = False
        elif not check_number_luhn(card_to):
            print("Probably you made a mistake in the card number." +
                  " Please try again!")
            status = False
        elif not card_to_info:
            print("Such a card does not exist.")
            status = False
        return status


while True:
    account = Account()
    code = input("1. Create an account\n" +
                 "2. Log into account\n" +
                 "0. Exit\n")
    if code == "0":
        exit("Bye!")
    if code == "1":
        account.create()
        print("Your card has been created")
        print(f"Your card number:\n{account.number}")
        print(f"Your card PIN:\n{account.password}")
    elif code == "2":
        number = input("Enter your card number:\n")
        password = input("Enter your PIN:\n")
        account = account.log_in(number, password)
        if account:
            print("You have successfully logged in!")
            while True:
                code_inside = int(input("1. Balance\n" +
                                        "2. Add income\n" +
                                        "3. Do transfer\n" +
                                        "4. Close account\n" +
                                        "5. Log out\n" +
                                        "0. Exit\n"))
                if code_inside == 1:
                    print(f"Balance: {account.get_balance()}")
                elif code_inside == 2:
                    account.add_income(int(input("Enter income:\n")))
                    print('Income was added!')
                    print(account.number)
                    print(account.balance)
                elif code_inside == 3:
                    card_to = input("Transfer" +
                                    "Enter card number:")
                    is_valid = account.check_card_to_transfer(card_to)
                    if is_valid:
                        count = int(input("Enter how much money you want to transfer:"))
                        is_transferred = account.do_transfer(card_to, count)
                        if is_transferred:
                            print("Success!")
                elif code_inside == 4:
                    account.close()
                elif code_inside == 5:
                    print("You have successfully logged out!")
                    del account
                    break
                elif code_inside == 0:
                    exit("Bye!")
        else:
            print("Wrong card number or PIN!")
    del account
