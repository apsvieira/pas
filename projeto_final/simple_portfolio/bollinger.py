from typing import Optional

import numpy as np
import pandas as pd
import plotly.offline as py
import plotly.graph_objs as go

from simple_portfolio.adaptive_filters import lms


class BollingerBands:
    def __init__(
        self,
        quotes: pd.DataFrame,
        num_periods: int,
        deviations: float,
        long_periods: int = 60
    ) -> None:
        assert isinstance(quotes, pd.DataFrame), "Quotes object should be a DataFrame."

        self.num_periods = num_periods
        self.deviations = deviations
        self.long_periods = long_periods
        self.quotes = self._construct_bands(quotes)
        self.signals = self._make_signals()

    def _construct_bands(self, quotes: pd.DataFrame) -> pd.DataFrame:
        # Standard Bolling Bands Algorithm
        quotes['TP'] = quotes.eval("(high + low + close) / 3")

        quotes['std_dev'] = quotes['TP'].rolling(self.num_periods).std()

        quotes['band_center'] = quotes['TP'].rolling(self.num_periods).mean()
        quotes['band_upper'] = quotes['band_center'] + self.deviations * quotes['std_dev']
        quotes['band_lower'] = quotes['band_center'] - self.deviations * quotes['std_dev']

        # Long term rolling standard deviation, used to evaluate "consolidation periods".
        quotes['long_term_std'] = quotes['TP'].rolling(self.long_periods).std()

        return quotes

    def _make_signals(self):
        quotes = self.quotes.copy()

        quotes['signal_short'] = quotes.eval('high >= band_upper').astype(int)
        quotes['signal_long'] = quotes.eval('low <= band_lower').astype(int)

        # In practice, this only has an impact in very high volatility situations.
        # In those situations, it might be relevant not to trade at all, as we don't have a good
        # estimate of in which direction the market "will move"
        quotes['signal'] = quotes['signal_long'] - quotes['signal_short']

        return quotes[['signal']]

    def plot_candlesticks(self, filename: str, last: int = 60):
        quotes = self.quotes

        candles = go.Candlestick(
            x=quotes.index.get_level_values('datetime'),
            open=quotes['open'],
            high=quotes['high'],
            low=quotes['low'],
            close=quotes['close']
        )

        layout = {
            "showlegend": False,
            "xaxis": {
                "autorange": True,
                "domain": [0, 1],
                "range": [quotes.index.min(), quotes.index.max()],
                "rangeslider": {"range": [quotes.index.min(), quotes.index.max()]},
                "title": 'Date',
                "type": 'category',
                "categoryorder": 'category ascending'
            },
            "yaxis": {
                "autorange": "visible",
                "domain": [0, 1],
                "type": 'linear'
            }

        }

        data = [candles]

        fig = {'data': data, 'layout': layout}

        py.iplot(data, filename=filename)


class LMSBands(BollingerBands):
    def __init__(
        self,
        quotes: pd.DataFrame,
        num_periods: int,
        deviations: float,
        long_periods: int = 60,
        pace: Optional[float] = None
    ) -> None:
        if pace is None:
            signal = quotes.eval("(high + low + close) / 3").values
            pace = 1 / (2 * np.correlate(signal, signal, 'valid'))
        self.pace = pace

        super().__init__(quotes, num_periods, deviations, long_periods)

    def _construct_bands(self, quotes: pd.DataFrame) -> pd.DataFrame:
        # Standard Bolling Bands Algorithm
        quotes['TP'] = quotes.eval("(high + low + close) / 3")
        
        entry = quotes['TP'].shift().values
        entry[0] = quotes['open'].values[0]
        reference = quotes['TP'].values
        
        lms_estimate, _ = lms(entry, reference, self.num_periods, self.pace)

        quotes['band_center'] = lms_estimate
        quotes['std_dev'] = quotes['TP'].rolling(self.num_periods).std()

        quotes['band_upper'] = quotes['band_center'] + self.deviations * quotes['std_dev']
        quotes['band_lower'] = quotes['band_center'] - self.deviations * quotes['std_dev']

        # Long term rolling standard deviation, used to evaluate "consolidation periods".
        quotes['long_term_std'] = quotes['TP'].rolling(self.long_periods).std()

        return quotes