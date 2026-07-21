FROM python:3.14-slim
WORKDIR /backend

# Install dependencies
COPY requirements.txt /backend/.
RUN pip install --no-cache-dir --upgrade pip --break-system-packages && \
   pip install --no-cache-dir -r requirements.txt && \
   useradd --create-home appuser

USER appuser

# Copy code
COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
