# vi: set ft=ruby :
# -*- coding: utf-8 -*-
# Authors: Jan Scotka <jscotka@redhat.com>
#

Vagrant.configure(2) do |config|

    config.vm.box = "fedora/29-cloud-base"
    config.vm.hostname = "conu-test-vm"
    config.vm.post_up_message = "This VM is purposed to run test suite of conu."
    config.vm.synced_folder ".", "/sharedolder", type: "sshfs"

    config.vm.provider "libvirt" do |libvirt|
        libvirt.memory = 2048
        libvirt.nested = true
        libvirt.cpu_mode = "host-model"
    end

    config.vm.provision "shell", inline: <<-SHELL
        set -x
        cd /vagrant
        sudo dnf install -y systemd-container make
        sudo make install-requirements
        sudo make install-test-requirements
        sudo pip3 install --user -r tests/requirements.txt
        sudo pip3 install --user -r requirements.txt
        sudo pip3 install --user .
        sudo systemctl start docker
        sudo -E make exec-test
    SHELL
end