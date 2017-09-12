%global framework_name conu

Name:           conu
Version:        0.0.1
Release:        1%{?dist}
Summary:        Container testing library

License:        GPLv2+
URL:            https://github.com/fedora-modularity/conu
Source0:        https://codeload.github.com/fedora-modularity/%{name}/tar.gz/%{name}-%{version}.tar.gz
BuildArch:      noarch

BuildRequires:  python2-devel
BuildRequires:  python2-setuptools
Requires:       docker
Provides:       conu = %{version}-%{release}

%description
Container testing library

%prep
%autosetup
# Remove bundled egg-info
rm -rf %{name}.egg-info

%build
%py2_build

%install
%py2_install
install -d -p -m 755 %{buildroot}%{_datadir}/%{framework_name}

%files
%license LICENSE
%{python2_sitelib}/conu/
%{python2_sitelib}/conu-*.egg-info/
%{_datadir}/conu/


%changelog
* Tue Sep 12 2017 Jan Scotka <jscotka@redhat.com> - 0.1.0-1
- Initial version

