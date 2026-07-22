FROM python:3.14-slim
WORKDIR /app

# Install dependencies
COPY backend ./backend
COPY ./backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip --break-system-packages && \
   pip install --no-cache-dir -r requirements.txt

# Create appuser with the same UID as the host user (503)
RUN useradd -u 503 -m -s /bin/bash appuser

USER appuser

# Copy code
COPY . .

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
