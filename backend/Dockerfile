FROM python:3.14-slim
WORKDIR /app

# Install dependencies
COPY backend ./backend
COPY ./backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip --break-system-packages && \
   pip install --no-cache-dir -r requirements.txt && \
   useradd --create-home appuser

USER appuser

# Copy code
COPY . .

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
