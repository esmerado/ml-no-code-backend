import numpy as np
import pandas as pd
from pycaret.classification import predict_model as predict_model_classification
from pycaret.classification import setup as setup_classification, compare_models as compare_models_classification, \
    pull as pull_classification
from pycaret.regression import predict_model as predict_model_regression
from pycaret.regression import setup as setup_regression, compare_models as compare_models_regression, \
    pull as pull_regression


async def machine_learning_model(
        df: pd.DataFrame,
        target: str,
):
    # Validación de la columna objetivo
    if target not in df.columns:
        raise ValueError(f"La columna objetivo '{target}' no existe en el dataset.")

    # Comprobación de que no tenga valores nulos
    missing_before = df.isnull().sum().sum()
    if missing_before > 0:
        print(f"⚠️ Se encontraron {missing_before} valores nulos. Rellenando con la mediana/moda...")
        for col in df.columns:
            if df[col].isnull().any():
                if df[col].dtype in [np.float64, np.int64]:
                    df[col].fillna(df[col].median(), inplace=True)
                else:
                    df[col].fillna(df[col].mode()[0], inplace=True)

    # Comprobación de si es regresión o clasificación
    if df[target].nunique() <= 20 or df[target].dtype == 'object':
        problem_type = 'classification'
    else:
        problem_type = 'regression'

    # Setup y entrenamiento
    if problem_type == 'classification':
        setup_classification(data=df,
                             target=target,
                             session_id=42,
                             normalize=True,
                             feature_selection=False,
                             pca=False,
                             fold_strategy="kfold",
                             fold=3, )
        best_model = compare_models_classification()
        results = pull_classification()
        predictions = predict_model_classification(best_model, data=df)
    else:
        df[target] = df[target].astype(float)
        try:
            setup_regression(
                data=df,
                target=target,
                session_id=42,
                normalize=True,
                feature_selection=False,
                pca=False,
                fold_strategy="kfold",
                fold=3,
            )
        except Exception as e:
            print(f"❌ Error en setup_regression: {e}")
            raise
        best_model = compare_models_regression()
        results = pull_regression()
        predictions = predict_model_regression(best_model, data=df)

    # Preparamos los resultados
    if 'Label' in predictions.columns and target in predictions.columns:
        prediction_sample = predictions[['Label', target]].head(10).to_dict(orient="records")
    else:
        prediction_sample = predictions.head(10).to_dict(orient="records")

    return {
        "problem_type": problem_type,
        "model_name": str(best_model),
        "metrics": results.to_dict(orient="records"),
        "prediction_sample": prediction_sample,
        "best_model": best_model,
    }
