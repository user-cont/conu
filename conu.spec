%global pypi_name conu

%if 0%{?rhel} && 0%{?rhel} <= 7
%bcond_with python3
%else
%bcond_without python3
%endif

Name:           %{pypi_name}
Version:        0.6.2
Release:        2%{?dist}
Summary:        library which makes it easy to write tests for your containers

License:        GPLv3+
URL:            https://github.com/fedora-modularity/conu
Source0:        https://files.pythonhosted.org/packages/source/c/%{pypi_name}/%{pypi_name}-%{version}.tar.gz
BuildArch:      noarch
# exclude ppc64 because there is no docker package
# https://bugzilla.redhat.com/show_bug.cgi?id=1547049
ExcludeArch:    ppc64

# for docs

%if %{with python3}
%endif

%description
`conu` is a library which makes it easy to write tests for your containers
and is handy when playing with containers inside your code.
It defines an API to access and manipulate containers,
images and provides more, very helpful functions.

%if (0%{?fedora} && 0%{?fedora} <= 29) || (0%{?rhel} && 0%{?rhel} <= 7)
%package -n     python2-%{pypi_name}
Summary:        %{summary}
%{?python_provide:%python_provide python2-%{pypi_name}}
BuildRequires:  python2-devel
BuildRequires:  python2-setuptools
%if 0%{?rhel} && 0%{?rhel} <= 7
BuildRequires:  python-docker-py
BuildRequires:  python-enum34
BuildRequires:  python-kubernetes
Requires:       python-kubernetes
Requires:       python-docker-py
Requires:       python-enum34
Requires:       python-requests
%else
BuildRequires:  python2-docker
BuildRequires:  python2-enum34
BuildRequires:  python2-kubernetes
Requires:       python2-kubernetes
Requires:       python2-docker
Requires:       python2-enum34
Requires:       python2-requests
%endif
%if (0%{?fedora} && 0%{?fedora} <= 27) || (0%{?rhel} && 0%{?rhel} <= 7)
BuildRequires:  pyxattr
Requires:       pyxattr
%else
BuildRequires:  python2-pyxattr
Requires:       python2-pyxattr
%endif
Requires:       python2-six
# this is the only way to create containers right now
Requires:       docker
%if 0%{?rhel} && 0%{?rhel} <= 7
# no s2i on centos :<
# Requires:       source-to-image
Requires:       acl
Requires:       libselinux-utils
%else
# these are optional but still recommended
Recommends:     source-to-image
Recommends:     acl
Recommends:     libselinux-utils
%endif

%description -n python2-%{pypi_name}
`conu` is a library which makes it easy to write tests for your containers
and is handy when playing with containers inside your code.
It defines an API to access and manipulate containers,
images and provides more, very helpful functions.

%package -n     python2-%{pypi_name}-pytest
Summary:        fixtures which can be utilized via pytest
%{?python_provide:%python_provide python2-%{pypi_name}-pytest}
Requires:       python2-pytest
Requires:       python2-%{pypi_name}

%description -n python2-%{pypi_name}-pytest
fixtures which can be utilized via pytest
%endif

%if %{with python3}
%package -n     python3-%{pypi_name}
Summary:        %{summary}
%{?python_provide:%python_provide python3-%{pypi_name}}
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  python3-kubernetes
BuildRequires:  python3-docker
BuildRequires:  python3-requests
BuildRequires:  python3-pyxattr
BuildRequires:  python3-six
Requires:       python3-kubernetes
Requires:       python3-docker
Requires:       python3-requests
Requires:       python3-pyxattr
Requires:       python3-six
# this is the only way to create containers right now
Requires:       docker
# these are optional but still recommended
Recommends:     source-to-image
Recommends:     acl
Recommends:     libselinux-utils

%description -n python3-%{pypi_name}
`conu` is a library which makes it easy to write tests for your containers
and is handy when playing with containers inside your code.
It defines an API to access and manipulate containers,
images and provides more, very helpful functions.

%package -n     python3-%{pypi_name}-pytest
Summary:        fixtures which can be utilized via pytest
%{?python_provide:%python_provide python3-%{pypi_name}-pytest}
Requires:       python3-pytest
Requires:       python3-%{pypi_name}

%description -n python3-%{pypi_name}-pytest
fixtures which can be utilized via pytest
%endif

%package -n %{pypi_name}-doc
Summary:        conu documentation
%if %{with python3}
BuildRequires:  python3-sphinx
%else
%if (0%{?fedora} && 0%{?fedora} <= 29) || (0%{?rhel} && 0%{?rhel} <= 7)
BuildRequires:  python2-sphinx
%endif  # if fedora
%endif  # if python3

%description -n %{pypi_name}-doc
Documentation for conu.

%prep
%autosetup -n %{pypi_name}-%{version}
# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info

%build
%if (0%{?fedora} && 0%{?fedora} <= 29) || (0%{?rhel} && 0%{?rhel} <= 7)
%py2_build
%endif
%if %{with python3}
%py3_build
%endif

# generate html docs
PYTHONPATH="${PWD}:${PWD}/docs/" sphinx-build docs/source html
# remove the sphinx-build leftovers
rm -rf html/.{doctrees,buildinfo}

%install
%if %{with python3}
%py3_install
%endif
%if (0%{?fedora} && 0%{?fedora} <= 29) || (0%{?rhel} && 0%{?rhel} <= 7)
%py2_install
%endif

%if (0%{?fedora} && 0%{?fedora} <= 29) || (0%{?rhel} && 0%{?rhel} <= 7)
%files -n python2-%{pypi_name}
%license LICENSE
%doc README.md
%{python2_sitelib}/%{pypi_name}/
%{python2_sitelib}/%{pypi_name}-*.egg-info/
%exclude %{python2_sitelib}/tests
%exclude %{python3_sitelib}/fixtures

%files -n python2-%{pypi_name}-pytest
%license LICENSE
%{python2_sitelib}/%{pypi_name}/fixtures/
%endif

%if %{with python3}
%files -n python3-%{pypi_name}
%license LICENSE
%doc README.md
%{python3_sitelib}/%{pypi_name}/
%{python3_sitelib}/%{pypi_name}-*.egg-info/
%exclude %{python3_sitelib}/tests
%exclude %{python3_sitelib}/fixtures

%files -n python3-%{pypi_name}-pytest
%license LICENSE
%{python3_sitelib}/%{pypi_name}/fixtures/
%endif

%files -n %{pypi_name}-doc
%doc html
%license LICENSE

%changelog
* Mon Jan 21 2019 Tomas Tomecek <ttomecek@redhat.com> - 0.6.2-2
- packaging fixes

* Thu Nov 15 2018 Tomas Tomecek <ttomecek@redhat.com> 0.6.2-1
- 0.6.2 release

* Wed Nov 14 2018 lachmanfrantisek <lachmanfrantisek@gmail.com> 0.6.1-1
- 0.6.1 release

* Wed Oct 24 2018 Radoslav Pitoňák <rado.pitonak@gmail.com> 0.6.0-1
- 0.6.0 release

* Thu Sep 13 2018 Radoslav Pitonak <rado.pitonak@gmail.com> - 0.5.0-2
- add dependency kubernetes 

* Thu Sep 13 2018 Radoslav Pitonak <rado.pitonak@gmail.com> - 0.5.0-1
- New upstream release 0.5.0

* Thu Jul 12 2018 Fedora Release Engineering <releng@fedoraproject.org> - 0.4.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Tue Jun 19 2018 Miro Hrončok <mhroncok@redhat.com> - 0.4.0-2
- Rebuilt for Python 3.7

* Fri May 25 2018 Tomas Tomecek <ttomecek@redhat.com> - 0.4.0-1
- New upstream release 0.4.0

* Wed May 02 2018 Tomas Tomecek <ttomecek@redhat.com> - 0.3.1-1
- New upstream release 0.3.1

* Thu Feb 01 2018 Tomas Tomecek <ttomecek@redhat.com> 0.2.0-1
- 0.2.0 release

* Wed Dec 06 2017 Tomas Tomecek <ttomecek@redhat.com> - 0.1.0-1
- Initial package.
