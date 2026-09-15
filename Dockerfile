FROM python:3.12-slim

RUN useradd --create-home --shell /bin/bash app
WORKDIR /home/app/llm_eval

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chown -R app:app /home/app/llm_eval

USER app

CMD ["python", "main.py", "--help"]
