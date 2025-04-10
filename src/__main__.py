import datetime

import domain
import database
import gui


class SystemClock(domain.Clock):
    def utcnow(self):
        return datetime.datetime.now(datetime.timezone.utc)

def main():
    clock = SystemClock()
    with database.BankMySqlDatabase() as db:
        bank = domain.Bank(db, clock)
        ui = gui.Application(bank)

        ui.run()

if __name__ == '__main__':
    main()
