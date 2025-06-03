import numpy as np
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, mean_absolute_error, \
    mean_squared_error, r2_score


def generate_prediction_report(model, X_test, y_test, problem_type="classification"):
    y_pred = model.predict(X_test)

    # Crear DataFrame con predicciones y valores reales
    df_test = X_test.copy()
    df_test["Real Value"] = y_test
    df_test["Predicted Value"] = y_pred

    if problem_type == "classification":
        df_test["Error %"] = (df_test["Real Value"] != df_test["Predicted Value"]).astype(int) * 100
        metrics = {
            "accuracy": accuracy_score(y_test, y_pred),
            "f1_score": f1_score(y_test, y_pred, average="weighted"),
            "precision": precision_score(y_test, y_pred, average="weighted"),
            "recall": recall_score(y_test, y_pred, average="weighted"),
        }

    elif problem_type == "regression":
        df_test["Error %"] = (
                                     np.abs(df_test["Real Value"] - df_test["Predicted Value"]) / (
                                         np.abs(df_test["Real Value"]) + 1e-8)
                             ) * 100
        metrics = {
            "mae": mean_absolute_error(y_test, y_pred),
            "mse": mean_squared_error(y_test, y_pred),
            "r2": r2_score(y_test, y_pred)
        }

    else:
        raise ValueError("Unsupported problem_type: choose 'classification' or 'regression'")

    return df_test, metrics
