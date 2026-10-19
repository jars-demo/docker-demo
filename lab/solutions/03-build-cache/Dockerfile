FROM python:3.13.16-slim-trixie
WORKDIR /app
# Dependencies change rarely, so they come first: this layer stays cached until
# requirements.txt itself changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Code changes on every commit, so it comes last.
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
