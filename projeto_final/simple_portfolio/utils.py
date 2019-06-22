from typing import List
from uuid import uuid4

import pandas as pd


def process_profitchart_data(df: pd.DataFrame) -> pd.DataFrame:
    """Process data from BR Profit Chart format to OHLC format."""
    _df = df.copy()

    _df['datetime'] = _df['Data'] + ' ' + _df['Hora']
    _df['datetime'] = pd.to_datetime(_df['datetime'], format='%d/%m/%Y %H:%M:%S').values

    _df.index = pd.MultiIndex.from_frame(_df[['datetime', 'Ativo']], names=['datetime', 'asset'])

    _df = _df.drop(['Data', 'Hora', 'datetime', 'Ativo'], axis=1)

    _df = _df.rename(columns={
        'Abertura': 'open',
        'Máximo': 'high',
        'Mínimo': 'low',
        'Fechamento': 'close',
        'Volume': 'volume',
        'Quantidade': 'quantity'
    })

    _df = _df.applymap(lambda value: value.replace('.', '').replace(',', '.')).astype(float)
    _df['quantity'] = _df['quantity'].astype(int)
    _df = _df.sort_index()

    return _df


def generate_id(existing_ids: List[str]) -> str:
    collision = True

    while collision:
        new_id = uuid4().hex
        collision = new_id in existing_ids

    return new_id
