FROM python:3.9-alpine
COPY pip.conf /etc/pip.conf
RUN mkdir /app
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt --no-cache-dir
COPY extensions.py main.py ./
CMD ["python","-u","./main.py"]