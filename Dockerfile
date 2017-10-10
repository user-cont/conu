FROM registry.fedoraproject.org/fedora:26

COPY . /src
WORKDIR /src
RUN ./requirements.sh && \
    dnf clean all && \
    pip3 install --user . && \
    pip2 install --user .
