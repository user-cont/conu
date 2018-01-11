%global pypi_name conu

Name:           %{pypi_name}
Version:        0.1.0
Release:        1%{?dist}
Summary:        library which makes it easy to write tests for your containers

License:        GPLv3+
URL:            https://github.com/fedora-modularity/conu
Source0:        https://files.pythonhosted.org/packages/source/c/%{pypi_name}/%{pypi_name}-%{version}.tar.gz
BuildArch:      noarch

BuildRequires:  python2-devel
BuildRequires:  python2-setuptools

# for docs
BuildRequires:  python2-docker
BuildRequires:  python2-sphinx
BuildRequires:  pyxattr

BuildRequires:  python3-devel
BuildRequires:  python3-setuptools

%description
`conu` is a library which makes it easy to write tests for your containers
and is handy when playing with containers inside your code.
It defines an API to access and manipulate containers,
images and provides more, very helpful functions.


%package -n     python2-%{pypi_name}
Summary:        %{summary}
%{?python_provide:%python_provide python2-%{pypi_name}}

Requires:       python2-docker
Requires:       python2-requests
Requires:       python2-six
Requires:       pyxattr
Requires:       source-to-image
Requires:       acl
Requires:       atomic
Requires:       docker
Requires:       libselinux-utils
%description -n python2-%{pypi_name}
`conu` is a library which makes it easy to write tests for your containers
and is handy when playing with containers inside your code.
It defines an API to access and manipulate containers,
images and provides more, very helpful functions.


%package -n     python3-%{pypi_name}
Summary:        %{summary}
%{?python_provide:%python_provide python3-%{pypi_name}}

Requires:       python3-docker
Requires:       python3-requests
Requires:       python3-six
Requires:       python3-pyxattr
Requires:       source-to-image
Requires:       acl
Requires:       atomic
Requires:       docker
Requires:       libselinux-utils
%description -n python3-%{pypi_name}
`conu` is a library which makes it easy to write tests for your containers
and is handy when playing with containers inside your code.
It defines an API to access and manipulate containers,
images and provides more, very helpful functions.


%package -n %{pypi_name}-doc
Summary:        conu documentation
%description -n %{pypi_name}-doc
Documentation for conu.

%prep
%autosetup -n %{pypi_name}-%{version}
# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info

%build
%py2_build
%py3_build
# generate html docs
PYTHONPATH=${PWD} sphinx-build docs/source html
# remove the sphinx-build leftovers
rm -rf html/.{doctrees,buildinfo}

%install
%py3_install
%py2_install

%files -n python2-%{pypi_name}
%license LICENSE
%doc README.md
%{python2_sitelib}/%{pypi_name}
%{python2_sitelib}/%{pypi_name}-%{version}-py?.?.egg-info

%files -n python3-%{pypi_name}
%license LICENSE
%doc README.md
%{python3_sitelib}/%{pypi_name}
%{python3_sitelib}/%{pypi_name}-%{version}-py?.?.egg-info

%files -n %{pypi_name}-doc
%doc html
%license LICENSE

%changelog
* Wed Dec 06 2017 Tomas Tomecek <ttomecek@redhat.com> - 0.1.0-1
- Initial package.
