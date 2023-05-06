FROM python:3.8-alpine
COPY ./ /app
WORKDIR app
RUN pip install --user -r requirements.txt
ENV DATA_PATH "/usr/data/"
RUN mkdir -p $DATA_PATH

CMD ["python","app.py"]