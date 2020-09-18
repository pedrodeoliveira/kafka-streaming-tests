FROM python:3.7-slim as builder

RUN apt-get update && \
    apt-get install gcc -y && \
    apt-get clean

COPY src/python/requirements.txt .

RUN pip install --no-cache-dir --user -r requirements.txt

COPY /src /src

# here is the app image
FROM python:3.7-slim as app

COPY --from=builder /root/.local /root/.local
COPY --from=builder /src /src

RUN apt-get update && \
    apt-get install sqlite3 && \
    apt-get clean

ENV PATH=/root/.local/bin:$PATH

WORKDIR /src
ENV PYTHONPATH=/src

CMD [ "python" ]
