from fastapi import FastAPI
from pydantic import BaseModel
from classifier import classify_email

app = FastAPI()

class EmailRequest(BaseModel):
    email_body: str

class ClassificationResponse(BaseModel):
    classification: str

@app.post("/classify-email", response_model = ClassificationResponse)
async def classify_email_endpoint(request: EmailRequest):
    classification = classify_email(request.email_body)
    return ClassificationResponse(classification = classification)

# To run the FastAPI application, use the command:
# uvicorn main:app --reload