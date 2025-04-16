FROM python:3.13
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1
EXPOSE 80
RUN chmod +x entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]