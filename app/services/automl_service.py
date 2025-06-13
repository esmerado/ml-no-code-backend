import pickle

import pandas as pd
from flaml import AutoML
from sklearn.model_selection import train_test_split

from app.utils.models_utils import infer_task_type
from app.utils.reports_utils import generate_prediction_report
from app.utils.s3_utils import download_file_from_s3, upload_file_to_s3


def train_from_s3(user_id: str, model_id: str, s3_dataset_path: str, target_column: str, s3_model_output_path: str):
    local_csv_path = f"/tmp/{model_id}.csv"
    download_file_from_s3(s3_dataset_path, local_csv_path)

    df = pd.read_csv(local_csv_path)
    X = df.drop(columns=[target_column])
    y = df[target_column]

    # Dividir dataset
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    # AutoML con FLAML
    automl = AutoML()
    task_type = infer_task_type(y)

    automl_settings = {
        "time_budget": 120,
        "metric": "accuracy" if task_type == "classification" else "rmse",
        "task": task_type,
        "log_file_name": f"/tmp/flaml_{model_id}.log",
    }

    automl.fit(X_train=X_train, y_train=y_train, **automl_settings)

    y_pred = automl.predict(X_test)

    df_test, metrics = generate_prediction_report(automl, X_test, y_test, problem_type=task_type)

    # Guardar df_test como CSV local
    local_test_name = f"df_test_{model_id}.csv"
    local_test_path = f"/tmp/{local_test_name}"
    df_test.to_csv(local_test_path, index=False)

    # Subir df_test a S3
    with open(local_test_path, "rb") as f:
        df_test_bytes = f.read()

    data_output_path = f"{s3_model_output_path}/{local_test_name}"
    test_filename = data_output_path.split("/")[-1]
    test_folder = "/".join(data_output_path.split("/")[:-1])
    print(f"Subiendo df_test a S3: {data_output_path}")
    upload_file_to_s3(df_test_bytes, test_filename, test_folder)

    local_model_path = f"/tmp/{model_id}.pkl"
    with open(local_model_path, "wb") as f:
        pickle.dump(automl, f)

    # Subir modelo a S3
    with open(local_model_path, "rb") as f:
        file_bytes = f.read()

    model_output_path = f"{s3_model_output_path}/{model_id}.pkl"

    filename = model_output_path.split("/")[-1]
    folder = "/".join(model_output_path.split("/")[:-1])

    upload_file_to_s3(file_bytes, filename, folder)
    # TODO: Revisar si devolver el df_test es lo correcto o debería tratarlo para que devuelva también el rmse.
    return model_id, task_type, metrics, df_test, model_output_path, data_output_path


def predict_from_s3(model_id: str, model_s3_path: str, input_data_s3_path: str):
    local_model_path = f"/tmp/{model_id}.pkl"

    download_file_from_s3(model_s3_path, local_model_path)

    with open(local_model_path, "rb") as f:
        model = pickle.load(f)

    local_input_path = f"/tmp/{model_id}.csv"
    download_file_from_s3(input_data_s3_path, local_input_path)

    df = pd.read_csv(local_input_path)

    predictions = model.predict(df)

    df_result = df.copy()
    df_result["Prediction"] = predictions
    df_result = df_result.replace([float('inf'), float('-inf')], None).where(pd.notnull(df_result), None)

    return df_result.to_dict(orient="records")
