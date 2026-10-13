# Headless image for direct Google Slides links only.
# LMS page URLs (Canvas, Moodle, ...) need a visible browser to sign in, so they
# do not work in Docker; run the tool natively for those.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install . \
 && playwright install --with-deps chromium

WORKDIR /output
ENTRYPOINT ["slides-dl", "--browser", "chromium"]
