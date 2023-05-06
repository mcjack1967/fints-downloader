FROM python:3.8.0-slim
COPY ./ /app
RUN apt-get update \
&& apt-get install gcc -y \
&& apt-get clean
WORKDIR app
RUN pip install --user -r requirements.txt
ENV DATA_PATH "/usr/data/"
RUN mkdir -p $DATA_PATH

CMD ["python","app.py"]