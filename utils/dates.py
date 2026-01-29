from datetime import datetime
from hijri_converter import Gregorian

def calculate_new_date(birth_date: str, years: int, months: int, days: int) -> str:
    try:
        date_obj = datetime.strptime(birth_date, "%Y/%m/%d")
        new_year = date_obj.year + years
        new_month = date_obj.month + months

        if new_month > 12:
            new_year += new_month // 12
            new_month %= 12

        new_day = date_obj.day + days

        while True:
            try:
                new_date = datetime(new_year, new_month, new_day)
                break
            except ValueError:
                new_day -= 1

        return new_date.strftime("%Y/%m/%d")
    except:
        return None


def get_hijri_date(gregorian_date: str) -> str:
    date_obj = datetime.strptime(gregorian_date, "%Y/%m/%d")
    hijri_date = Gregorian(date_obj.year, date_obj.month, date_obj.day).to_hijri()
    return f"{hijri_date.day:02d}/{hijri_date.month:02d}/{hijri_date.year}"