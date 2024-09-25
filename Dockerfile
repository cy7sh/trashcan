FROM python:3.12-alpine

EXPOSE 80
WORKDIR /usr/src/app

RUN apk --no-cache add curl unixodbc-dev g++ \
    && curl -O https://download.microsoft.com/download/7/6/d/76de322a-d860-4894-9945-f0cc5d6a45f8/msodbcsql18_18.4.1.1-1_amd64.apk \
    && curl -O https://download.microsoft.com/download/7/6/d/76de322a-d860-4894-9945-f0cc5d6a45f8/mssql-tools18_18.4.1.1-1_amd64.apk \
    && apk add --allow-untrusted msodbcsql18_18.4.1.1-1_amd64.apk \
    && apk add --allow-untrusted mssql-tools18_18.4.1.1-1_amd64.apk

COPY . .
RUN pip install --no-cache-dir -r requirements.txt \
    && chmod +x ./entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]