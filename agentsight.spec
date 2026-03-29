%define anolis_release 1
%global debug_package %{nil}

Name:           agentsight
Version:        0.1.0
Release:        %{anolis_release}%{?dist}
Summary:        eBPF-based AI Agent Observability Tool

License:        Apache-2.0
URL:            https://github.com/alibaba/anolisa
Source0:        %{name}-%{version}.tar.gz

# Build dependencies (required for OpenSSL compilation during cargo build)
BuildRequires:  perl-IPC-Cmd
BuildRequires:  perl-core

# Runtime dependencies
# Requires for eBPF components
Requires:       elfutils-libelf

%description
AgentSight is an eBPF-based AI Agent observability tool that provides zero-intrusion 
monitoring for AI Agents running on Linux, capturing SSL/TLS encrypted traffic, 
LLM API calls, token consumption, and process behaviors.

%prep
%setup -q

%build
# Binary is built by scripts/rpm-build.sh prior to rpmbuild and included in the source tarball.

%install
rm -rf $RPM_BUILD_ROOT
install -d -m 0755 %{buildroot}/usr/local/bin
install -d -m 0755 %{buildroot}%{_docdir}/agentsight

install -p -m 0755 agentsight %{buildroot}/usr/local/bin/
install -p -m 0644 README.md %{buildroot}%{_docdir}/agentsight/
install -p -m 0644 README_CN.md %{buildroot}%{_docdir}/agentsight/
install -p -m 0644 LICENSE %{buildroot}%{_docdir}/agentsight/

%files
%defattr(0644,root,root,0755)
%attr(0755,root,root) /usr/local/bin/agentsight
%doc %{_docdir}/agentsight/README.md
%doc %{_docdir}/agentsight/README_CN.md
%license %{_docdir}/agentsight/LICENSE

%changelog
* Mon Mar 30 2026 chengshuyi <chengshuyi.csy@alibaba-inc.com> - 0.1.0-1
- Initial AgentSight RPM package
