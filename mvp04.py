import os
import time
import json
from dotenv import load_dotenv
load_dotenv()
import python_bithumb

# 강의자료 : https://jocoding.net/gptbitcoin-bithumb 
# 4단계 
# - 4-5강(디테일 수정 및 실제 자동매매 실행하기) 
# - 5-1강(시스템 메시지에 투자철학 추가) 
# - 5-2강(공포탐욕지수 추가) 

def ai_trading():
    # 1. 빗썸 차트 데이터 가져오기 (hour6: 6시간 단위) 
    term = "hour6"
    df = python_bithumb.get_ohlcv("KRW-BTC", interval=term, count=30)

    # 2. AI에게 차트 데이터 제공하고 판단 받기
    from openai import OpenAI
    client = OpenAI()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",

                        # 너는 비트코인 투자 전문가야. 주어진 차트를 보고 buy, sell hold 중 알려줘. 한국어로 대답해줘.
                        "text": """   
한국어로 대답해줘. You are an expert in Bitcoin investing. Tell me whether to buy, sell, or hold at the moment based on the chart data provided. response in json format.\

You invest based on the following principles of 워렌 버핏:
Rule No.1: Never lose money.
Rule No.2: Never forget Rule No.1.

\n\nResponse Example:\n\
{\"decision\": \"buy\", \"reason\": \"some technical reason\"}\n
{\"decision\": \"sell\", \"reason\": \"some technical reason\"}\n
{\"decision\": \"hold\", \"reason\": \"some technical reason\"}\n
"""               
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": df.to_json()
                    }
                ]
            }
        ],
        response_format={
            "type": "json_object"
        }
    )
    result = response.choices[0].message.content

    # 3. AI의 판단에 따라 실제로 자동매매 진행하기
    result = json.loads(result)
    access = os.getenv("BITHUMB_ACCESS_KEY")
    secret = os.getenv("BITHUMB_SECRET_KEY")
    bithumb = python_bithumb.Bithumb(access, secret)

    my_krw = bithumb.get_balance("KRW")  # 보유 현금(원화)
    my_btc = bithumb.get_balance("BTC")  # 보유 비트코인(개수)   

    assess = result["decision"].upper()
    print(f"### ★★★{assess}★★★ 했습니다.")
    print(f"### AI 판단({term} 차트 분석): ", assess, "###")
    print(f"### Reason: {result['reason']} ###")
    
    # # 임시로 buy, sell
    # result["decision"] = "sell"   # buy or sell or hold
    # print("### 임시로 입력된 decision: ", result["decision"])

    # 투자의견이 buy일 때
    if result["decision"] == "buy":
        if my_krw > 50000:    # 내 잔고가 5000원(최소 거래금액) 이상일 때만 buy
            print("### Buy Order Executed ###", '\n')            
            bithumb.buy_market_order("KRW-BTC", my_krw*0.1*0.997)   # my_krw : 내 보유 자산, 0.997: 수수료 감안
        else:
            print("### Buy Order Failed: Insufficient KRW (less than 5000 KRW) ###", '\n')
    
    # 투자의견이 sell일 때
    elif result["decision"] == "sell":
        current_price = python_bithumb.get_current_price("KRW-BTC")
        if my_btc * current_price > 5000:
            print("### Sell Order Executed ###", '\n')
            bithumb.sell_market_order("KRW-BTC", my_btc)
        else:
            print("### Sell Order Failed: Insufficient BTC (less than 5000 KRW worth) ###", '\n')
    
    # 투자의견이 hold일 때
    elif result["decision"] == "hold":
        print("### Hold Position ###", '\n')

# 10초마다 반복 수행
while True:
    ai_trading()
    time.sleep(20)  # n초당 한번씩 실행(buy or sell or hold)



