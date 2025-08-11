import ccxt
import time
import logging
import config
from strategy import check_strategy

# --- Configuration ---
# Bitget 데모 선물(Futures) 거래를 위한 심볼
SYMBOL = 'SBTC/SUSDT:SUSDT'  # sBTCUSDT 대신 CCXT 표준에 맞는 심볼 사용  # sBTCUSDT 대신 CCXT 표준에 맞는 심볼 사용
PRICE_THRESHOLD = 60000
LOOP_INTERVAL_SECONDS = 30
BUY_AMOUNT = 0.001
SELL_AMOUNT = 0.001

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Main Bot Logic ---
def main():
    """The main function to run the trading bot."""
    logger.info("--- Starting Bitget Demo Futures Trading Bot ---")

    # --- Initialize Exchange ---
    if not all([config.API_KEY, config.SECRET_KEY, config.PASSPHRASE]):
        logger.error("API credentials not found. Please check your .env file.")
        return

    try:
        exchange = ccxt.bitget({
            'apiKey': config.API_KEY,
            'secret': config.SECRET_KEY,
            'password': config.PASSPHRASE,
            'options': {
                'defaultType': 'future',  # 선물(Futures) 거래를 위해 'future'로 설정
            },
            'timeout': 30000,  # 30초 타임아웃 설정
        })
        exchange.set_sandbox_mode(True)
        logger.info("Successfully connected to Bitget Sandbox.")
    except Exception as e:
        logger.error(f"Error initializing exchange: {e}")
        return

    # --- Trading Loop ---
    while True:
        try:
            # --- Fetch Data ---
            logger.info(f"Fetching ticker for {SYMBOL}...")
            ticker = exchange.fetch_ticker(SYMBOL)
            last_price = ticker['last']
            logger.info(f"Ticker fetched successfully. Last price: {last_price}")

            logger.info("Fetching positions...")
            # 모든 포지션을 가져온 후, 특정 심볼로 필터링 (API는 심볼 인자를 받지 않음)
            all_positions = exchange.fetch_positions()
            logger.info("Positions fetched successfully.")
            
            # CCXT 심볼(예: 'SBTC/SUSDT:SUSDT')을 API가 사용하는 심볼(예: 'SBTCUSDT')로 변환
            target_symbol_for_api = SYMBOL.split(':')[0].replace('/', '')
            positions = [p for p in all_positions if p.get('info', {}).get('symbol') == target_symbol_for_api]

            # 필터링된 포지션이 실제로 존재하는지 확인
            has_position = len(positions) > 0 and positions[0].get('contracts', 0) > 0

            # --- Log Current State ---
            position_info = "No position"
            if has_position:
                pos = next((p for p in positions if p['contracts'] > 0), None)
                if pos:
                    side = pos.get('side')
                    contracts = pos.get('contracts')
                    entry_price = pos.get('entryPrice')
                    position_info = f"Position: {contracts} {pos.get('symbol')} ({side}) at ${entry_price:,.2f}"
            logger.info(position_info)

            logger.info(f"Current price for {SYMBOL} is: ${last_price:,.2f}")

            # --- Strategy and Execution ---
            signal = check_strategy(last_price, PRICE_THRESHOLD, has_position)
            logger.info(f"Strategy signal: {signal}")

            if signal == 'BUY':
                logger.info(f"BUY signal received. Placing a market buy order for {BUY_AMOUNT} {SYMBOL}.")
                order = exchange.create_market_buy_order_with_cost(SYMBOL, cost=100)
                logger.info(f"Order placed: {order['id']}")
            elif signal == 'SELL':
                logger.info(f"SELL signal received. Placing a market sell order for {SELL_AMOUNT} {SYMBOL}.")
                order = exchange.create_market_sell_order(SYMBOL, SELL_AMOUNT)
                logger.info(f"Order placed: {order['id']}")
            else:
                logger.info("No trading signal. Holding current position.")

        except ccxt.NetworkError as e:
            logger.warning(f"Network error: {e}. Retrying...")
        except ccxt.ExchangeError as e:
            logger.error(f"Exchange error: {e}. Stopping bot.")
            break
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            break

        logger.info(f"--- Waiting for {LOOP_INTERVAL_SECONDS} seconds... ---")
        time.sleep(LOOP_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()