FROM registry.fedoraproject.org/fedora:27

RUN mkdir /src/
WORKDIR /src
COPY ./requirements.sh /src/
RUN ./requirements.sh && \
    dnf clean all

COPY . /src
RUN pip3 install --user . && \
    pip2 install --user .
