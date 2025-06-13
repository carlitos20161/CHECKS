
# utils/check_utils.py
from extensions import db
from models import Check

def get_next_global_check_number():
    last_check = db.session.query(Check).order_by(Check.check_number.desc()).first()
    return (last_check.check_number + 1) if last_check else 1000
