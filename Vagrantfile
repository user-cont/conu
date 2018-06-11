# vi: set ft=ruby :
# -*- coding: utf-8 -*-
# Authors: Jan Scotka <jscotka@redhat.com>
#

Vagrant.configure(2) do |config|

    config.vm.box = "fedora/28-cloud-base"
    config.vm.hostname = "conu-test-vm"
    config.vm.post_up_message = "This VM is purposed to run test suite of conu."

    config.vm.provider "libvirt" do |libvirt|
        libvirt.memory = 2048
        libvirt.nested = true
        libvirt.cpu_mode = "host-model"
    end

    config.vm.provision "shell", inline: <<-SHELL
        set -x
        cd /vagrant
        sudo ./requirements.sh
        sudo -E make exec-test
    SHELL
end
