FROM python:3.11-bullseye

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    nano \
    tesseract-ocr-all \
    && apt-get autoremove \
    && rm -rf /var/lib/apt/lists/*
