FROM python:3.13-alpine

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

EXPOSE 5005
CMD [ "python3", "web_service.py" ]