FROM registry.fedoraproject.org/fedora:30

# ANSIBLE_STDOUT_CALLBACK - nicer output from the playbook run
ENV LANG=en_US.UTF-8 \
    PYTHONDONTWRITEBYTECODE=yes \
    WORKDIR=/src \
    ANSIBLE_STDOUT_CALLBACK=debug


RUN dnf install -y ansible && dnf clean all

WORKDIR /src
COPY . /src

# install all packages
RUN ansible-playbook -vv -c local -i localhost, files/install-packages.yaml \
    && dnf clean all

# install conu
RUN pip3 install .
