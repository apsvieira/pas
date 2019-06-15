import pandas as pd


def process_profitchart_data(df):
    """Process data from BR Profit Chart format to OHLC format."""
    _df = df.copy()

    _df['datetime'] = _df['Data'] + ' ' + _df['Hora']
    _df.index = pd.to_datetime(_df['datetime'], format='%d/%m/%Y %H:%M:%S').values

    _df = _df.drop(['Data', 'Hora', 'datetime', 'Ativo', 'Quantidade'], axis=1)

    _df = _df.rename(columns={
        'Abertura': 'open',
        'Máximo': 'high',
        'Mínimo': 'low',
        'Fechamento': 'close',
        'Volume': 'volume',
    })

    _df = _df.applymap(lambda value: value.replace('.', '').replace(',', '.')).astype(float)
    _df = _df.sort_index()

    return _df
