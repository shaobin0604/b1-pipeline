def fetch_stock_basic(pro):
    return pro.stock_basic(exchange="", list_status="L", fields="ts_code,name,industry")
