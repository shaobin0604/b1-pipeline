def fetch_daily_for_code(pro, code: str, start_date: str, end_date: str):
    return pro.daily(ts_code=code, start_date=start_date, end_date=end_date)
