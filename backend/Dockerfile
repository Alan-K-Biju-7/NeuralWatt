FROM python:3.13-slim

# Fix OpenSSL 3.x TLS compatibility with MongoDB Atlas
RUN apt-get update && apt-get install -y \
    libssl-dev \
    ca-certificates \
    openssl \
    && rm -rf /var/lib/apt/lists/* \
    && sed -i 's/MinProtocol = TLSv1.2/MinProtocol = TLSv1/' /etc/ssl/openssl.cnf \
    && sed -i 's/CipherString = DEFAULT@SECLEVEL=2/CipherString = DEFAULT@SECLEVEL=1/' /etc/ssl/openssl.cnf

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
