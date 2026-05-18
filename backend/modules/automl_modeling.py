"""Automated Machine Learning Modeling module."""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, GradientBoostingRegressor, GradientBoostingClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score, f1_score
from typing import Dict, Any
import warnings
warnings.filterwarnings("ignore")

try:
    import xgboost as xgb
    HAS_XGB = True
except Exception:
    HAS_XGB = False

try:
    import lightgbm as lgb
    HAS_LGB = True
except Exception:
    HAS_LGB = False


class AutoMLModeling:
    def __init__(self):
        self.best_model = None
        self.best_model_name = ""
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_names = []

    def auto_build_model(self, df: pd.DataFrame, target_column: str,
                         problem_type: str = "auto") -> Dict[str, Any]:
        X, y = self._prepare_features(df, target_column)
        self.feature_names = list(X.columns)

        if problem_type == "auto":
            problem_type = self._detect_problem_type(y)

        # Split data
        stratify = y if problem_type == "classification" else None
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=stratify
        )

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Train models
        if problem_type == "regression":
            results = self._train_regression_models(X_train_scaled, X_test_scaled, y_train, y_test)
        else:
            results = self._train_classification_models(X_train_scaled, X_test_scaled, y_train, y_test)

        # Feature importance
        feature_importance = self._analyze_feature_importance()

        return {
            "problem_type": problem_type,
            "model_results": results,
            "best_model_name": self.best_model_name,
            "feature_importance": feature_importance,
            "test_size": len(y_test),
            "train_size": len(y_train),
        }

    def _prepare_features(self, df: pd.DataFrame, target_column: str):
        df = df.copy()
        y = df[target_column].copy()
        X = df.drop(columns=[target_column])

        # Encode categorical columns
        for col in X.select_dtypes(include=["object", "category"]).columns:
            le = LabelEncoder()
            X[col] = X[col].astype(str)
            mask = X[col].notna()
            X.loc[mask, col] = le.fit_transform(X.loc[mask, col])
            X[col] = X[col].fillna(-1)
            self.label_encoders[col] = le

        # Encode target if classification
        if y.dtype == object or y.dtype.name == "category":
            le = LabelEncoder()
            y = y.astype(str).fillna("missing")
            y = le.fit_transform(y)
            self.label_encoders[target_column] = le

        # Fill remaining NaN
        X = X.fillna(X.median(numeric_only=True))
        X = X.fillna(0)

        return X, y

    def _detect_problem_type(self, y) -> str:
        if y.dtype in (np.int64, np.int32):
            unique_ratio = len(np.unique(y)) / len(y)
            if unique_ratio < 0.05 and len(np.unique(y)) <= 20:
                return "classification"
        if y.dtype == object or y.dtype.name == "category":
            return "classification"
        return "regression"

    def _train_regression_models(self, X_train, X_test, y_train, y_test) -> Dict:
        models = {
            "LinearRegression": LinearRegression(),
            "RandomForest": RandomForestRegressor(n_estimators=100, random_state=42),
            "GradientBoosting": GradientBoostingRegressor(n_estimators=100, random_state=42),
        }
        if HAS_XGB:
            models["XGBoost"] = xgb.XGBRegressor(n_estimators=100, random_state=42, verbosity=0)
        if HAS_LGB:
            models["LightGBM"] = lgb.LGBMRegressor(n_estimators=100, random_state=42, verbose=-1)

        results = {}
        best_score = -np.inf
        for name, model in models.items():
            try:
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                r2 = float(r2_score(y_test, y_pred))
                rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
                cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring="r2")
                cv_mean = float(cv_scores.mean())
                cv_std = float(cv_scores.std())
                results[name] = {"r2_score": round(r2, 4), "rmse": round(rmse, 4),
                                 "cv_mean": round(cv_mean, 4), "cv_std": round(cv_std, 4)}
                if r2 > best_score:
                    best_score = r2
                    self.best_model = model
                    self.best_model_name = name
            except Exception as e:
                results[name] = {"error": str(e)}

        return results

    def _train_classification_models(self, X_train, X_test, y_train, y_test) -> Dict:
        models = {
            "LogisticRegression": LogisticRegression(max_iter=1000, random_state=42),
            "RandomForest": RandomForestClassifier(n_estimators=100, random_state=42),
            "GradientBoosting": GradientBoostingClassifier(n_estimators=100, random_state=42),
        }
        if HAS_XGB:
            models["XGBoost"] = xgb.XGBClassifier(n_estimators=100, random_state=42, verbosity=0)
        if HAS_LGB:
            models["LightGBM"] = lgb.LGBMClassifier(n_estimators=100, random_state=42, verbose=-1)

        results = {}
        best_score = -np.inf
        for name, model in models.items():
            try:
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                acc = float(accuracy_score(y_test, y_pred))
                f1 = float(f1_score(y_test, y_pred, average="weighted"))
                cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring="accuracy")
                cv_mean = float(cv_scores.mean())
                cv_std = float(cv_scores.std())
                results[name] = {"accuracy": round(acc, 4), "f1_score": round(f1, 4),
                                 "cv_mean": round(cv_mean, 4), "cv_std": round(cv_std, 4)}
                if acc > best_score:
                    best_score = acc
                    self.best_model = model
                    self.best_model_name = name
            except Exception as e:
                results[name] = {"error": str(e)}

        return results

    def _analyze_feature_importance(self) -> Dict[str, float]:
        if self.best_model is None or not self.feature_names:
            return {}
        if hasattr(self.best_model, "feature_importances_"):
            importances = self.best_model.feature_importances_
        elif hasattr(self.best_model, "coef_"):
            importances = np.abs(self.best_model.coef_).flatten()
        else:
            return {}

        n_features = min(len(self.feature_names), len(importances))
        return {self.feature_names[i]: round(float(importances[i]), 4) for i in range(n_features)}
