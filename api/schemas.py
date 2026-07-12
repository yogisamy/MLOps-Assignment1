from pydantic import BaseModel, Field


class PatientFeatures(BaseModel):
    age: float = Field(..., description="Age in years")
    sex: float = Field(..., description="1=male, 0=female")
    cp: float = Field(..., description="Chest pain type (0-3)")
    trestbps: float = Field(..., description="Resting blood pressure (mmHg)")
    chol: float = Field(..., description="Serum cholesterol (mg/dl)")
    fbs: float = Field(..., description="Fasting blood sugar > 120 mg/dl (1=true)")
    restecg: float = Field(..., description="Resting ECG results (0-2)")
    thalach: float = Field(..., description="Maximum heart rate achieved")
    exang: float = Field(..., description="Exercise induced angina (1=yes)")
    oldpeak: float = Field(..., description="ST depression induced by exercise")
    slope: float = Field(..., description="Slope of peak exercise ST segment (0-2)")
    ca: float = Field(..., description="Number of major vessels (0-3)")
    thal: float = Field(..., description="Thalassemia (1=normal, 2=fixed defect, 3=reversable)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "age": 63, "sex": 1, "cp": 3, "trestbps": 145,
                "chol": 233, "fbs": 1, "restecg": 0, "thalach": 150,
                "exang": 0, "oldpeak": 2.3, "slope": 0, "ca": 0, "thal": 1,
            }
        }
    }


class PredictionResponse(BaseModel):
    prediction: int
    label: str
    confidence: float
