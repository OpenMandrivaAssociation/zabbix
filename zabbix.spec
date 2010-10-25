%define _disable_ld_as_needed 1
%define _localstatedir /var
%define _requires_exceptions pear

Name:           zabbix
Version:        1.8.3
Release:        %mkrel 1
Summary:        Open-source monitoring solution for your IT infrastructure

Group:          Networking/Other
License:        GPLv2+
URL:            http://www.zabbix.com/
Source0:        http://downloads.sourceforge.net/%{name}/%{name}-%{version}.tar.gz
Source1:        zabbix-web.conf
Source2:        zabbix-server.init
Source3:        zabbix-agent.init
Source4:        zabbix-logrotate.in
Patch:		zabbix-1.4-fixmysqlheaders.patch
Patch1:		zabbix-1.4-mysqlcflags.patch
Buildroot:      %{_tmppath}/%{name}-%{version}-root

%define database %{nil}
%define zdb %{nil}
%define with_postgresql %{?_with_postgresql: 1} %{?!_with_postgresql: 0}
#define with_mysql %{?_with_mysql: 1} %{?!_with_mysql: 0}
%define with_mysql %{?_without_mysql: 0} %{?!_without_mysql: 1}

# Zabbix can only be built with mysql -or- postgresql
# support. We build with mysql by default, but you can
# pass --with postgresql to build with postgresql instead.
%if %{with_postgresql}
%define database postgresql
%define zdb pgsql
%endif
%if %{with_mysql}
%define database mysql
%define zdb mysql
%endif

#if %{?database:1}%{!?database:0}
%if %{with_mysql} || %{with_postgresql}
BuildRequires:  	%{database}-devel
%endif
BuildRequires:		net-snmp-devel
BuildRequires:		openldap-devel, gnutls-devel
BuildRequires:		libiksemel-devel
BuildRequires:		libtasn1-devel
BuildRequires:		curl-devel
Requires:		logrotate, fping
%if %{?mdkversion:1}%{?!mdkversion:0}
Requires(pre):		rpm-helper
Requires(post):		rpm-helper
Requires(preun):	rpm-helper
%else
# for userdadd:
Requires(pre):		shadow-utils
Requires(post):		chkconfig
Requires(preun):	chkconfig
# for /sbin/service:
Requires(preun):	initscripts
%endif

%description
ZABBIX is software that monitors numerous parameters of a
network and the health and integrity of servers. ZABBIX
uses a flexible notification mechanism that allows users
to configure e-mail based alerts for virtually any event.
This allows a fast reaction to server problems. ZABBIX
offers excellent reporting and data visualisation features
based on the stored data. This makes ZABBIX ideal for
capacity planning.

ZABBIX supports both polling and trapping. All ZABBIX
reports and statistics, as well as configuration
parameters are accessed through a web-based front end. A
web-based front end ensures that the status of your network
and the health of your servers can be assessed from any
location. Properly configured, ZABBIX can play an important
role in monitoring IT infrastructure. This is equally true
for small organisations with a few servers and for large
companies with a multitude of servers.


%package agent
Summary:        Zabbix Agent
Group:          Networking/Other
Requires:       logrotate
%if %{?mdkversion:1}%{?!mdkversion:0}
Requires(pre):		rpm-helper
Requires(post):		rpm-helper
Requires(preun):	rpm-helper
%else
Requires(pre):      /usr/sbin/useradd
Requires(post):     /sbin/chkconfig
Requires(preun):    /sbin/chkconfig
Requires(preun):    /sbin/service
%endif

%description agent
The zabbix client agent, to be installed on monitored systems.

%package web
Summary:        Zabbix Web Frontend
Group:          Networking/Other
Requires:       php-%{zdb}, php-gd, apache-mod_php, php-bcmath php-sockets

%description web
The php frontend to display the zabbix web interface.

%prep
%setup -q
%patch -p1 -b .mysqlheaders
%patch1 -p1 -b .mysqlcflags
perl -pi -e 's/ -static//g' configure

# fix up some lib64 issues
%{__perl} -pi.orig -e 's|_LIBDIR=/usr/lib|_LIBDIR=%{_libdir}|g' \
    configure

# fix up pt_br
%{__chmod} a-x frontends/php/include/locales/pt_br.inc.php ||:
%{__sed} -i 's/\r//' frontends/php/include/locales/pt_br.inc.php ||:

%build
%configure \
    --enable-server \
    --enable-agent \
    --with-net-snmp \
    --with-ldap \
    --with-jabber \
    --enable-static=no \
%if %{with_mysql}
    --with-mysql
%endif
%if %{with_postgresql}
    --with-%{zdb} 
%endif
%if !%{with_mysql} && !%{with_postgresql}
    --with-sqlite3 
%endif
    #--disable-static
    #--with-mysql \
    #--with-mysql=%{_libdir}/mysql/mysql_config \
    #--with-mysql=%{_bindir}/mysql_config 

# --disable-static is partially broken atm,
# -static still gets into CFLAGS, so fix up in make
# (and even then, .a files still show their face...)
#find . -name Makefile -exec perl -pi -e 's/ -static//g' {} \;
%make
#make %{?_smp_mflags} CFLAGS="$RPM_OPT_FLAGS"

%install
rm -rf %{buildroot}
# set up some required directories
mkdir -p %{buildroot}%{_sysconfdir}/%{name}
mkdir -p %{buildroot}%{_sysconfdir}/init.d
mkdir -p %{buildroot}%{_sysconfdir}/logrotate.d
mkdir -p %{buildroot}%{_sysconfdir}/httpd/conf.d
mkdir -p %{buildroot}%{_datadir}
mkdir -p %{buildroot}%{_localstatedir}/log/%{name}
mkdir -p %{buildroot}%{_localstatedir}/run/%{name}
# php frontend
cp -a frontends/php %{buildroot}%{_datadir}/%{name}
mv %{buildroot}%{_datadir}/%{name}/include/db.inc.php \
    %{buildroot}%{_sysconfdir}/%{name}/
ln -s ../../../..%{_sysconfdir}/%{name}/db.inc.php \
    %{buildroot}%{_datadir}/%{name}/include/db.inc.php
# kill off .htaccess files, options set in SOURCE1
rm -f %{buildroot}%{_datadir}/%{name}/include/.htaccess
rm -f %{buildroot}%{_datadir}/%{name}/include/classes/.htaccess
# drop config files in place
install -m 0644 misc/conf/%{name}_agent.conf %{buildroot}%{_sysconfdir}/%{name}
cat misc/conf/%{name}_agentd.conf | sed \
    -e 's|PidFile=.*|PidFile=%{_localstatedir}/run/%{name}/%{name}_agentd.pid|g' \
    -e 's|LogFile=.*|LogFile=%{_localstatedir}/log/%{name}/%{name}_agentd.log|g' \
    > %{buildroot}%{_sysconfdir}/%{name}/%{name}_agentd.conf
cat misc/conf/zabbix_server.conf | sed \
    -e 's|PidFile=.*|PidFile=%{_localstatedir}/run/%{name}/%{name}.pid|g' \
    -e 's|LogFile=.*|LogFile=%{_localstatedir}/log/%{name}/%{name}_server.log|g' \
    -e 's|AlertScriptsPath=/home/%{name}/bin/|AlertScriptsPath=%{_localstatedir}/lib/%{name}/|g' \
    -e 's|DBUser=root|DBUser=%{name}|g' \
    -e 's|DBSocket=/tmp/mysql.sock|DBSocket=%{_localstatedir}/lib/%{zdb}/%{zdb}.sock|g' \
    -e 's|FpingLocation=/usr/sbin/fping|FpingLocation=/bin/fping|g' \
    > %{buildroot}%{_sysconfdir}/%{name}/%{name}_server.conf
install -m 0644 %{SOURCE1} %{buildroot}%{_sysconfdir}/httpd/conf.d/%{name}.conf
# log rotation
cat %{SOURCE4} | sed -e 's|COMPONENT|server|g' > \
     %{buildroot}%{_sysconfdir}/logrotate.d/%{name}
cat %{SOURCE4} | sed -e 's|COMPONENT|agentd|g' > \
     %{buildroot}%{_sysconfdir}/logrotate.d/%{name}-agent
# init scripts
install -m 0755 %{SOURCE2} %{buildroot}%{_sysconfdir}/init.d/%{name}
install -m 0755 %{SOURCE3} %{buildroot}%{_sysconfdir}/init.d/%{name}-agent

make DESTDIR=%{buildroot} install
rm -rf %{buildroot}%{_libdir}/libzbx*.a

%clean
rm -rf %{buildroot}

%pre
# Add the "zabbix" user
/usr/sbin/useradd -c "Zabbix Monitoring System" \
        -s /sbin/nologin -r -d %{_localstatedir}/lib/%{name} %{name} 2> /dev/null || :

%pre agent
# Add the "zabbix" user
/usr/sbin/useradd -c "Zabbix Monitoring System" \
        -s /sbin/nologin -r -d %{_localstatedir}/lib/%{name} %{name} 2> /dev/null || :

%post
/sbin/chkconfig --add %{name}

%post agent
/sbin/chkconfig --add %{name}-agent

%preun
if [ "$1" = 0 ]
then
  /sbin/service %{name} stop >/dev/null 2>&1 || :
  /sbin/chkconfig --del %{name}
fi

%preun agent
if [ "$1" = 0 ]
then
  /sbin/service %{name}-agent stop >/dev/null 2>&1 || :
  /sbin/chkconfig --del %{name}-agent
fi

%files
%defattr(-,root,root,-)
%doc AUTHORS ChangeLog COPYING CREDITS NEWS README
%doc create
%dir %{_sysconfdir}/%{name}
%{_sbindir}/%{name}_server
%{_sysconfdir}/init.d/%{name}
%{_mandir}/man8/%{name}_server.8*
%config(noreplace) %{_sysconfdir}/logrotate.d/zabbix
%config(noreplace) %{_sysconfdir}/%{name}/%{name}_server.conf
%attr(0755,%{name},%{name}) %dir %{_localstatedir}/log/%{name}
%attr(0755,%{name},%{name}) %dir %{_localstatedir}/run/%{name}

%files agent
%defattr(-,root,root,-)
%doc AUTHORS ChangeLog COPYING CREDITS NEWS README
%dir %{_sysconfdir}/%{name}
%{_bindir}/%{name}_sender
%{_bindir}/%{name}_get
%{_sbindir}/%{name}_agent
%{_sbindir}/%{name}_agentd
%{_mandir}/man1/%{name}_sender.1*
%{_mandir}/man1/%{name}_get.1*
%{_mandir}/man8/%{name}_agentd.8*
%{_sysconfdir}/init.d/%{name}-agent
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}-agent
%config(noreplace) %{_sysconfdir}/%{name}/%{name}_agent.conf
%config(noreplace) %{_sysconfdir}/%{name}/%{name}_agentd.conf
%attr(0755,%{name},%{name}) %dir %{_localstatedir}/log/%{name}
%attr(0755,%{name},%{name}) %dir %{_localstatedir}/run/%{name}

%files web
%defattr(-,root,root,-)
%doc README
%dir %{_sysconfdir}/%{name}
%config(noreplace) %{_sysconfdir}/%{name}/db.inc.php
%config(noreplace) %{_sysconfdir}/httpd/conf.d/%{name}.conf
%{_datadir}/%{name}

