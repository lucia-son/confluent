FROM python:3.7
WORKDIR /usr/src/app
COPY ./krb5.conf /etc
COPY . . 
RUN pip install --upgrade pip setuptools wheel 
RUN pip install -r requirements.txt 
CMD ["python-producer.py"]
ENTRYPOINT ["python3"]
