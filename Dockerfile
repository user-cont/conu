FROM registry.fedoraproject.org/fedora:27

ENV PYTHONDONTWRITEBYTECODE=yes

WORKDIR /src
COPY ./requirements.sh /src/
RUN ./requirements.sh && \
    dnf clean all

COPY . /src
RUN pip3 install --user . && \
    pip2 install --user .
