# vi: set ft=ruby :
# -*- coding: utf-8 -*-
# Authors: Jan Scotka <jscotka@redhat.com>
#

Vagrant.configure(2) do |config|

    config.vm.box = "fedora/27-cloud-base"
    config.vm.network "private_network", ip: "192.168.50.10"
    config.vm.hostname = "conu"
    config.vm.post_up_message = "This is machine with installed conu, for testing nspawn abilities"

    config.vm.provider "libvirt" do |libvirt|
        libvirt.memory = 1024
        libvirt.nested = true
        libvirt.cpu_mode = "host-model"
    end

    config.vm.provision "shell", inline: <<-SHELL
        set -x
        cd /vagrant
        dnf -y install python2-nose git /usr/sbin/mkfs.btrfs
        make install
        setenforce 0
        nosetests -vdx tests/integration/test_nspawn_backend.py
    SHELL
end
