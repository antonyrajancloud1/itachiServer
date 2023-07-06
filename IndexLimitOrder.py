import os

from dateutil.rrule import rrule, WEEKLY, TH
from flask import *
import datetime
import pandas as pd

import KiteActions
import TradeConstants

from kite_trade import KiteApp

app = Flask(__name__)
apiToken = os.environ.get('APITOKEN')
kite = KiteApp(enctoken=apiToken)

isTradeAllowed = True
option_data = {}
current_expiry = ""
index_global = "NIFTY"
is_monthly_expiry = False
tradingsymbol = 'NSE:NIFTY 50'
lots = os.getenv("NIFTY_LOTS")
bn_lots = os.getenv("BN_LOTS")
targetPoints = os.getenv("NIFTY_TARGET")
bn_targetPoints = os.getenv("BN_TARGET")

# lots = 1
qty = 50 * int(lots)
# targetPoints = 10
# bn_lots = 1
bn_qty = 25 * int(lots)

isOrderPlaced = False
currentPremiumPlaced = ""
currentOrderID = ""
currentPremiumPlacedBN = ""
currentOrderID_BN = ""
isOrderPlaced_BN = False


def getUserName():
    try:
        return kite.get_profile()["user_name"]
    except Exception as e:
        print("exception in getUserName Kite   -----  " + str(e))
        return "Check Token"


userName = getUserName()


def getnsedata():
    try:
        global option_data
        df = pd.DataFrame(kite.instruments())
        df = df[(df.name == index_global)]
        df = sorted(df.expiry.unique())
        option_data[0] = str(datetime.datetime.strptime(str(df[0]), '%Y-%m-%d').strftime('%d-%b-%Y'))
        option_data[1] = str(datetime.datetime.strptime(str(df[1]), '%Y-%m-%d').strftime('%d-%b-%Y'))
        print(option_data)
    except BaseException as e:
        print("exception in getNseData Kite instruments  -----  " + str(e))


def getExpiryList():
    try:
        if option_data != "":
            global current_expiry
            current_expiry = option_data[0]
            print("Current Expiry = " + str(current_expiry))
            next_expiry = option_data[1]

            if (str(current_expiry).split("-")[1] != (str(next_expiry).split("-")[1])):
                global is_monthly_expiry
                is_monthly_expiry = True
            return current_expiry
    except BaseException as e:
        print("exception in getExpiryList  -----  " + str(e))


def getExistingOrders():
    try:
        print("Existing Orders")
        print(kite.orders())
        return kite.orders()
    except BaseException as e:
        print("exception in getExistingOrders  -----  " + str(e))


def placeCallOption(message):
    global currentPremiumPlaced
    global currentOrderID
    try:
        if isTradeAllowed:
            exitOrder(message, currentPremiumPlaced, currentOrderID)
            # rsiValue = round(getCurrentRSI())
            # if rsiValue > 50:
            optionToBuy = KiteActions.getTradingSymbol(TradeConstants.TRADE_INDEX) + str(
                KiteActions.getCurrentAtmDynamically(TradeConstants.TRADE_SYMBOLE,
                                                     TradeConstants.ROUND_OFF_VALUE) - 200) + "CE"

            currentPremiumPlaced = optionToBuy
            print("Current premium  = " + str(currentPremiumPlaced))
            order_id = kite.place_order(tradingsymbol=optionToBuy, variety=kite.VARIETY_REGULAR,
                                        exchange=kite.EXCHANGE_NFO,
                                        transaction_type=kite.TRANSACTION_TYPE_BUY, quantity=qty,
                                        order_type=kite.ORDER_TYPE_MARKET, product=kite.PRODUCT_NRML)
            if order_id["status"] == "success":
                if order_id["data"]["order_id"] != "":
                    optionLtp = getLTPForOption("Option For LimitOrder", currentPremiumPlaced)
                    target = int(optionLtp) + int(targetPoints)
                    sell_order = kite.place_order(tradingsymbol=optionToBuy, variety=kite.VARIETY_REGULAR,
                                                  exchange=kite.EXCHANGE_NFO,
                                                  transaction_type=kite.TRANSACTION_TYPE_SELL, quantity=qty,
                                                  price=target,
                                                  order_type=kite.ORDER_TYPE_LIMIT, product=kite.PRODUCT_NRML)
                    print("*** Buy Order Details ***")
                    print(order_id)
                    print(currentPremiumPlaced + " call Option")
                    getLTPForOption("Buy  -- " + message, currentPremiumPlaced)
                    print("*** Sell Order Details ***")
                    print(sell_order)

                    currentOrderID = sell_order["data"]["order_id"]
                    print("Sell order placed with target || Order ID = " + str(currentOrderID))
                    print("target price === " + str(target))
                    global isOrderPlaced
                    isOrderPlaced = True
                    # checkForTarget(getCurrentIndexValue())
            else:
                print(order_id)
        # else:
        #    print("RSI value is not greater tha 50|| Current RSI = "+ str(rsiValue))
        else:
            print('Trading is blocked in server')
    except BaseException as e:
        print("exception in placeCallOption ---- " + str(e))


def placePutOption(message):
    global currentPremiumPlaced
    global currentOrderID
    try:
        if isTradeAllowed:
            exitOrder(message, currentPremiumPlaced, currentOrderID)
            # rsiValue = round(getCurrentRSI())
            # if rsiValue < 50:
            # optionToBuy = getTradingSymbol() + str(getCurrentAtm() + 200) + "PE"
            optionToBuy = KiteActions.getTradingSymbol(TradeConstants.TRADE_INDEX) + str(
                KiteActions.getCurrentAtmDynamically(TradeConstants.TRADE_SYMBOLE,
                                                     TradeConstants.ROUND_OFF_VALUE) + 200) + "PE"
            currentPremiumPlaced = optionToBuy
            print("Current premium  = " + str(currentPremiumPlaced))
            order_id = kite.place_order(tradingsymbol=optionToBuy, variety=kite.VARIETY_REGULAR,
                                        exchange=kite.EXCHANGE_NFO,
                                        transaction_type=kite.TRANSACTION_TYPE_BUY, quantity=qty,
                                        order_type=kite.ORDER_TYPE_MARKET, product=kite.PRODUCT_NRML)
            if order_id["status"] == "success":
                if order_id["data"]["order_id"] != "":
                    currentPremiumPlaced = optionToBuy
                    optionLtp = getLTPForOption("Option For LimitOrder", currentPremiumPlaced)
                    target = int(optionLtp) + int(targetPoints)
                    sell_order = kite.place_order(tradingsymbol=optionToBuy, variety=kite.VARIETY_REGULAR,
                                                  exchange=kite.EXCHANGE_NFO,
                                                  transaction_type=kite.TRANSACTION_TYPE_SELL, quantity=qty,
                                                  price=target,
                                                  order_type=kite.ORDER_TYPE_LIMIT, product=kite.PRODUCT_NRML)
                    print("*** Buy Order Details ***")
                    print(order_id)
                    print(currentPremiumPlaced + " Put Option")
                    getLTPForOption("Buy  -- " + message, currentPremiumPlaced)
                    print("*** Sell Order Details ***")
                    print(sell_order)
                    currentOrderID = sell_order["data"]["order_id"]
                    print("Sell order placed with target || Order ID = " + str(currentOrderID))
                    print("target price === " + str(target))
                    global isOrderPlaced
                    isOrderPlaced = True
                    # checkForTarget(getCurrentIndexValue())

            else:
                print(order_id)
        # else:
        #    print("Rsi is not less than 50 || Current RSI = " + str(rsiValue))
        else:
            print("Trading is blocked in server")
    except BaseException as e:
        print("exception in placePutOption ----- " + str(e))


def exitOrder(message, premium, exitorderID):
    global currentPremiumPlacedBN
    global currentPremiumPlaced
    try:
        print(premium)
        if premium != "":
            if exitorderID != "":
                print(premium)
                order_id = kite.modify_order(order_id=exitorderID, variety=kite.VARIETY_REGULAR,
                                             quantity=qty,
                                             order_type=kite.ORDER_TYPE_MARKET)
                print(order_id)
                print(premium + " exit order")
                getLTPForOption("exit -- " + message, premium)
                if str(premium).__contains__("BANK"):
                    currentPremiumPlacedBN = "No Current Orders In Bank Nifty"
                else:
                    currentPremiumPlaced = "No Current Orders in Nifty"
                    print(currentPremiumPlaced)


    except BaseException as e:
        print("exception in exitOrder ---- " + str(e))


def getCurrentIndexValue():
    return (kite.ltp(tradingsymbol)).get(tradingsymbol).get('last_price')


def getCurrentAtm():
    try:
        niftyLTP = getCurrentIndexValue()
        print("Nifty current value = " + str(niftyLTP))
        niftySpot = 50 * round(niftyLTP / 50)
        print("Nifty spot value = " + str(niftySpot))
        return niftySpot
    except BaseException as e:
        print("exception in getCurrentAtm  -----  " + str(e))


def getTradingSymbol():
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
    except BaseException as e:
        print("exception in getTradingSymbol  -----  " + str(e))


def getLTPForOption(action, premium):
    try:
        print("__________")
        ltp_str = json.dumps(kite.quote("NFO:" + premium))
        ltp = json.loads(ltp_str)["NFO:" + premium]["last_price"]
        print("tradebooklogs = " + premium + " \t " + action + " \t" + str(ltp) + "\t" + str(
            datetime.datetime.now()) + "\n")
        print("__________")
        return ltp
    except BaseException as e:
        print("exception in getLTPForOption  -----  " + str(e))


# def checkIfOrderExists():
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
#                         exitOrder("exit order")
#         else:
#             print("No day positions")
#         print()
#     except BaseException as e:
#         print("exception in checkIfOrderExists  -----  " + str(e))


# def checkForTarget(niftySpot):
#     try:
#         print("Nifty value while place order " + str(niftySpot))
#         target = int(niftySpot) + int(targetPoints)
#         stopLoss = int(niftySpot) - int(targetPoints)
#         print("Target " + str(target))
#         print("SL " + str(stopLoss))
#         global isOrderPlaced
#         while isOrderPlaced:
#             indexCurrentValue = int(getCurrentIndexValue())
#             # print("position is active")
#             if indexCurrentValue >= target:
#                 exitOrder("checkForTarget")
#                 print("Exit trade considering target")
#                 print(getCurrentIndexValue())
#                 isOrderPlaced = False
#                 break
#             elif indexCurrentValue <= stopLoss:
#                 exitOrder("checkForTarget")
#                 print("Exit trade considering Stoploss")
#                 print(getCurrentIndexValue())
#
#                 isOrderPlaced = False
#                 break
#             time.sleep(3)
#     except Exception as e:
#         print("exception in checkForTarget  -----  " + str(e))


def placeBNCallOption(message):
    global currentPremiumPlacedBN
    global currentOrderID_BN
    global isOrderPlaced_BN

    try:
        if isTradeAllowed:
            exitOrder(message, currentPremiumPlacedBN, currentOrderID_BN)
            # rsiValue = round(getCurrentRSI())
            # if rsiValue > 50:
            optionToBuy = KiteActions.getTradingSymbol(TradeConstants.BN_OPTION_NAME) + str(
                KiteActions.getCurrentAtmDynamically(TradeConstants.BN_TRADE_SYMBOLE,
                                                     TradeConstants.BN_ROUND_OFF_VALUE) - 200) + "CE"
            currentPremiumPlacedBN = optionToBuy
            print("Current premium  = " + str(currentPremiumPlacedBN))
            order_id = kite.place_order(tradingsymbol=optionToBuy, variety=kite.VARIETY_REGULAR,
                                        exchange=kite.EXCHANGE_NFO,
                                        transaction_type=kite.TRANSACTION_TYPE_BUY, quantity=bn_qty,
                                        order_type=kite.ORDER_TYPE_MARKET, product=kite.PRODUCT_NRML)
            if order_id["status"] == "success":
                if order_id["data"]["order_id"] != "":
                    optionLtp = getLTPForOption("Option For LimitOrder", currentPremiumPlacedBN)
                    target = int(optionLtp) + int(bn_targetPoints)
                    sell_order = kite.place_order(tradingsymbol=optionToBuy, variety=kite.VARIETY_REGULAR,
                                                  exchange=kite.EXCHANGE_NFO,
                                                  transaction_type=kite.TRANSACTION_TYPE_SELL, quantity=bn_qty,
                                                  price=target,
                                                  order_type=kite.ORDER_TYPE_LIMIT, product=kite.PRODUCT_NRML)
                    print("*** Buy Order Details ***")
                    print(order_id)
                    print(currentPremiumPlaced + " call Option")
                    getLTPForOption("Buy  -- " + message, currentPremiumPlacedBN)
                    print("*** Sell Order Details ***")
                    print(sell_order)
                    currentOrderID_BN = sell_order["data"]["order_id"]
                    print("Sell order placed with target || Order ID = " + str(currentOrderID_BN))
                    print("target price === " + str(target))
                    isOrderPlaced_BN = True
                    # checkForTarget(getCurrentIndexValue())
            else:
                print(order_id)
        # else:
        #    print("RSI value is not greater tha 50|| Current RSI = "+ str(rsiValue))
        else:
            print('Trading is blocked in server')
    except BaseException as e:
        print("exception in placeBNCallOption ---- " + str(e))


def placeBNPutOption(message):
    global currentPremiumPlacedBN
    global currentOrderID_BN
    global isOrderPlaced_BN
    try:
        if isTradeAllowed:
            exitOrder(message, currentPremiumPlacedBN, currentOrderID_BN)
            # rsiValue = round(getCurrentRSI())
            # if rsiValue < 50:
            optionToBuy = KiteActions.getTradingSymbol(TradeConstants.BN_OPTION_NAME) + str(
                KiteActions.getCurrentAtmDynamically(TradeConstants.BN_TRADE_SYMBOLE,
                                                     TradeConstants.BN_ROUND_OFF_VALUE) + 200) + "PE"
            currentPremiumPlacedBN = optionToBuy
            order_id = kite.place_order(tradingsymbol=optionToBuy, variety=kite.VARIETY_REGULAR,
                                        exchange=kite.EXCHANGE_NFO,
                                        transaction_type=kite.TRANSACTION_TYPE_BUY, quantity=bn_qty,
                                        order_type=kite.ORDER_TYPE_MARKET, product=kite.PRODUCT_NRML)
            if order_id["status"] == "success":
                if order_id["data"]["order_id"] != "":
                    currentPremiumPlacedBN = optionToBuy
                    optionLtp = getLTPForOption("Option For LimitOrder", currentPremiumPlacedBN)
                    target = int(optionLtp) + int(bn_targetPoints)
                    sell_order = kite.place_order(tradingsymbol=optionToBuy, variety=kite.VARIETY_REGULAR,
                                                  exchange=kite.EXCHANGE_NFO,
                                                  transaction_type=kite.TRANSACTION_TYPE_SELL, quantity=bn_qty,
                                                  price=target,
                                                  order_type=kite.ORDER_TYPE_LIMIT, product=kite.PRODUCT_NRML)
                    print("*** Buy Order Details ***")
                    print(order_id)
                    print(currentPremiumPlacedBN + " Put Option")
                    getLTPForOption("Buy  -- " + message, currentPremiumPlacedBN)
                    print("*** Sell Order Details ***")
                    print(sell_order)
                    currentOrderID_BN = sell_order["data"]["order_id"]
                    print("Sell order placed with target || Order ID = " + str(currentOrderID_BN))
                    print("target price === " + str(target))
                    isOrderPlaced_BN = True
                    # checkForTarget(getCurrentIndexValue())

            else:
                print(order_id)
        # else:
        #    print("Rsi is not less than 50 || Current RSI = " + str(rsiValue))
        else:
            print("Trading is blocked in server")
    except BaseException as e:
        print("exception in placePutOption ----- " + str(e))


@app.route('/')
def index():
    return render_template('html/algoscalping.html')


@app.route('/exit_nifty', methods=["GET", "POST"])
def exitCurrentOrder():
    print("Exit Order")
    exitOrder("exit", currentPremiumPlaced, currentOrderID)
    return render_template('html/algoscalping.html', option=currentPremiumPlaced + "Order Exited")


@app.route('/exit_bank_nifty', methods=["GET", "POST"])
def exitCurrentOrderBN():
    print("Exit Order")
    exitOrder("exit", currentPremiumPlacedBN, currentOrderID_BN)
    return render_template('html/algoscalping.html', option=currentPremiumPlaced + "Order Exited")


#######################
@app.route('/buy', methods=["GET", "POST"])
def buyCE():
    print("Entry CE")
    placeCallOption("CE")
    return render_template('html/algoscalping.html', option=currentPremiumPlaced + "Order placed")


@app.route('/sell', methods=["GET", "POST"])
def buyPE():
    print("Entry PE")
    placePutOption("PE")
    return render_template('html/algoscalping.html', option=currentPremiumPlaced + " Order placed")


# @app.route('/exit', methods=["GET", "POST"])
# def exit():
#     exitOrder("exit")
#     return render_template('html/algoscalping.html', option=currentPremiumPlaced + " Order placed")
@app.route('/settoggle/<message>', methods=["GET", "POST"])
def setToggle(message):
    print("Set toggle")
    global isTradeAllowed
    if message == "false":
        isTradeAllowed = False
    elif message == "true":
        isTradeAllowed = True
    print(isTradeAllowed)
    return render_template('html/algoscalping.html', option=isTradeAllowed)


@app.route('/getvalues', methods=["GET", "POST"])
def getvalues():
    allValues = {"currentPremiumPlaced": currentPremiumPlaced, "lots": lots, "targetPoints": targetPoints,
                 "userName": userName, "currentPremiumPlacedBN": currentPremiumPlacedBN,
                 "bn_targetPoints": bn_targetPoints, "bn_lots": bn_lots}
    return allValues


@app.route('/buy_bank_ce', methods=["GET", "POST"])
def buy_bank_ce():
    print("Entry CE")
    placeBNCallOption("CE")
    return render_template('html/algoscalping.html', option=currentPremiumPlacedBN + "Order placed")


@app.route('/buy_bank_pe', methods=["GET", "POST"])
def buy_bank_pe():
    print("Entry PE")
    placeBNPutOption("PE")
    return render_template('html/algoscalping.html', option=currentPremiumPlacedBN + "Order placed")


######################

KiteActions.getnsedata()
print("ITACHI Started")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)
