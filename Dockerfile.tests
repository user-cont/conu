FROM docker.io/usercont/conu:dev

RUN dnf install -y nmap-ncat make && \
    pip3 install --user -r tests/requirements.txt

# a solution to set cgroup_manager to cgroupfs since we don't have
# systemd in the container where we run tests
RUN cp /usr/share/containers/libpod.conf /etc/containers/ \
    && sed -i '/cgroup_manager/ s/systemd/cgroupfs/' /etc/containers/libpod.conf
