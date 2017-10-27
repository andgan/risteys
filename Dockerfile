FROM python:3.6

MAINTAINER Andrea Ganna

WORKDIR /var/www

ADD . /var/www

RUN pip install -r requirements.txt

EXPOSE 80


CMD ["python3","routes.py"]