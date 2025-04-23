from tkinter import Frame, StringVar, Toplevel, Widget, ttk, Tk
from typing import Callable

import domain


class OpenAccount(Toplevel):
    def __init__(self, parent: Widget, bank: domain.Bank):
        super().__init__(parent)
        self.parent = parent
        self.bank = bank

        ttk.Label(
            self,
            text="Open an Account",
            ).pack()

        form_grid = Frame(self)
        form_grid.pack()

        self.full_name = StringVar()
        ttk.Label(
            form_grid,
            text='Full Name',
            ).grid(row=0, column=0)
        ttk.Entry(
            form_grid,
            textvariable=self.full_name,
            ).grid(row=0, column=1)

        ttk.Button(
            self,
            text='Create',
            command=self.on_click,
            ).pack()
        self.message = StringVar()
        self.message.set('')
        ttk.Label(
            self,
            textvariable=self.message,
            ).pack(fill='both')

    def on_click(self):
        try:
            account = self.bank.open_account(self.full_name.get())
            self.message.set(f'opened account ID {account.id}')
        except Exception as exc:
            self.message.set(f'ERROR {exc}')

class ModifyAccount(Toplevel):
    def __init__(self, parent: Widget, bank: domain.Bank):
        super().__init__(parent)
        self.parent = parent
        self.bank = bank

        ttk.Label(
            self,
            text="Modify an Account",
            ).pack()

        form_grid = Frame(self)
        form_grid.pack()

        ttk.Label(
            form_grid,
            text="Account ID",
            ).grid(row=0, column=0)
        self.account_id = StringVar()
        ttk.Entry(
            form_grid,
            textvariable=self.account_id,
            ).grid(row=0, column=1)

        ttk.Label(
            form_grid,
            text="Full Name",
            ).grid(row=1, column=0)
        self.full_name = StringVar()
        ttk.Entry(
            form_grid,
            textvariable=self.full_name,
            ).grid(row=1, column=1)

        ttk.Button(
            self,
            text='Modify',
            command=self.on_click,
            ).pack(side='top')

        self.message = StringVar()
        self.message.set('')
        ttk.Label(
            self,
            textvariable=self.message,
            ).pack(fill='both')

    def on_click(self):
        try:
            account_id = int(self.account_id.get())
            account = self.bank.alter_name(account_id, self.full_name.get())
            self.message.set(
                f'Account holder name for {account_id} '
                f'changed to {account.full_name}.')
        except Exception as exc:
            self.message.set(f'ERROR {exc}')

class CloseAccount(Toplevel):
    def __init__(self, parent: Widget, bank: domain.Bank):
        super().__init__(parent)
        self.parent = parent
        self.bank = bank

        ttk.Label(
            self,
            text="Close an Account",
            ).pack()

        form_grid = Frame(self)
        form_grid.pack()

        ttk.Label(
            form_grid,
            text="Account ID",
            ).grid(row=0, column=0)
        self.account_id = StringVar()
        ttk.Entry(
            form_grid,
            textvariable=self.account_id,
            ).grid(row=0, column=1)

        ttk.Button(
            self,
            text='Close',
            command=self.on_click,
            ).pack(side='top')

        self.message = StringVar()
        self.message.set('')
        ttk.Label(
            self,
            textvariable=self.message,
            ).pack(fill='both')

    def on_click(self):
        try:
            account_id = int(self.account_id.get())
            account = self.bank.close_account(account_id)
            self.message.set(f'Account {account_id} closed at {account.closed_at}')
        except Exception as exc:
            self.message.set(f'ERROR {exc}')

class ViewBalance(Toplevel):
    def __init__(self, parent: Widget, bank: domain.Bank):
        super().__init__(parent)
        self.parent = parent
        self.bank = bank

        ttk.Label(
            self,
            text="View Balance",
            ).pack()

        form_grid = Frame(self)
        form_grid.pack()

        ttk.Label(
            form_grid,
            text="Account ID",
            ).grid(row=0, column=0)
        self.account_id = StringVar()
        ttk.Entry(
            form_grid,
            textvariable=self.account_id,
            ).grid(row=0, column=1)

        ttk.Button(
            self,
            text='Look Up',
            command=self.on_click,
            ).pack(side='top')

        self.message = StringVar()
        self.message.set('')
        ttk.Label(
            self,
            textvariable=self.message,
            ).pack(fill='both')

    def on_click(self):
        try:
            account_id = int(self.account_id.get())
            account = self.bank.load(account_id)
            open_or_closed = 'open' if account.is_open else 'closed'
            self.message.set(
                f'{open_or_closed} account {account_id} '
                f'balance is {account.balance}')
        except Exception as exc:
            self.message.set(f'ERROR {exc}')

class Deposit(Toplevel):
    def __init__(self, parent: Widget, bank: domain.Bank):
        super().__init__(parent)
        self.parent = parent
        self.bank = bank

        ttk.Label(
            self,
            text="Deposit into Account",
            ).pack()

        form_grid = Frame(self)
        form_grid.pack()

        ttk.Label(
            form_grid,
            text="Account ID",
            ).grid(row=0, column=0)
        self.account_id = StringVar()
        ttk.Entry(
            form_grid,
            textvariable=self.account_id,
            ).grid(row=0, column=1)

        ttk.Label(
            form_grid,
            text="Amount USD",
            ).grid(row=1, column=0)
        self.amount_var = StringVar()
        ttk.Entry(
            form_grid,
            textvariable=self.amount_var,
            ).grid(row=1, column=1)

        ttk.Button(
            self,
            text='Deposit',
            command=self.on_click,
            ).pack(side='top')

        self.message = StringVar()
        self.message.set('')
        ttk.Label(
            self,
            textvariable=self.message,
            ).pack(fill='both')

    def on_click(self):
        try:
            account_id = int(self.account_id.get())
            amount = domain.USD.parse(self.amount_var.get())

            before = self.bank.load(account_id)
            after = self.bank.deposit(account_id, amount)

            self.message.set(
                f'Account {account_id} balance was {before.balance};'
                f'is now {after.balance}.')
        except Exception as exc:
            self.message.set(f'ERROR {exc}')

class Withdraw(Toplevel):
    def __init__(self, parent: Widget, bank: domain.Bank):
        super().__init__(parent)
        self.parent = parent
        self.bank = bank

        ttk.Label(
            self,
            text="Withdraw from Account",
            ).pack()

        form_grid = Frame(self)
        form_grid.pack()

        ttk.Label(
            form_grid,
            text="Account ID",
            ).grid(row=0, column=0)
        self.account_id = StringVar()
        ttk.Entry(
            form_grid,
            textvariable=self.account_id,
            ).grid(row=0, column=1)

        ttk.Label(
            form_grid,
            text="Amount USD",
            ).grid(row=1, column=0)
        self.amount_var = StringVar()
        ttk.Entry(
            form_grid,
            textvariable=self.amount_var,
            ).grid(row=1, column=1)

        ttk.Button(
            self,
            text='Withdraw',
            command=self.on_click,
            ).pack(side='top')

        self.message = StringVar()
        self.message.set('')
        ttk.Label(
            self,
            textvariable=self.message,
            ).pack(fill='both')

    def on_click(self):
        try:
            account_id = int(self.account_id.get())
            amount = domain.USD.parse(self.amount_var.get())

            before = self.bank.load(account_id)
            after = self.bank.withdraw(account_id, amount)

            self.message.set(
                f'Account {account_id} balance was {before.balance};'
                f'is now {after.balance}.')
        except Exception as exc:
            self.message.set(f'ERROR {exc}')

class MainMenu(Frame):
    def __init__(
            self,
            parent: Widget,
            bank: domain.Bank,
            on_quit: Callable):
        super().__init__(parent)
        self.parent = parent
        self.bank = bank

        ttk.Label(
            self,
            text='Code2College Bank',
            ).pack(side='top')

        menu_items = [
            ('Open an Account',     self.on_open_account),
            ('Modify Account',      self.on_modify_account),
            ('Close an Account',    self.on_close_account),
            ('View Balance',        self.on_view_balance),
            ('Deposit',             self.on_deposit),
            ('Withdraw',            self.on_withdraw),
            ('Quit',                on_quit),
            ]

        for (text, command) in menu_items:
            ttk.Button(self, text=text, command=command).pack(fill='both')

    def on_open_account(self):
        OpenAccount(self.parent, self.bank)

    def on_modify_account(self):
        ModifyAccount(self.parent, self.bank)

    def on_close_account(self):
        CloseAccount(self.parent, self.bank)

    def on_view_balance(self):
        ViewBalance(self.parent, self.bank)

    def on_deposit(self):
        Deposit(self.parent, self.bank)

    def on_withdraw(self):
        Withdraw(self.parent, self.bank)

class Application:
    def __init__(self, bank: domain.Bank):
        self.root = Tk()
        self.main_menu = MainMenu(
            self.root,
            bank,
            on_quit=self.root.destroy)
        self.main_menu.pack(side='top', fill='both', expand=True)

    def run(self):
        self.root.mainloop()
