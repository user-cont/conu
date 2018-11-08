# vi: set ft=ruby :
# -*- coding: utf-8 -*-
# Authors: Jan Scotka <jscotka@redhat.com>
#

Vagrant.configure(2) do |config|

    config.vm.box = "fedora/28-cloud-base"
    config.vm.hostname = "conu-test-vm"
    config.vm.post_up_message = "This VM used for podman development."

    config.vm.provider :virtualbox do |vb|
        vb.name = "fedora-conu-podman-dev"
    end

    config.vm.synced_folder ".", "/vagrant", type: "rsync", rsync__exclude: ".git/"

    config.vm.provision "shell", inline: <<-SHELL
        set -x
        cd /vagrant
        sudo dnf install -y systemd-container make
        sudo make install-requirements
        sudo make install-test-requirements
        sudo pip2 install --user -r tests/requirements.txt
        sudo pip2 install --user -r requirements.txt
        sudo pip2 install --user .
        sudo pip3 install --user -r tests/requirements.txt
        sudo pip3 install --user -r requirements.txt
        sudo pip3 install --user .
        sudo systemctl start docker
        systemctl enable --now io.podman.socket
    SHELL
end