from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split


class RandomForestTrainer:
    def train(self):
        print("Entrenando modelo RandomForestClassifier")
        X, y = load_iris(return_X_y=True)
        feature_names = load_iris().feature_names
        target_names = load_iris().target_names.tolist()

        print("X shape:", X.shape)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        print("X_train shape:", X_train.shape)
        # Entrenar modelo
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        print("Modelo entrenado")
        # Predicciones
        y_pred = model.predict(X_test)

        print("Predicciones realizadas")
        # Evaluación
        acc = accuracy_score(y_test, y_pred)
        cm = confusion_matrix(y_test, y_pred).tolist()  # Convertir a lista JSON
        feature_importances = model.feature_importances_.tolist()

        print("Evaluación completada")
        # Enviar respuesta JSON al frontend
        return {
            "accuracy": acc,
            "confusion_matrix": cm,
            "feature_importance": {
                "features": feature_names,
                "values": feature_importances
            },
            "target_names": target_names,
            "epochs": 10,  # Example value
            "accuracy_values": [acc],  # Example value
            "loss_values": [0.1]  # Example value
        }
