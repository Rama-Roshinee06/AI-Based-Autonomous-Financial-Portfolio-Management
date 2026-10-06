"""Optional REST API:  uvicorn api.main:app --reload   (requires fastapi + uvicorn)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dataclasses import asdict
from fastapi import FastAPI, HTTPException
from data.fallback_data import SCENARIOS
from models.schemas import PortfolioState
from orchestration.orchestrator import Orchestrator

app = FastAPI(title="Multi-Agent AI Portfolio Management (SIMULATION)")
_orch = Orchestrator(PortfolioState(), use_live=True)


@app.get("/scenarios")
def scenarios():
    return SCENARIOS


@app.post("/analyse")
def analyse(symbol: str = "AAPL", scenario: str = None):
    try:
        r = _orch.analyse(symbol, scenario)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    out = asdict(r)
    out["notice"] = "SIMULATION - NO REAL TRADING. AI-generated simulated recommendation."
    return out


@app.get("/portfolio")
def portfolio():
    return _orch.portfolio.snapshot()
