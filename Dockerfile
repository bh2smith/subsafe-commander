FROM python:3.10
COPY . .
RUN pip install -r requirements.txt
ENTRYPOINT [ "python3", "-m" , "src.exec"]