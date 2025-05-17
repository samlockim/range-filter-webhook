# webhook_server.py
from flask import Flask, request
import os

try:
    import MetaTrader5 as mt5
except ModuleNotFoundError as e:
    raise ImportError("MetaTrader5 모듈이 설치되어 있지 않습니다. pip install MetaTrader5 를 실행해 설치하세요.") from e

app = Flask(__name__)

# MT5 계정 정보 (주인님 정보 입력됨)
login = 2100133177
password = "rlathdnjf11!A"
server = "EZSquare-Server"
symbol = "NQ2.ez2"
lot = 0.01

# MT5 연결 초기화
if not mt5.initialize(login=login, server=server, password=password):
    raise ConnectionError(f"MT5 초기화 실패: {mt5.last_error()}")

mt5.symbol_select(symbol, True)

# 현재 포지션 확인 함수
def get_position():
    positions = mt5.positions_get(symbol=symbol)
    if positions and len(positions) > 0:
        return positions[0].type  # 0 = Buy, 1 = Sell
    return None

# 주문 전송 함수
def send_order(order_type):
    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        print("틱 데이터 수신 실패")
        return None

    price = tick.ask if order_type == mt5.ORDER_TYPE_BUY else tick.bid
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": order_type,
        "price": price,
        "deviation": 20,
        "magic": 123456,
        "comment": "Range Filter Webhook Entry",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(request)
    print("주문 결과:", result)
    return result

# 웹훅 엔드포인트
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    signal = data.get("signal", "").upper()
    print("수신된 시그널:", signal)

    current = get_position()

    if signal == "BUY":
        if current == 1:
            print("Sell 포지션 청산 후 Buy 진입")
            send_order(mt5.ORDER_TYPE_BUY)
        elif current is None:
            print("Buy 진입")
            send_order(mt5.ORDER_TYPE_BUY)

    elif signal == "SELL":
        if current == 0:
            print("Buy 포지션 청산 후 Sell 진입")
            send_order(mt5.ORDER_TYPE_SELL)
        elif current is None:
            print("Sell 진입")
            send_order(mt5.ORDER_TYPE_SELL)

    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
