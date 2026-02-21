from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
import json
from pathlib import Path
from datetime import date
from typing import Optional
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
import os
from .db import init_db

init_db()


app = FastAPI(title="WhoAmI API", version="0.1.0")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
ROLES_FILE = DATA_DIR / os.getenv("ROLES_FILE", "roles.json")
DAYS_FILE = DATA_DIR / os.getenv("DAYS_FILE", "days.json")

class Segment(BaseModel):
    roleId: int
    minutes: int = Field(ge=0, le=24*60)
    note: Optional[str] = None


class DayLog(BaseModel):
    userId: str
    day: str # "YYYY-MM-DD"
    sleepMinutes: int = Field(default=480, ge=0, le=24*60)
    bufferMinutes: int =Field(default=120, ge=0, le=24*60)
    segments: List[Segment] = Field (default_factory=list)

class Role(BaseModel):
    id: int
    name: str
    percent: int = Field(ge=0, le=100) # 0-100

def load_days() -> dict:
    if not DAYS_FILE.exists():
        return {}
    return json.loads(DAYS_FILE.read_text(encoding="utf-8"))

def save_days(data: dict) -> None:
     DAYS_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def today_str () -> str:
    return date.today().isoformat()

def calc_other_minutes(log: DayLog) -> int:
    total = 24*60
    used = log.sleepMinutes + log.bufferMinutes + sum(s.minutes for s in log.segments)
    return max(0, total - used)


def load_roles() -> list[Role]:
    if not ROLES_FILE.exists():
        return [
            Role(id=1, name="Devops", percent=25),
            Role(id=2, name="Father of the family", percent=35),
            Role(id=3, name="Sportsman", percent=20),
            Role(id=4, name="Master of the house", percent=15),
            Role(id=5, name="Other", percent=5),
        ]

    data = json.loads(ROLES_FILE.read_text(encoding="utf-8"))
    return [Role(**item) for item in data]


def save_roles(items: List[Role]) -> None:
    data = [r.model_dump() for r in items]
    ROLES_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


roles: List[Role] = load_roles()

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/roles", response_model=List[Role])
def list_roles():
    return roles


@app.post("/roles", response_model=Role)
def add_role(role: Role):
    if any(r.id == role.id for r in roles):
        raise HTTPException(status_code=409, detail="Role with this id already exists")

    roles.append(role)
    save_roles(roles)
    return role


@app.delete("/roles/{role_id}")
def delete_role(role_id: int):
    idx = next((i for i, r in enumerate(roles) if r.id == role_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Role not found")

    deleted = roles.pop(idx)
    save_roles(roles)
    return {"deleted": deleted.model_dump()}

@app.get("/today")
def get_today(userId: str):
    days = load_days()
    key = f"{userId}:{today_str()}"

    if key in days:
        log = DayLog(**days[key])
    else:
        log = DayLog(userId=userId, day=today_str())

    other = calc_other_minutes(log)
    total = 24 * 60

    def pct(mins: int) -> int:
        return round(mins * 100 / total)

    return {
        "log": log.model_dump(),
        "otherMinutes": other,
        "summaryPercent": {
            "sleep": pct(log.sleepMinutes),
            "buffer": pct(log.bufferMinutes),
            "tracked": pct(sum(s.minutes for s in log.segments)),
            "other": pct(other),
        }
    }

@app.post("/today/segment")
def add_segment(userId: str, seg: Segment):
    days = load_days()
    key = f"{userId}:{today_str()}"

    if key in days:
        log = DayLog(**days[key])
    else:
        log = DayLog(userId=userId, day=today_str())

    log.segments.append(seg)

    # Защита от "Переписать день"
    if calc_other_minutes(log) == 0 and (
        log.sleepMinutes + log.bufferMinutes +sum(s.minutes for s in log.segments)

    ) > 24 * 60:
        raise HTTPException(status_code=409, detail="Total minutes exceed 1440")

    days[key] = log.model_dump()
    save_days(days)
    return {"ok": True, "log": log.model_dump(), "otherMinutes": calc_other_minutes(log)}