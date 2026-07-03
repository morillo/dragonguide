# DragonGuide — deployability concept.
FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -e .

# Default to offline/fixture mode so the container runs with no keys.
ENV DRAGONGUIDE_OFFLINE=1
EXPOSE 7860

CMD ["python", "app.py"]
