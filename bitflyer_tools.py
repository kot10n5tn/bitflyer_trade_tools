# -*- coding: utf-8 -*-
from enum import Enum


class ChildOrder:

    def __init__(self,
                 product_code,
                 child_order_type,
                 side,
                 price: int,
                 size: float,
                 minute_to_expire: int,
                 time_in_force):
        self.product_code = product_code
        self.child_order_type = child_order_type
        self.side = side
        self.price = price
        self.size = size
        self.minute_to_expire = minute_to_expire
        self.time_in_force = time_in_force

    def to_body(self):
        return {
            "product_code": self.product_code.value,
            "child_order_type": self.child_order_type.value,
            "side": self.side.value,
            "price": self.price,
            "size": self.size,
            "minute_to_expire": self.minute_to_expire,
            "time_in_force": self.time_in_force.value
        }


class ProductCode(Enum):
    btc_jpy = "BTC_JPY"
    btc_fx = "FX_BTC_JPY"
    eth_btc = "ETH_BTC"


class ChildOrderType(Enum):
    limit = "LIMIT"  # 指値注文
    market = "MARKET"  # 成行注文


class Side(Enum):
    buy = "BUY"
    sell = "SELL"

    def other_side(self):
        if self == Side.buy:
            return Side.sell
        else:
            return Side.buy


class TimeInForce(Enum):
    good_till_canceled = "GTC"  # 注文が約定するかキャンセルされるまで有効
    immediate_or_cancel = "IOC"  # 指定した価格かそれよりも有利な価格で即時に一部あるいは全部を約定させ、約定しなかった注文数量をキャンセル
    fill_or_kill = "FOK"  # 発注の全数量が即座に約定しない場合当該注文をキャンセル


class ParentOrder:

    def __init__(self,
                 order_method,
                 minute_to_expire: int,
                 time_in_force,
                 parameters,
                 ):
        self.order_method = order_method
        self.minute_to_expire = minute_to_expire
        self.time_in_force = time_in_force
        self.parameters = parameters

    def to_body(self):
        parameters_body = []
        for parameter in self.parameters:
            parameters_body.append(parameter.to_body())
        return {
            "order_method": self.order_method.value,
            "minute_to_expire": self.minute_to_expire,
            "time_in_force": self.time_in_force.value,
            "parameters": parameters_body
        }


class OrderMethod(Enum):
    simple = "SIMPLE"
    ifd = "IFD"
    oco = "OCO"
    ifd_oco = "IFDOCO"


class Parameter:

    def __init__(self,
                 product_code,
                 condition_type,
                 side: Side,
                 price: int,
                 size: float,
                 trigger_price: int,
                 offset: int
                 ):
        self.product_code = product_code
        self.condition_type = condition_type
        self.side = side
        self.price = price
        self.size = size
        self.trigger_price = trigger_price
        self.offset = offset

    def to_body(self):
        return {
            "product_code": self.product_code.value,
            "condition_type": self.condition_type.value,
            "side": self.side.value,
            "price": self.price,
            "size": self.size,
            "trigger_price": self.trigger_price,
            "offset": self.offset
        }


class ConditionType(Enum):
    limit = "LIMIT"
    market = "MARKET"
    stop = "STOP"
    stop_limit = "STOP_LIMIT"
    trail = "TRAIL"