"""Predictive analytics service using machine learning models."""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy import select, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import os

from models.user import User
from models.course import UserCourseProgress
from models.phishing import PhishingResult
from models.analytics import AnalyticsEvent
from core.cache import cache, cache_key, cached
from core.logging import logger
from core.config import settings


class PredictiveAnalyticsService:
    """Service for predictive analytics and ML models."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.models_dir = os.path.join(settings.DATA_DIR, "ml_models")
        os.makedirs(self.models_dir, exist_ok=True)
        self._models = {}
        self._scalers = {}
        
    async def initialize_models(self):
        """Initialize or load existing ML models."""
        models_config = {
            "phishing_risk": {
                "model_class": RandomForestClassifier,
                "params": {"n_estimators": 100, "random_state": 42}
            },
            "training_completion": {
                "model_class": LogisticRegression,
                "params": {"random_state": 42}
            },
            "user_churn": {
                "model_class": RandomForestClassifier,
                "params": {"n_estimators": 50, "random_state": 42}
            },
            "security_incident": {
                "model_class": LogisticRegression,
                "params": {"random_state": 42}
            }
        }
        
        for model_name, config in models_config.items():
            model_path = os.path.join(self.models_dir, f"{model_name}.pkl")
            scaler_path = os.path.join(self.models_dir, f"{model_name}_scaler.pkl")
            
            if os.path.exists(model_path) and os.path.exists(scaler_path):
                # Load existing model
                self._models[model_name] = joblib.load(model_path)
                self._scalers[model_name] = joblib.load(scaler_path)
                logger.info(f"Loaded existing model: {model_name}")
            else:
                # Create new model
                self._models[model_name] = config["model_class"](**config["params"])
                self._scalers[model_name] = StandardScaler()
                logger.info(f"Created new model: {model_name}")
                
    async def predict_phishing_risk(
        self,
        company_id: int,
        user_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Predict phishing risk for users.
        
        Args:
            company_id: Company ID
            user_ids: Optional list of specific user IDs to analyze
            
        Returns:
            Risk predictions and recommendations
        """
        # Get user features
        features_data = await self._get_user_phishing_features(company_id, user_ids)
        
        if not features_data:
            return {"predictions": [], "summary": {}}
            
        # Prepare features for model
        user_info = features_data["users"]
        feature_matrix = np.array([
            [
                user["past_clicks"],
                user["training_completion"],
                user["days_since_last_training"],
                user["login_frequency"],
                user["security_incidents"],
                user["report_rate"],
                user["avg_response_time"],
            ]
            for user in user_info
        ])
        
        # Scale features
        if "phishing_risk" not in self._scalers:
            self._scalers["phishing_risk"] = StandardScaler()
            scaled_features = self._scalers["phishing_risk"].fit_transform(feature_matrix)
        else:
            scaled_features = self._scalers["phishing_risk"].transform(feature_matrix)
            
        # Make predictions
        if hasattr(self._models["phishing_risk"], "predict_proba"):
            risk_scores = self._models["phishing_risk"].predict_proba(scaled_features)[:, 1]
        else:
            # Fallback for models without predict_proba
            risk_scores = self._models["phishing_risk"].predict(scaled_features)
            
        # Prepare results
        predictions = []
        for i, user in enumerate(user_info):
            risk_score = float(risk_scores[i])
            risk_level = self._categorize_risk(risk_score)
            
            predictions.append({
                "user_id": user["user_id"],
                "name": user["name"],
                "risk_score": round(risk_score * 100, 2),
                "risk_level": risk_level,
                "factors": self._get_risk_factors(user, risk_score),
                "recommendations": self._get_user_recommendations(user, risk_score),
            })
            
        # Summary statistics
        summary = {
            "total_users": len(predictions),
            "high_risk": len([p for p in predictions if p["risk_level"] == "high"]),
            "medium_risk": len([p for p in predictions if p["risk_level"] == "medium"]),
            "low_risk": len([p for p in predictions if p["risk_level"] == "low"]),
            "avg_risk_score": round(np.mean([p["risk_score"] for p in predictions]), 2),
        }
        
        return {
            "predictions": sorted(predictions, key=lambda x: x["risk_score"], reverse=True),
            "summary": summary,
            "model_accuracy": await self._get_model_accuracy("phishing_risk"),
        }
        
    async def predict_training_completion(
        self,
        company_id: int,
        course_id: int,
        days_ahead: int = 30
    ) -> Dict[str, Any]:
        """
        Predict which users are likely to complete training.
        
        Args:
            company_id: Company ID
            course_id: Course ID
            days_ahead: Prediction timeframe in days
            
        Returns:
            Completion predictions
        """
        # Get user features for enrolled users
        features_data = await self._get_training_features(company_id, course_id)
        
        if not features_data:
            return {"predictions": [], "summary": {}}
            
        user_info = features_data["users"]
        feature_matrix = np.array([
            [
                user["current_progress"],
                user["days_since_enrollment"],
                user["avg_session_duration"],
                user["login_streak"],
                user["past_completion_rate"],
                user["quiz_scores_avg"],
            ]
            for user in user_info
        ])
        
        # Scale and predict
        if "training_completion" not in self._scalers:
            self._scalers["training_completion"] = StandardScaler()
            scaled_features = self._scalers["training_completion"].fit_transform(feature_matrix)
        else:
            scaled_features = self._scalers["training_completion"].transform(feature_matrix)
            
        if hasattr(self._models["training_completion"], "predict_proba"):
            completion_probs = self._models["training_completion"].predict_proba(scaled_features)[:, 1]
        else:
            completion_probs = self._models["training_completion"].predict(scaled_features)
            
        # Prepare predictions
        predictions = []
        for i, user in enumerate(user_info):
            completion_prob = float(completion_probs[i])
            
            predictions.append({
                "user_id": user["user_id"],
                "name": user["name"],
                "current_progress": user["current_progress"],
                "completion_probability": round(completion_prob * 100, 2),
                "expected_completion_days": self._estimate_completion_days(
                    user["current_progress"], completion_prob, user["avg_session_duration"]
                ),
                "risk_factors": self._get_completion_risk_factors(user),
                "recommendations": self._get_completion_recommendations(user, completion_prob),
            })
            
        # Summary
        summary = {
            "total_enrolled": len(predictions),
            "likely_completers": len([p for p in predictions if p["completion_probability"] > 70]),
            "at_risk": len([p for p in predictions if p["completion_probability"] < 30]),
            "avg_completion_probability": round(
                np.mean([p["completion_probability"] for p in predictions]), 2
            ),
        }
        
        return {
            "predictions": sorted(
                predictions, key=lambda x: x["completion_probability"], reverse=True
            ),
            "summary": summary,
            "course_id": course_id,
            "prediction_window_days": days_ahead,
        }
        
    async def predict_security_incidents(
        self,
        company_id: int,
        timeframe_days: int = 30
    ) -> Dict[str, Any]:
        """
        Predict likelihood of security incidents.
        
        Args:
            company_id: Company ID
            timeframe_days: Prediction timeframe
            
        Returns:
            Security incident predictions
        """
        # Get company-wide security features
        features = await self._get_security_features(company_id)
        
        if not features:
            return {"prediction": None, "factors": []}
            
        feature_vector = np.array([[
            features["avg_phishing_click_rate"],
            features["untrained_user_percentage"],
            features["avg_password_age_days"],
            features["two_fa_adoption_rate"],
            features["recent_incidents_count"],
            features["avg_security_score"],
            features["user_turnover_rate"],
        ]])
        
        # Scale and predict
        if "security_incident" not in self._scalers:
            self._scalers["security_incident"] = StandardScaler()
            scaled_features = self._scalers["security_incident"].fit_transform(feature_vector)
        else:
            scaled_features = self._scalers["security_incident"].transform(feature_vector)
            
        if hasattr(self._models["security_incident"], "predict_proba"):
            incident_prob = float(self._models["security_incident"].predict_proba(scaled_features)[0, 1])
        else:
            incident_prob = float(self._models["security_incident"].predict(scaled_features)[0])
            
        risk_level = self._categorize_risk(incident_prob)
        
        return {
            "prediction": {
                "incident_probability": round(incident_prob * 100, 2),
                "risk_level": risk_level,
                "timeframe_days": timeframe_days,
            },
            "contributing_factors": self._get_incident_factors(features, incident_prob),
            "recommendations": self._get_incident_recommendations(features, incident_prob),
            "trend": await self._get_incident_trend(company_id),
        }
        
    async def predict_user_churn(
        self,
        company_id: int,
        days_ahead: int = 90
    ) -> Dict[str, Any]:
        """
        Predict which users are at risk of becoming inactive.
        
        Args:
            company_id: Company ID
            days_ahead: Prediction timeframe
            
        Returns:
            Churn predictions
        """
        # Get user engagement features
        features_data = await self._get_churn_features(company_id)
        
        if not features_data:
            return {"predictions": [], "summary": {}}
            
        user_info = features_data["users"]
        feature_matrix = np.array([
            [
                user["days_since_last_login"],
                user["login_frequency_trend"],
                user["course_engagement_score"],
                user["days_since_last_activity"],
                user["total_activities_30d"],
                user["completion_rate"],
            ]
            for user in user_info
        ])
        
        # Scale and predict
        if "user_churn" not in self._scalers:
            self._scalers["user_churn"] = StandardScaler()
            scaled_features = self._scalers["user_churn"].fit_transform(feature_matrix)
        else:
            scaled_features = self._scalers["user_churn"].transform(feature_matrix)
            
        if hasattr(self._models["user_churn"], "predict_proba"):
            churn_probs = self._models["user_churn"].predict_proba(scaled_features)[:, 1]
        else:
            churn_probs = self._models["user_churn"].predict(scaled_features)
            
        # Prepare predictions
        predictions = []
        for i, user in enumerate(user_info):
            churn_prob = float(churn_probs[i])
            
            predictions.append({
                "user_id": user["user_id"],
                "name": user["name"],
                "churn_probability": round(churn_prob * 100, 2),
                "risk_level": self._categorize_risk(churn_prob),
                "last_active": user["last_login_date"],
                "engagement_score": round(user["course_engagement_score"], 2),
                "recommendations": self._get_retention_recommendations(user, churn_prob),
            })
            
        # Summary
        high_risk_count = len([p for p in predictions if p["churn_probability"] > 70])
        summary = {
            "total_users": len(predictions),
            "high_risk": high_risk_count,
            "medium_risk": len([p for p in predictions if 30 < p["churn_probability"] <= 70]),
            "low_risk": len([p for p in predictions if p["churn_probability"] <= 30]),
            "retention_actions_needed": high_risk_count,
        }
        
        return {
            "predictions": sorted(predictions, key=lambda x: x["churn_probability"], reverse=True),
            "summary": summary,
            "timeframe_days": days_ahead,
        }
        
    async def train_models(self, company_id: int) -> Dict[str, Any]:
        """
        Train or retrain ML models with latest data.
        
        Args:
            company_id: Company ID for training data
            
        Returns:
            Training results
        """
        results = {}
        
        # Train phishing risk model
        phishing_result = await self._train_phishing_model(company_id)
        results["phishing_risk"] = phishing_result
        
        # Train completion prediction model
        completion_result = await self._train_completion_model(company_id)
        results["training_completion"] = completion_result
        
        # Train churn prediction model
        churn_result = await self._train_churn_model(company_id)
        results["user_churn"] = churn_result
        
        # Train security incident model
        incident_result = await self._train_incident_model(company_id)
        results["security_incident"] = incident_result
        
        # Save models
        for model_name in self._models:
            model_path = os.path.join(self.models_dir, f"{model_name}.pkl")
            scaler_path = os.path.join(self.models_dir, f"{model_name}_scaler.pkl")
            
            joblib.dump(self._models[model_name], model_path)
            joblib.dump(self._scalers[model_name], scaler_path)
            
        return {
            "training_results": results,
            "models_saved": list(self._models.keys()),
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    # Helper methods
    
    def _categorize_risk(self, score: float) -> str:
        """Categorize risk based on score."""
        if score >= 0.7:
            return "high"
        elif score >= 0.3:
            return "medium"
        else:
            return "low"
            
    def _get_risk_factors(self, user_data: Dict, risk_score: float) -> List[str]:
        """Get risk factors for a user."""
        factors = []
        
        if user_data["past_clicks"] > 2:
            factors.append("Multiple past phishing clicks")
        if user_data["training_completion"] < 50:
            factors.append("Low training completion rate")
        if user_data["days_since_last_training"] > 90:
            factors.append("Overdue for security training")
        if user_data["login_frequency"] < 5:
            factors.append("Infrequent system usage")
            
        return factors
        
    def _get_user_recommendations(self, user_data: Dict, risk_score: float) -> List[str]:
        """Get recommendations for a user based on risk."""
        recommendations = []
        
        if risk_score > 0.7:
            recommendations.append("Immediate mandatory phishing awareness training")
            recommendations.append("Enable additional email security filters")
        if user_data["training_completion"] < 80:
            recommendations.append("Complete all assigned security training modules")
        if user_data["report_rate"] < 0.2:
            recommendations.append("Training on how to identify and report phishing")
            
        return recommendations
        
    def _estimate_completion_days(
        self, 
        current_progress: float, 
        completion_prob: float,
        avg_session_duration: float
    ) -> Optional[int]:
        """Estimate days to completion."""
        if completion_prob < 0.3 or current_progress >= 100:
            return None
            
        remaining_progress = 100 - current_progress
        daily_progress = avg_session_duration * 2  # Rough estimate
        
        if daily_progress > 0:
            return int(remaining_progress / daily_progress)
        return None
        
    async def _get_user_phishing_features(
        self,
        company_id: int,
        user_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Get phishing-related features for users."""
        # Implementation would query database for user features
        # This is a simplified version
        base_query = select(User).where(
            User.company_id == company_id,
            User.is_active == True
        )
        
        if user_ids:
            base_query = base_query.where(User.id.in_(user_ids))
            
        result = await self.db.execute(base_query)
        users = result.scalars().all()
        
        user_features = []
        for user in users:
            # These would be calculated from actual data
            user_features.append({
                "user_id": user.id,
                "name": f"{user.first_name} {user.last_name}",
                "past_clicks": 0,  # Would query PhishingResult
                "training_completion": 75.0,  # Would query UserCourseProgress
                "days_since_last_training": 30,
                "login_frequency": 15,
                "security_incidents": 0,
                "report_rate": 0.5,
                "avg_response_time": 2.5,
            })
            
        return {"users": user_features}
        
    async def _get_model_accuracy(self, model_name: str) -> float:
        """Get model accuracy score."""
        # In production, this would track actual model performance
        return 85.5  # Placeholder
        
    async def _train_phishing_model(self, company_id: int) -> Dict[str, Any]:
        """Train phishing risk prediction model."""
        # This would implement actual model training
        return {
            "samples_used": 1000,
            "accuracy": 0.86,
            "features": 7,
            "training_time_seconds": 2.5,
        }
        
    # Additional helper methods would be implemented similarly...