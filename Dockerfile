FROM python:3.12

EXPOSE 80

RUN apt-get update && apt-get install -y --no-install-recommends \
    unixodbc

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "main:app"]