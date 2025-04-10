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
        self.full_name = StringVar()
        ttk.Entry(
            self,
            textvariable=self.full_name,
            ).pack(fill='both')
        ttk.Button(
            self,
            text='Create Account',
            command=self.on_click,
            ).pack()
        self.message = StringVar()
        self.message.set('')
        ttk.Label(
            self,
            textvariable=self.message,
            ).pack(fill='both')

    def on_click(self):
        ## FIXME: error handling
        account = self.bank.open_account(self.full_name.get())
        self.message.set(f'successfully opened account ID {account.id}')

class ModifyAccount(Toplevel):
    def __init__(self, parent: Widget, bank: domain.Bank):
        super().__init__(parent)
        self.parent = parent
        self.bank = bank

        ttk.Label(
            self,
            text="Modify an Account",
            ).pack()

        self.account_id = StringVar()
        ttk.Entry(
            self,
            textvariable=self.account_id,
            ).pack(fill='both')

        self.full_name = StringVar()
        ttk.Entry(
            self,
            textvariable=self.full_name,
            ).pack(fill='both')

        ttk.Button(
            self,
            text='Modify',
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
            account_id = int(self.account_id.get())
            account = self.bank.alter_name(account_id, self.full_name.get())
            self.message.set(
                f'Account holder name for {account_id} '
                f'changed to {account.full_name}.')
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
        ttk.Button(
            self,
            text='Open an Account',
            command=self.on_open_account,
            ).pack(side='top', fill='both')
        ttk.Button(
            self,
            text='Modify Account',
            command=self.on_modify_account,
            ).pack(fill='both')

        self.close_account = ttk.Button(self, text='Close an Account')
        self.close_account.pack(fill='both')

        self.check_balance = ttk.Button(self, text='View Balance')
        self.check_balance.pack(fill='both')

        self.deposit = ttk.Button(self, text='Deposit')
        self.deposit.pack(fill='both')

        self.withdraw = ttk.Button(self, text='Withdraw')
        self.withdraw.pack(fill='both')

        self.quit = ttk.Button(self, text="Quit", command=on_quit)
        self.quit.pack(fill='both')

    def on_open_account(self):
        OpenAccount(self.parent, self.bank)

    def on_modify_account(self):
        ModifyAccount(self.parent, self.bank)

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
