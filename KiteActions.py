import datetime;
import json
import os

import pandas as pd
import requests
from dateutil.rrule import rrule, WEEKLY, TH

import TradeConstants
from kite_trade import KiteApp

kite = KiteApp(enctoken=os.environ.get('APITOKEN'))

option_data = {}
is_monthly_expiry = False


def getTaregtForOrderFromList(levels, currentValue, orderType):
    if orderType == "CE":
        result = min(filter(lambda i: i > currentValue, levels), default=None)
        return result
    elif orderType == "PE":
        result = max(filter(lambda i: i < currentValue, levels), default=None)
        return result


def addLogToFile(index, logDetails):
    print(logDetails)
    fileName = 'TRADEBOOK_' + str(index) + '_' + str(TradeConstants.TIME_INTERVAL) + '.txt'
    file = open(fileName, 'a')
    file.write(str(logDetails) + "\t " + str(
        datetime.datetime.now()) + "\n\n")
    file.close()
    if logDetails.__contains__("SuccessFully") or logDetails.__contains__("exception"):
        sendMessageInTelegram(logDetails)


# def addLogToFile(logDetails):
#     print(logDetails)
#     fileName = 'TRADEBOOK_' + str(TradeConstants.TRADE_INDEX) + '_' + str(TradeConstants.TIME_INTERVAL) + '.txt'
#     file = open(fileName, 'a')
#     file.write(str(logDetails) + "\t " + str(
#         datetime.datetime.now()) + "\n\n")
#     file.close()
#     if logDetails.__contains__("SuccessFully") or logDetails.__contains__("exception"):
#         sendMessageInTelegram(logDetails)


def getnsedata():
    try:
        global option_data
        df = pd.DataFrame(kite.instruments())
        df = df[(df.name == TradeConstants.TRADE_INDEX)]
        df = sorted(df.expiry.unique())
        option_data[0] = str(datetime.datetime.strptime(str(df[0]), '%Y-%m-%d').strftime('%d-%b-%Y'))
        option_data[1] = str(datetime.datetime.strptime(str(df[1]), '%Y-%m-%d').strftime('%d-%b-%Y'))
        print(option_data)
        return option_data
    except Exception as e:
        print("exception in getNseData Kite instruments  -----  " + str(e))


def getExpiryList():
    try:
        if option_data != "":
            global current_expiry
            current_expiry = option_data[0]
            print("Current Expiry = " + str(current_expiry))
            next_expiry = option_data[1]

            if str(current_expiry).split("-")[1] != (str(next_expiry).split("-")[1]):
                global is_monthly_expiry
                is_monthly_expiry = True
            return current_expiry
    except Exception as e:
        print("exception in getExpiryList  -----  " + str(e))


def getExistingOrders():
    try:
        print("Existing Orders")
        print(kite.orders())
        return kite.orders()
    except Exception as e:
        print("exception in getExistingOrders  -----  " + str(e))


def getCurrentIndexValue(tradingsymbol):
    return (kite.ltp(tradingsymbol)).get(tradingsymbol).get('last_price')
    #return int(input("Enter CurrentIndex value\n"))


def getCurrentAtm():
    try:
        niftyLTP = getCurrentIndexValue(TradeConstants.TRADE_SYMBOLE)
        print("Nifty current value = " + str(niftyLTP))
        niftySpot = 50 * round(niftyLTP / 50)
        print("Nifty spot value = " + str(niftySpot))
        return niftySpot
    except Exception as e:
        print("exception in getCurrentAtm  -----  " + str(e))


def getTradingSymbol(index_global):
    try:
        getExpiryList()
        global symbol
        today = datetime.date.today()
        year = str(today.year)[2:4]
        if is_monthly_expiry:
            month = str(current_expiry.split("-")[1]).upper()
            symbol = index_global + year + month
            print(symbol)
        else:
            # month = str(current_expiry.split("-")[1]).upper()[0]
            # currentMonth = datetime.datetime.now().month
            monthList = dict(Jan=1, Feb=2, Mar=3, Apr=4, May=5, Jun=6, Jul=7, Aug=8, Sep=9, Oct=10, Nov=11, Dec=12)
            month = str(current_expiry.split("-")[1])
            next_thursday = rrule(freq=WEEKLY, dtstart=today, byweekday=TH, count=1)[0]
            date = str(next_thursday)[8:10]
            symbol = "" + index_global + year + str(monthList[month]) + date
            print(symbol)
        return symbol
    except Exception as e:
        print("exception in getTradingSymbol  -----  " + str(e))


def getLTPForOption(currentPremiumPlaced, action):
    try:
        ltp_str = json.dumps(kite.quote("NFO:" + currentPremiumPlaced))
        ltp = json.loads(ltp_str)["NFO:" + currentPremiumPlaced]["last_price"]
        print("LTP Logs = " + currentPremiumPlaced + " \t " + action + " \t" + str(ltp) + "\t" + str(
            datetime.datetime.now()) + "\n")
        if str(currentPremiumPlaced).__contains__("BANK"):
            addLogToFile(TradeConstants.BN_OPTION_NAME,
                         "TradeBook = \t" + currentPremiumPlaced + " \t " + action + " \t" + str(ltp) + "\t" + str(
                             datetime.datetime.now()))
        else:
            addLogToFile(TradeConstants.TRADE_INDEX,
                         "TradeBook = \t" + currentPremiumPlaced + " \t " + action + " \t" + str(ltp) + "\t" + str(
                             datetime.datetime.now()))

        print("__________")
        sendMessageInTelegram(
            currentPremiumPlaced + " \t " + action + " \t" + str(ltp) + "\t" + str(datetime.datetime.now()))
        return ltp
    except Exception as e:
        if str(currentPremiumPlaced).__contains__("BANK"):
            addLogToFile(TradeConstants.BN_OPTION_NAME, "exception in getLTPForOption  -----  " + str(e))
        else:
            addLogToFile(TradeConstants.TRADE_INDEX, "exception in getLTPForOption  -----  " + str(e))


def exitOrder(message, currentPremiumPlaced, lotSize):
    try:
        # global currentPremiumPlaced
        print(currentPremiumPlaced)
        if currentPremiumPlaced != "":
            # print(currentPremiumPlaced)
            order_id = kite.place_order(tradingsymbol=currentPremiumPlaced, variety=kite.VARIETY_REGULAR,
                                        exchange=kite.EXCHANGE_NFO,
                                        transaction_type=kite.TRANSACTION_TYPE_SELL,
                                        quantity=lotSize,
                                        order_type=kite.ORDER_TYPE_MARKET, product=kite.PRODUCT_MIS)
            print(order_id)
            if str(currentPremiumPlaced).__contains__("BANK"):
                addLogToFile(TradeConstants.BN_OPTION_NAME, currentPremiumPlaced + "Order Exited SuccessFully")
            else:
                addLogToFile(TradeConstants.TRADE_INDEX, currentPremiumPlaced + "Order Exited SuccessFully")
            getLTPForOption(currentPremiumPlaced, "exit -- " + message)
            currentPremiumPlaced = "No Current Orders"
        print(currentPremiumPlaced)

    except Exception as e:
        print("exception in exitOrder ---- " + str(e))


#
# def checkIfOrderExists(currentPremiumPlaced):
#     try:
#         position_string = json.dumps(getExistingOrders())
#         position_json = json.loads(position_string)
#         allDayPositions = position_json['day']
#         print(allDayPositions)
#         if allDayPositions != []:
#             for position in allDayPositions:
#                 print(position['tradingsymbol'])
#                 if position['tradingsymbol'] == currentPremiumPlaced:
#                     if position['quantity'] >= 0:
#                         print(position['last_price'])
#                         exitOrder("exit order", currentPremiumPlaced)
#         else:
#             print("No day positions")
#         print()
#     except Exception as e:
#         print("exception in checkIfOrderExists  -----  " + str(e))


def sendMessageInTelegram(message):
    try:
        botId = "5962420966:AAEWI5ym4lIFUuRziUc-M21NcWng4uxRjgU"
        url = "https://api.telegram.org/bot" + botId + "/sendMessage"

        for user_id in TradeConstants.TELEGRAM_IDS:
            payload = {
                'text': message,
                'chat_id': user_id
            }

            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }

            response = requests.post(url=url, params=payload, headers=headers)
            # print(response)
    except Exception as e:
        addLogToFile("COMMON", "exception in sendMessageInTelegram  -----  " + str(e))


def checkProfile():
    profile = kite.get_profile()
    if profile.__str__().__contains__("error"):
        return "token error"
    else:
        return profile['user_name']


########### Bank Nifty Changes ###########

def getCurrentAtmDynamically(tradingSymbol, roundValue):
    try:
        indexLtp = getCurrentIndexValue(tradingSymbol)
        print("indexLtp current value = " + str(indexLtp))
        indexSpot = roundValue * round(indexLtp / roundValue)
        print("indexLtp spot value = " + str(indexSpot))
        return indexSpot
    except Exception as e:
        print("exception in getCurrentAtmDynamically  -----  " + str(e))
