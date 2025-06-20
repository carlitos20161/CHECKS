from extensions import db
from models import Check, Bank

def get_next_check_number_by_bank(bank_id):
    last_check = (
        db.session.query(Check)
        .filter_by(bank_id=bank_id)
        .order_by(Check.check_number.desc())
        .first()
    )

    if last_check:
        return last_check.check_number + 1
    else:
        bank = Bank.query.get(bank_id)
        return bank.starting_check_number if bank and bank.starting_check_number else 1000
