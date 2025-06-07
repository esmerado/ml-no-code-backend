import pandas as pd


def infer_task_type(y: pd.Series) -> str:
    if y.dtype == 'object' or y.dtype.name == 'category':
        return 'classification'
    elif y.nunique() <= 20:
        return 'classification'
    else:
        return 'regression'
