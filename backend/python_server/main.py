"""
FastAPI wrapper around scheduler.solvers.
POST /api/solver/solve
  body: { algorithm: 'csp'|'sa'|'ga', mode: 'finals'|'regular', sa_iters?, ga_pop?, ga_gens? }

The service reads users and finals from MongoDB (env var MONGO_URI must be set).
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List
from dotenv import load_dotenv
import os
from pymongo import MongoClient
from datetime import datetime

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI')
if not MONGO_URI:
    # allow fallback to DATABASE_URL
    MONGO_URI = os.getenv('DATABASE_URL')
if not MONGO_URI:
    raise RuntimeError('MONGO_URI not set in environment (.env)')

client = MongoClient(MONGO_URI)
# attempt to get default DB name from URI; fall back to 'test'
try:
    db = client.get_default_database()
except Exception:
    db = client.get_database()

users_col = db.get_collection('users')
finals_col = db.get_collection('finals')
shifts_col = db.get_collection('shifts')

from algorithms.csp_algo import CSPAlgorithm
from algorithms.sa_algo import SAAlgorithm
from algorithms.ga_algo import GAAlgorithm

app = FastAPI(title='IT Scheduler Python Backend')

class SolveRequest(BaseModel):
    algorithm: str = 'csp'
    mode: str = 'finals'
    sa_iters: int = 2000
    ga_pop: int = 30
    ga_gens: int = 200


def load_users_from_db() -> List[Dict]:
    docs = list(users_col.find({}))
    users = []
    for d in docs:
        u = {
            '_id': str(d.get('_id')),
            'name': d.get('name'),
            'position': d.get('position'),
            'isCommuter': bool(d.get('isCommuter', False)),
            'isActive': bool(d.get('isActive', True)),
            'desiredHours': float(d.get('desiredHours', 15)),
            'busy_times': d.get('busy_times', {}),
            'exam_times': []
        }
        users.append(u)
    return users


def load_finals_from_db() -> List[Dict]:
    docs = list(finals_col.find({}))
    finals = []
    for f in docs:
        date_val = f.get('date')
        if isinstance(date_val, datetime):
            date_str = date_val.strftime('%Y-%m-%d')
        else:
            date_str = str(date_val)
        finals.append({
            'userId': str(f.get('userId')),
            'date': date_str,
            'startTime': f.get('startTime'),
            'endTime': f.get('endTime')
        })
    return finals


def attach_exam_times(users: List[Dict], finals: List[Dict]) -> List[Dict]:
    by_user: Dict[str, List[List[str]]] = {}
    for f in finals:
        uid = f.get('userId')
        by_user.setdefault(uid, []).append([f.get('date'), f.get('startTime'), f.get('endTime')])
    for u in users:
        u['exam_times'] = by_user.get(u['_id'], [])
    return users


def generate_slots(mode: str='finals') -> List[Dict]:
    DAY_SLICES = {
      '2025-05-12': [['07:30','11:00'], ['11:30','15:30'], ['15:30','19:30']],
      '2025-05-13': [['07:30','11:00'], ['11:30','15:30'], ['15:30','19:30']],
      '2025-05-14': [['07:30','11:00'], ['11:30','15:30'], ['15:30','19:30']],
      '2025-05-15': [['07:30','11:00'], ['11:30','15:30'], ['15:30','19:30']],
      '2025-05-16': [['07:30','11:00'], ['11:30','15:30'], ['15:30','17:00']],
    }
    if mode == 'regular':
        DAY_SLICES['2025-05-17'] = [['10:00','14:00'], ['14:30','18:00']]

    slots: List[Dict] = []
    for date, ranges in DAY_SLICES.items():
        try:
            day_name = datetime.fromisoformat(date).strftime('%A')
        except Exception:
            day_name = ''
        for (s,e) in ranges:
            slots.append({'date': date, 'day_name': day_name, 'start_time': s, 'end_time': e, 'shift_type': 'Window'})
            slots.append({'date': date, 'day_name': day_name, 'start_time': s, 'end_time': e, 'shift_type': 'Remote'})
    return slots


@app.post('/api/solver/solve')
def solve(req: SolveRequest):
    algorithm = req.algorithm.lower()
    mode = req.mode.lower()

    users = load_users_from_db()
    finals = load_finals_from_db()
    users = attach_exam_times(users, finals)
    slots = generate_slots(mode)

    if algorithm == 'csp':
        algo = CSPAlgorithm(users, slots)
    elif algorithm == 'sa':
        algo = SAAlgorithm(users, slots)
    elif algorithm == 'ga':
        algo = GAAlgorithm(users, slots)
    else:
        raise HTTPException(status_code=400, detail='Unknown algorithm; use csp|sa|ga')

    algo.configure(sa_iters=req.sa_iters, ga_pop=req.ga_pop, ga_gens=req.ga_gens)
    res = algo.solve()

    return { 'algorithm': algorithm, 'mode': mode, 'result': res }
