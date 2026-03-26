import tushare as ts


def build_client(token: str):
    ts.set_token(token)
    return ts.pro_api()
