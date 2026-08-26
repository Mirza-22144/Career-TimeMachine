# Career TimeMachine

Helping experienced women in tech return from a career break without starting from scratch.

## The problem

Women in Australia's tech sector face compounded disadvantages during and after maternity leave —
not because they've lost their skills, but because of uncertainty about what's changed while they
were away, and a lack of low-friction ways to rebuild confidence before returning to work.

## The idea

Rather than another generic skills-gap finder or course recommender, Career TimeMachine helps a
returning professional answer three specific questions:

1. **What actually changed** in the Australian tech industry while I was away?
2. **Which of my existing skills still transfer?**
3. **Can I practise working in that changed environment before I return?**

## Reducing User's hurdle

No login required. No generic course list.

## Setup

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Runs at `http://localhost:8000` — check `http://localhost:8000/health`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Runs at `http://localhost:5173`.

### Database

## Iteration

Iteration 1
