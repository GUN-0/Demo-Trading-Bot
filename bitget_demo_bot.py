import ccxt
import time
import logging
import config
from strategy import check_strategy

# --- Configuration ---
SYMBOL = 'BTCUSDT'
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


class TradingBot:
    def __init__(self):
        # --- Exchange Setup ---
        if not all([config.API_KEY, config.SECRET_KEY, config.PASSPHRASE]):
            raise ValueError("API credentials not found. Please check your .env file.")

        self.exchange = ccxt.bitget({
            'apiKey': config.API_KEY,
            'secret': config.SECRET_KEY,
            'password': config.PASSPHRASE,
            'options': {
                'defaultType': 'future',
            },
        })
        self.exchange.set_sandbox_mode(True)
        logger.info("Successfully connected to Bitget Sandbox.")

        # --- State & PnL Tracking ---
        self.initial_balance = self.fetch_balance()
        self.trade_count = 0
        self.wins = 0
        self.entry_price = 0  # Stores the entry price when a position is opened

        logger.info(f"Bot initialized. Initial balance: {self.initial_balance:.4f} USDT")

    def fetch_balance(self):
        """Fetches the current balance of the quote currency."""
        try:
            balance_data = self.exchange.fetch_balance()
            # In sandbox, the USDT equivalent is SUSDT
            return balance_data['total'].get('USDT', 0)
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return 0 # Return 0 if balance can't be fetched

    def run(self):
        """The main trading loop."""
        while True:
            try:
                # --- Fetch Data ---
                current_price = self.exchange.fetch_ticker(SYMBOL)['last']
                current_balance = self.fetch_balance()
                
                # --- Position Check ---
                all_positions = self.exchange.fetch_positions()
                position_info = next((p for p in all_positions if p.get('info', {}).get('symbol') == SYMBOL), None)
                has_position = position_info is not None and float(position_info.get('contracts', 0)) > 0

                # --- Strategy & Execution ---
                signal = check_strategy(current_price, PRICE_THRESHOLD, has_position)
                
                if signal == 'BUY' and not has_position:
                    logger.info(f"BUY signal received. Placing a market buy order for {BUY_AMOUNT} {SYMBOL}.")
                    # self.exchange.create_market_buy_order(SYMBOL, BUY_AMOUNT) # Uncomment to enable live trading
                    logger.info(f"Simulating BUY order at {current_price}") # Simulation
                    self.entry_price = current_price # Record entry price

                elif signal == 'SELL' and has_position:
                    logger.info(f"SELL signal received. Placing a market sell order for {SELL_AMOUNT} {SYMBOL}.")
                    # self.exchange.create_market_sell_order(SYMBOL, SELL_AMOUNT) # Uncomment to enable live trading
                    logger.info(f"Simulating SELL order at {current_price}") # Simulation
                    
                    # --- PnL & Win Rate Calculation ---
                    if self.entry_price > 0: # Ensure we have a valid entry price
                        self.trade_count += 1
                        if current_price > self.entry_price:
                            self.wins += 1
                            logger.info("Trade result: WIN")
                        else:
                            logger.info("Trade result: LOSS")
                    self.entry_price = 0 # Reset entry price after closing position

                # --- Log Status ---
                self.log_status(current_balance, current_price, signal, position_info)

            except ccxt.NetworkError as e:
                logger.warning(f"Network error: {e}. Retrying...")
            except ccxt.ExchangeError as e:
                logger.error(f"Exchange error: {e}. Stopping bot.")
                break
            except Exception as e:
                logger.error(f"An unexpected error occurred: {e}", exc_info=True)
                break
            
            logger.info(f"--- Waiting for {LOOP_INTERVAL_SECONDS} seconds... ---")
            time.sleep(LOOP_INTERVAL_SECONDS)

    def log_status(self, current_balance, current_price, signal, position_info):
        """Logs the current status of the bot."""
        pnl = ((current_balance - self.initial_balance) / self.initial_balance) * 100 if self.initial_balance > 0 else 0
        win_rate = (self.wins / self.trade_count) * 100 if self.trade_count > 0 else 0

        status_report = (
            f"\n"
            f"================ BOT STATUS =================\n"
            f"|| Price:       ${current_price:,.2f}\n"
            f"|| Signal:      {signal}\n"
            f"||------------------------------------------\n"
            f"|| Balance:     {current_balance:,.4f} USDT\n"
            f"|| PnL:           {pnl:,.2f}%\n"
            f"|| Win Rate:    {win_rate:,.2f}% ({self.wins}/{self.trade_count} trades)\n"
            f"============================================"
        )
        logger.info(status_report)


if __name__ == "__main__":
    try:
        bot = TradingBot()
        bot.run()
    except Exception as e:
        logger.critical(f"Failed to initialize and run the bot: {e}", exc_info=True)
