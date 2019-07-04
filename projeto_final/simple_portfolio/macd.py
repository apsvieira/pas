from typing import Optional

import numpy as np
import pandas as pd

from simple_portfolio.adaptive_filters import lms, error_signal_lms, rls


class MACD:
    def __init__(
        self,
        quotes: pd.DataFrame,
        short_periods: int,
        long_periods: int,
        signal_periods: int,
        tolerance: float = 2e-1
    ) -> None:
        assert isinstance(quotes, pd.DataFrame), "Quotes object should be a DataFrame."

        self.short_periods = short_periods
        self.long_periods = long_periods
        self.signal_periods = signal_periods
        self.tolerance = tolerance
        self.quotes = self._construct_indicator(quotes)
        self.signals = self._make_signals()

    def _construct_indicator(self, quotes: pd.DataFrame) -> pd.DataFrame:
        # Standard MACD Algorithm
        quotes['short_ma'] = quotes['close'].ewm(span=self.short_periods).mean()
        quotes['long_ma'] = quotes['close'].ewm(span=self.long_periods).mean()
        quotes['macd'] = quotes['short_ma'] - quotes['long_ma']
        quotes['signal_line'] = quotes['macd'].ewm(span=self.signal_periods).mean()

        quotes['relative_signal'] = quotes['macd'] - quotes['signal_line']

        return quotes

    def _make_signals(self) -> pd.Series:
        quotes = self.quotes.copy()

        is_small = quotes['relative_signal'].abs() <= self.tolerance
        change_velocity = np.sign(quotes['relative_signal'].diff().fillna(0))
        quotes['signal'] = is_small * change_velocity

        return quotes[['signal']]


class LMS_MACD(MACD):
    def __init__(
        self,
        quotes: pd.DataFrame,
        short_periods: int,
        long_periods: int,
        signal_periods: int,
        tolerance: float = 2e-1,
        pace: Optional[float] = None
    ) -> None:
        if pace is None:
            signal = quotes.eval("(high + low + close) / 3").values
            pace = signal.var() / np.correlate(signal, signal, 'valid')
        self.pace = pace

        super().__init__(quotes, short_periods, long_periods, signal_periods,  tolerance)

    def _construct_indicator(self, quotes: pd.DataFrame) -> pd.Series:
        entry = quotes['close'].shift().values
        entry[0] = quotes['open'].values[0]
        reference = quotes['close'].values

        estimate_short, _ = lms(entry, reference, self.short_periods, self.pace)
        estimate_long, _ = lms(entry, reference, self.long_periods, self.pace)
        estimate_short = pd.Series(estimate_short)
        estimate_long = pd.Series(estimate_long)

        quotes['short_ma'] = estimate_short.ewm(span=self.short_periods).mean()
        quotes['long_ma'] = estimate_long.ewm(span=self.long_periods).mean()
        quotes['macd'] = quotes['short_ma'] - quotes['long_ma']

        entry = quotes['macd'].shift().values
        entry[0] = quotes['open'].values[0]
        reference = quotes['macd'].values

        estimate_signal, _ = lms(entry, reference, self.signal_periods, self.pace)
        estimate_signal = pd.Series(estimate_signal)

        quotes['signal_line'] = estimate_signal.ewm(span=self.signal_periods).mean()
        quotes['relative_signal'] = quotes['macd'] - quotes['signal_line']

        return quotes


class ES_MACD(LMS_MACD):
    def __init__(
        self,
        quotes: pd.DataFrame,
        short_periods: int,
        long_periods: int,
        signal_periods: int,
        tolerance: float = 2e-1,
        pace: Optional[float] = None
    ) -> None:
        super().__init__(quotes, short_periods, long_periods, signal_periods,  tolerance, pace)

    def _construct_indicator(self, quotes: pd.DataFrame) -> pd.Series:
        entry = quotes['close'].shift().values
        entry[0] = quotes['open'].values[0]
        reference = quotes['close'].values

        estimate_short, _ = error_signal_lms(entry, reference, self.short_periods, self.pace)
        estimate_long, _ = error_signal_lms(entry, reference, self.long_periods, self.pace)
        estimate_short = pd.Series(estimate_short)
        estimate_long = pd.Series(estimate_long)

        quotes['short_ma'] = estimate_short.ewm(span=self.short_periods).mean()
        quotes['long_ma'] = estimate_long.ewm(span=self.long_periods).mean()
        quotes['macd'] = quotes['short_ma'] - quotes['long_ma']

        entry = quotes['macd'].shift().values
        entry[0] = quotes['open'].values[0]
        reference = quotes['macd'].values

        estimate_signal, _ = error_signal_lms(entry, reference, self.signal_periods, self.pace)
        estimate_signal = pd.Series(estimate_signal)

        quotes['signal_line'] = estimate_signal.ewm(span=self.signal_periods).mean()
        quotes['relative_signal'] = quotes['macd'] - quotes['signal_line']

        return quotes


class RLS_MACD(MACD):
    def __init__(
        self,
        quotes: pd.DataFrame,
        short_periods: int,
        long_periods: int,
        signal_periods: int,
        lamb: float,
        sigma: float,
        tolerance: float = 2e-1
    ) -> None:
        self.lamb = lamb
        self.sigma = sigma

        super().__init__(quotes, short_periods, long_periods, signal_periods, tolerance)

    def _construct_indicator(self, quotes: pd.DataFrame) -> pd.Series:
        entry = quotes['close'].shift().values
        entry[0] = quotes['open'].values[0]
        reference = quotes['close'].values

        estimate_short, _ = rls(entry, reference, self.short_periods, self.lamb, self.sigma)
        estimate_long, _ = rls(entry, reference, self.long_periods, self.lamb, self.sigma)
        estimate_short = pd.Series(estimate_short)
        estimate_long = pd.Series(estimate_long)

        quotes['short_ma'] = estimate_short.ewm(span=self.short_periods).mean()
        quotes['long_ma'] = estimate_long.ewm(span=self.long_periods).mean()
        quotes['macd'] = quotes['short_ma'] - quotes['long_ma']

        entry = quotes['macd'].shift().values
        entry[0] = quotes['open'].values[0]
        reference = quotes['macd'].values

        estimate_signal, _ = rls(entry, reference, self.signal_periods, self.lamb, self.sigma)
        estimate_signal = pd.Series(estimate_signal)

        quotes['signal_line'] = estimate_signal.ewm(span=self.signal_periods).mean()
        quotes['relative_signal'] = quotes['macd'] - quotes['signal_line']

        return quotes
