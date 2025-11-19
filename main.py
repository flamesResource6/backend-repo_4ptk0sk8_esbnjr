import os
import time
from datetime import datetime, timedelta
from random import randint, random
from typing import List, Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Insights API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        from database import db

        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"

            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    # Check environment variables
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# ------------------------------
# Dashboard sample data endpoint
# ------------------------------

class KPI(BaseModel):
    label: str
    value: float
    delta: float
    icon: str
    format: str = "number"  # number | percent | currency


class TimeSeriesPoint(BaseModel):
    date: str
    users: int
    sessions: int


class FeatureUsage(BaseModel):
    name: str
    count: int


class TrafficSource(BaseModel):
    name: str
    value: int


class DashboardPayload(BaseModel):
    range: str
    kpis: List[KPI]
    series: List[TimeSeriesPoint]
    features: List[FeatureUsage]
    traffic: List[TrafficSource]
    recent: List[Dict[str, Any]]
    last_updated: str


def _gen_series(days: int = 30) -> List[Dict[str, int]]:
    base_users = 800
    base_sessions = 1200
    data = []
    for i in range(days):
        date = (datetime.utcnow() - timedelta(days=days - i)).strftime("%Y-%m-%d")
        u = int(base_users + (i * 7) + randint(-60, 60))
        s = int(base_sessions + (i * 10) + randint(-90, 90))
        data.append({"date": date, "users": max(0, u), "sessions": max(0, s)})
    return data


@app.get("/api/dashboard/sample", response_model=DashboardPayload)
def get_sample_dashboard(range: str = "Last 30 days"):
    kpis = [
        KPI(label="Total Users", value=23540, delta=+4.2, icon="Users", format="number"),
        KPI(label="Active Sessions", value=5821, delta=+2.1, icon="Activity", format="number"),
        KPI(label="Conversion Rate", value=7.8, delta=-0.6, icon="TrendingUp", format="percent"),
        KPI(label="MRR", value=48250, delta=+5.4, icon="CreditCard", format="currency"),
    ]

    series = _gen_series(30)

    features = [
        {"name": f"Feature {chr(65+i)}", "count": randint(120, 1400)} for i in range(10)
    ]

    traffic = [
        {"name": "Organic", "value": 5200},
        {"name": "Paid", "value": 2800},
        {"name": "Referral", "value": 1800},
        {"name": "Social", "value": 1400},
    ]

    recent = [
        {
            "name": f"User {i}",
            "email": f"user{i}@example.com",
            "date": (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d"),
            "source": ["Organic", "Paid", "Referral", "Social"][i % 4],
            "status": ["Activated", "Invited", "Pending", "Churn Risk"][i % 4],
        }
        for i in range(1, 13)
    ]

    payload = DashboardPayload(
        range=range,
        kpis=kpis,
        series=series,
        features=sorted(features, key=lambda x: x["count"], reverse=True),
        traffic=traffic,
        recent=recent,
        last_updated=datetime.utcnow().isoformat() + "Z",
    )
    return payload


# ------------------------------
# Chat placeholder endpoint
# ------------------------------

class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    source: str = "AI • Model v1"


@app.post("/api/chat/respond", response_model=ChatResponse)
def chat_respond(req: ChatRequest):
    # Simulate thinking time
    time.sleep(0.4)
    reply = (
        "Here is a sample answer. In a real app this would be generated by an AI model "
        "and could stream tokens to the client."
    )
    return ChatResponse(reply=reply)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
