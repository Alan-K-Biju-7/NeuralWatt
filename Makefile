.PHONY: demo-up demo-down seed-demo test-backend

demo-up:
	docker compose up --build mongo backend frontend simulator

demo-down:
	docker compose down

seed-demo:
	python3 scripts/seed_energy_readings.py --days 30 --anomaly-probability 0.03

test-backend:
	cd backend && pytest
