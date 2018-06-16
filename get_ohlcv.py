# -*- coding: utf-8 -*-
import bitflyer_helper
import time, os, datetime
import pandas as pd

INI_FILE_DIR = "./settings.ini"

PERIOD = 60 * 1  # seconds

unix_time = lambda y, m, d, h: int(time.mktime(datetime.datetime(y, m, d, h).timetuple()))


def fetch_ohlc_24h():
    bf = bitflyer_helper.BitflyerHelper(api_key=None, api_secret=None)
    today = datetime.datetime.today()

    after_time = unix_time(today.year, today.month, today.day-3, today.hour)
    before_time = int(time.time())

    ohlc_response = bf.get_ohlc(period=PERIOD, after=after_time, before=before_time)
    ohlcs = ohlc_response.json()["result"][str(PERIOD)]
    for ohlc in ohlcs:
        ohlc.pop(6)
        ohlc[0] = datetime.datetime.fromtimestamp(ohlc[0])
    return ohlcs


def save_ohlc_csv(ohlcs):
    df = pd.DataFrame(ohlcs, columns=["datetime", "open", "high", "low", "close", "volume"])

    csv_name = "ohlc_" + str(PERIOD//60) + ".csv"

    if not os.path.exists("./board_data"):
        os.mkdir("./board_data")

    if os.path.exists("./board_data/" + csv_name):
        csv_data = pd.read_csv("./board_data/" + csv_name, parse_dates=["datetime"])
        csv_max_unixtime = csv_data["datetime"].max()

        df_filtered = df[df.datetime > csv_max_unixtime]
        df_filtered.to_csv("./board_data/" + csv_name, index=False, header=False, mode="a")
    else:
        df.to_csv("./board_data/" + csv_name, index=False, mode="w")


if __name__ == "__main__":
    ohlcs = fetch_ohlc_24h()
    save_ohlc_csv(ohlcs)
