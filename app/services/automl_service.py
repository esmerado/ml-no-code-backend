import pickle
import uuid

import pandas as pd
from flaml import AutoML
from sklearn.model_selection import train_test_split

from app.utils.reports_utils import generate_prediction_report
from app.utils.s3_upload import download_file_from_s3, upload_file_to_s3


def train_from_s3(user_id: str, s3_dataset_path: str, target_column: str, s3_model_output_path: str):
    local_csv_path = f"/tmp/{uuid.uuid4()}.csv"
    download_file_from_s3(s3_dataset_path, local_csv_path)

    df = pd.read_csv(local_csv_path)
    print("✅ CSV file loaded successfully")
    X = df.drop(columns=[target_column])
    print("✅ Features separated from target column")
    y = df[target_column]

    print("✅ Data loaded and target column separated")
    # Dividir dataset
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    print("✅ Dataset split into train and test sets")
    # AutoML con FLAML
    automl = AutoML()
    automl_settings = {
        "time_budget": 120,  # segundos
        "metric": "accuracy",
        "task": "classification",
        "log_file_name": f"/tmp/flaml_{uuid.uuid4()}.log",
    }

    print("✅ AutoML settings configured")
    automl.fit(X_train=X_train, y_train=y_train, **automl_settings)

    y_pred = automl.predict(X_test)

    df_test, metrics = generate_prediction_report(automl, X_test, y_test, problem_type="classification")

    # Guardar modelo
    model_id = str(uuid.uuid4())
    print("✅ Entrenamiento completo, modelo listo para guardar.")
    print("✅ Entrenamiento completo, modelo listo para guardar.")
    local_model_path = f"/tmp/{model_id}.pkl"
    with open(local_model_path, "wb") as f:
        pickle.dump(automl, f)
    print(f"💾 Modelo guardado en {local_model_path}")

    # Subir modelo a S3
    with open(local_model_path, "rb") as f:
        file_bytes = f.read()

    output_path = f"{s3_model_output_path}/{model_id}.pkl"
    # Extrae filename del output_model_s3_path
    filename = output_path.split("/")[-1]
    folder = "/".join(output_path.split("/")[:-1])
    print(f"📂 Carpeta de destino: {folder}, Nombre del archivo: {filename}")

    upload_file_to_s3(file_bytes, filename, folder)
    return model_id, metrics, df_test


def predict_from_s3(model_s3_path: str, input_data_s3_path: str):
    # 1. Descargar modelo
    local_model_path = f"/tmp/{uuid.uuid4()}.pkl"
    download_file_from_s3(model_s3_path, local_model_path)

    with open(local_model_path, "rb") as f:
        model = pickle.load(f)

    # 2. Descargar dataset de entrada
    local_input_path = f"/tmp/{uuid.uuid4()}.csv"
    download_file_from_s3(input_data_s3_path, local_input_path)

    df = pd.read_csv(local_input_path)

    # 3. Predecir
    predictions = model.predict(df)

    # 4. Devolver resultados
    df_result = df.copy()
    df_result["Prediction"] = predictions
    df_result = df_result.replace([float('inf'), float('-inf')], None).where(pd.notnull(df_result), None)

    return df_result.to_dict(orient="records")
