FROM python:3.9-slim


RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*


RUN useradd -m appuser
USER appuser
WORKDIR /app


COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY --chown=appuser:appuser . .


EXPOSE 7860


CMD ["python", "app.py"]
