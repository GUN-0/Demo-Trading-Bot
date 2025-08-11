import logging

logger = logging.getLogger(__name__)

def check_strategy(last_price, price_threshold, has_position):
    """
    현재 포지션 상태를 고려한 간단한 트레이딩 전략.
    'BUY', 'SELL', 'HOLD' 중 하나의 신호를 반환합니다.
    """
    if not has_position:
        # 포지션이 없을 때
        if last_price < price_threshold:
            logger.info(f"Strategy: Price ({last_price:,.2f}) is below threshold (${price_threshold:,.2f}). Firing BUY signal.")
            return 'BUY'
        else:
            logger.info(f"Strategy: No position and price is not low enough. Firing HOLD signal.")
            return 'HOLD'
    else:
        # 포지션이 있을 때
        if last_price >= price_threshold:
            logger.info(f"Strategy: Price ({last_price:,.2f}) is at or above threshold (${price_threshold:,.2f}). Firing SELL signal.")
            return 'SELL'
        else:
            logger.info(f"Strategy: Position exists and price is not high enough. Firing HOLD signal.")
            return 'HOLD'
