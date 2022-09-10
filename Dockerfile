FROM python:3.10.7-bullseye

COPY ./ /app/

WORKDIR /app

RUN chmod +x bot.py

RUN pip install -r requirements.txt

CMD ["python", "bot.py"]
