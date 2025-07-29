FROM python:3.9-slim

WORKDIR /opt/operator

# copy your complete operator logic
COPY webapp-operator.py .

# install deps at build time
RUN pip install --no-cache-dir kubernetes pyyaml

# run operator
CMD ["python", "webapp-operator.py"]
