FROM python:3.8
LABEL maintainer "Simone Pessina <pessina.simone4@gmail.com>"
WORKDIR /app
COPY requirements.txt /
RUN pip install -r /requirements.txt
COPY ./ ./
EXPOSE 8050
CMD ["python", "./app.py"]