.PHONY: backend frontend

backend:
	. venv/bin/activate && uvicorn backend.main:app --reload

frontend:
	npm run dev
