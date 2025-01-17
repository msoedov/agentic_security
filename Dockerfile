FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x /app/agentic_security.py || true

EXPOSE 8718

# Run the initialization command first, then start the application
CMD ["sh", "-c", "python -m agentic_security i && python -m agentic_security s"]