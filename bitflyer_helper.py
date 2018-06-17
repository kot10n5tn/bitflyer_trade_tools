# -*- coding: utf-8 -*-
import hashlib, hmac, json, sys, time, requests
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub, SubscribeListener
from bitflyer_tools import ChildOrder, ProductCode, ChildOrderType, Side, TimeInForce, ParentOrder, \
    OrderMethod, Parameter, ConditionType
from requests.adapters import HTTPAdapter

BASE_URL = "https://api.bitflyer.jp{0}"
error_limit = 10


class BitflyerHelper:

    api_key = ""
    api_secret = ""
    pubnub_subscribe_key = ""
    error_count = 0
    pubnub = None

    def __init__(self, api_key, api_secret, pubnub_subscribe_key=""):
        self.session = requests.session()
        self.api_key = api_key
        self.api_secret = api_secret
        self.pubnub_subscribe_key = pubnub_subscribe_key
        self.listener = SubscribeListener()
        self.session.mount('https://', HTTPAdapter(max_retries=5))
        self.session.mount('http://', HTTPAdapter(max_retries=5))

    # リアルタイム(pubnub)で情報を取得するためのセットアップ
    def setup_pubnub(self):
        pnconfig = PNConfiguration()
        pnconfig.subscribe_key = self.pubnub_subscribe_key
        pnconfig.ssl = False
        self.pubnub = PubNub(pnconfig)
        self.pubnub.add_listener(self.listener)

    # 板情報をリアルタイムで取得するためのセットアップ
    def subscribe_board_pubnub(self):
        self.pubnub.subscribe().channels('lightning_board_snapshot_FX_BTC_JPY').execute()
        self.listener.wait_for_connect()

    # 板情報の差分をリアルタイムで取得するためのセットアップ
    def subscribe_board_diff_pubnub(self):
        self.pubnub.subscribe().channels('lightning_board_FX_BTC_JPY').execute()
        self.listener.wait_for_connect()

    # 約定履歴をリアルタイムで取得するためのセットアップ
    def subscribe_executions_pubnub(self):
        self.pubnub.subscribe().channels('lightning_executions_FX_BTC_JPY').execute()
        self.listener.wait_for_connect()

    # 板情報をリアルタイムで取得
    def get_board_pubnub(self):
        return self.listener.wait_for_message_on("lightning_board_snapshot_FX_BTC_JPY").message

    # 板情報の差分をリアルタイムで取得
    def get_board_diff_pubnub(self):
        return self.listener.wait_for_message_on("lightning_board_FX_BTC_JPY").message

    # 約定履歴をリアルタイムで取得
    def get_executions_pubnub(self):
        return self.listener.wait_for_message_on('lightning_executions_FX_BTC_JPY').message

    # 4本値の取得, period: n本足を秒数で表記, after: 指定したunixtime以降のデータを取得
    """
        返り値 [UNIX timestamp, 始値, 高値, 安値, 終値, 出来高]
    """
    def get_ohlc(self, period: int, after: int, before: int):
        endpoint = "https://api.cryptowat.ch/markets/bitflyer/btcfxjpy/ohlc?" \
                   "periods={0}&after={1}&before={2}".format(str(period), str(after), str(before))
        response = self.get_request(endpoint)
        return response

    # マーケットの一覧を取得
    def get_markets(self):
        response = self.get_request("/v1/getmarkets").json()
        return response

    # 板情報を取得
    def get_board(self, product_code: ProductCode):
        params = {"product_code": product_code.value}
        response = self.get_request("/v1/getboard", params=params).json()
        return response

    # Tickerを取得
    def get_ticker(self, product_code: ProductCode):
        params = {"product_code": product_code.value}
        response = self.get_request("/v1/getticker", params=params).json()
        return response

    # 約定履歴
    def get_executions(self, product_code: ProductCode):
        params = {"product_code": product_code.value}
        response = self.get_request("/v1/getexecutions", params=params).json()
        return response

    # 板の状態
    def get_board_state(self, product_code: ProductCode):
        params = {"product_code": product_code.value}
        response = self.get_request("/v1/getboardstate", params=params).json()
        return response

    # 取引所の状態
    def get_health(self, product_code: ProductCode):
        params = {"product_code": product_code.value}
        response = self.get_request("/v1/gethealth", params=params).json()
        return response

    # チャットの取得
    def get_chats(self, from_date: str=None):
        params = {}
        response = self.get_request("/v1/getchats", params=params).json()
        return response

    # APIキーの権限を取得
    def get_permissions(self):
        method = "GET"
        endpoint = "/v1/me/getpermissions"
        body = ""
        headers = self.create_private_header(method=method, endpoint=endpoint, body=body)
        response = self.get_request(endpoint=endpoint, params=body, headers=headers).json()
        return response

    # 資産残高を取得
    def get_balance(self):
        method = "GET"
        endpoint = "/v1/me/getbalance"
        body = ""
        headers = self.create_private_header(method=method, endpoint=endpoint, body=body)
        response = self.get_request(endpoint=endpoint, params=body, headers=headers).json()
        return response

    # 証拠金の状態を取得
    def get_collateral(self):
        method = "GET"
        endpoint = "/v1/me/getcollateral"
        body = ""
        headers = self.create_private_header(method=method, endpoint=endpoint, body=body)
        response = self.get_request(endpoint=endpoint, params=body, headers=headers).json()
        return response

    # 通貨別の証拠金の数量を取得
    def get_collateralaccounts(self):
        method = "GET"
        endpoint = "/v1/me/getcollateralaccounts"
        body = ""
        headers = self.create_private_header(method=method, endpoint=endpoint, body=body)
        response = self.get_request(endpoint=endpoint, params=body, headers=headers).json()
        return response

    # 新規注文を出す
    def send_child_order(self, child_order: ChildOrder):
        method = "POST"
        endpoint = "/v1/me/sendchildorder"
        body = child_order.to_body()
        print(body)
        body = json.dumps(body)
        headers = self.create_private_header(method=method, endpoint=endpoint, body=body)
        response = self.post_request(endpoint=endpoint, params=body, headers=headers).json()
        print(response)
        return response

    # 注文をキャンセルする
    def cancel_child_order(self, product_code: ProductCode, child_order_acceptance_id: str):
        method = "POST"
        endpoint = "/v1/me/cancelchildorder"
        body = {
            "product_code": product_code.value,
            "child_order_acceptance_id": child_order_acceptance_id
        }
        body = json.dumps(body)
        headers = self.create_private_header(method=method, endpoint=endpoint, body=body)
        response = self.post_request(endpoint=endpoint, params=body, headers=headers)
        return response

    # 新規の親注文を出す(特殊注文)
    def send_parent_order(self, parent_order):
        method = "POST"
        endpoint = "/v1/me/sendparentorder"
        body = parent_order.to_body()
        body = json.dumps(body)
        headers = self.create_private_header(method=method, endpoint=endpoint, body=body)
        response = self.post_request(endpoint=endpoint, params=body, headers=headers).json()
        print(response)
        return response

    # 注文の一覧を取得
    def get_child_orders(self, product_code: ProductCode):
        method = "GET"
        endpoint = "/v1/me/getchildorders?product_code={}".format(product_code.value)
        headers = self.create_private_header(method=method, endpoint=endpoint, body="")
        response = self.get_request(endpoint=endpoint, headers=headers).json()
        return response

    # 建玉の一覧を取得
    def get_positions(self, product_code: ProductCode):
        method = "GET"
        endpoint = "/v1/me/getpositions?product_code={}".format(product_code.value)
        headers = self.create_private_header(method=method, endpoint=endpoint, body="")
        response = self.get_request(endpoint=endpoint, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return None

    # Private API用のヘッダーを作成
    def create_private_header(self, method, endpoint, body):
        if self.api_key and self.api_secret:
            access_timestamp = str(time.time())
            api_secret = str.encode(self.api_secret)
            text = str.encode(access_timestamp + method + endpoint + body)
            access_sign = hmac.new(api_secret,
                                   text,
                                   hashlib.sha256).hexdigest()
            auth_header = {
                "ACCESS-KEY": self.api_key,
                "ACCESS-TIMESTAMP": access_timestamp,
                "ACCESS-SIGN": access_sign,
                "Content-Type": "application/json"
            }
            return auth_header
        else:
            sys.exit()

    # GETメソッド用
    def get_request(self, endpoint, params=None, headers=None):
        if endpoint[0] == "/":
            url = BASE_URL.format(endpoint)
        else:
            url = endpoint
        while True:
            try:
                response = self.session.get(url, params=params, timeout=5, headers=headers)
                if not (response.status_code == 200 or response.status_code == 404):
                    continue
                self.error_count = 0
                return response
            except Exception as e:
                if self.error_count < error_limit:
                    self.error_count += 1
                    continue
                else:
                    sys.exit(e)

    # POSTメソッド用
    def post_request(self, endpoint, params=None, headers=None):
        url = BASE_URL.format(endpoint)
        while True:
            try:
                response = self.session.post(url, data=params, timeout=5, headers=headers)
                if response.status_code != 200:
                    continue
                self.error_count = 0
                return response
            except Exception as e:
                if self.error_count < error_limit:
                    self.error_count += 1
                    continue
                else:
                    sys.exit(e)

