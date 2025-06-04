FROM python:3.13-alpine

WORKDIR /app
COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . .

EXPOSE 5005

HEALTHCHECK CMD wget --spider http://127.0.0.1:5005/healthz || exit 1
CMD [ "python3", "web_service.py" ]