FROM python:3.12

EXPOSE 80 2222
WORKDIR /usr/src/app

COPY . .

RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && curl https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends \
    unixodbc msodbcsql18 dialog openssh-server \
    && echo "root:Docker!" | chpasswd \
    && chmod +x ./entrypoint.sh
COPY sshd_config /etc/ssh/

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["./entrypoint.sh"]