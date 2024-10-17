# TODO, maybe sometime:
# * Do something about mutex errors sometimes occurring when init scripts'
#   restart is invoked; something like "sleep 2" between stop and start?
# * Use "Include" in zabbix_{agentd,proxy,server}.conf, point to corresponding
#   /etc/zabbix/zabbix_*.conf.d/ dir; needs patching in order to not load
#   various backup files (*.rpm{orig,new,save}, *~ etc) in that dir.

%global srcname zabbix

Summary:	Open-source monitoring solution for your IT infrastructure
Name:		zabbix
Version:	2.0.14
Release:	2
License:	GPLv2+
Group:		Monitoring
Url:		https://www.zabbix.com/
Source0:	http://downloads.sourceforge.net/%{srcname}/%{srcname}-%{version}.tar.gz
# upstream tarball minus src/zabbix_java/lib/org-json-2010-12-28.jar
#Source0:	%{srcname}-%{version}-free.tar.gz
Source1:	zabbix-web.conf
Source5:	zabbix-logrotate.in
# tmpfiles for F >= 15 mandriva >= 2012
Source9:	zabbix-tmpfiles.conf
# systemd units
Source10:	zabbix-agent.service
Source11:	zabbix-proxy-mysql.service
Source12:	zabbix-proxy-pgsql.service
Source13:	zabbix-proxy-sqlite3.service
Source14:	zabbix-server-mysql.service
Source15:	zabbix-server-pgsql.service
Source16:	zabbix-server-sqlite3.service

# local rules for config files
Patch0:		zabbix-2.0.1-config.patch
# local rules for config files - fonts
Patch1:		zabbix-2.0.14-fonts-config.patch
# remove flash content (#737337)
# https://support.zabbix.com/browse/ZBX-4794
Patch2:		zabbix-2.0.1-no-flash.patch
# adapt for fping3 - https://support.zabbix.com/browse/ZBX-4894
Patch3:		zabbix-1.8.12-fping3.patch

BuildRequires:	systemd-units
BuildRequires:	mysql-devel
BuildRequires:	net-snmp-devel
#BuildRequires:	openldap-devel
BuildRequires:	unixODBC-devel
BuildRequires:	pkgconfig(gnutls)
BuildRequires:	pkgconfig(iksemel)
BuildRequires:	pkgconfig(libcurl)
BuildRequires:	pkgconfig(libpq)
BuildRequires:	pkgconfig(libssh2)
BuildRequires:	pkgconfig(OpenIPMI)
BuildRequires:	pkgconfig(sqlite3)

Requires:	logrotate
Requires(pre):	shadow-utils
%if %{srcname} != %{name}
Conflicts:	%{srcname}
%endif

%description
ZABBIX is software that monitors numerous parameters of a network and
the health and integrity of servers. ZABBIX uses a flexible
notification mechanism that allows users to configure e-mail based
alerts for virtually any event.  This allows a fast reaction to server
problems. ZABBIX offers excellent reporting and data visualisation
features based on the stored data. This makes ZABBIX ideal for
capacity planning.

ZABBIX supports both polling and trapping. All ZABBIX reports and
statistics, as well as configuration parameters are accessed through a
web-based front end. A web-based front end ensures that the status of
your network and the health of your servers can be assessed from any
location. Properly configured, ZABBIX can play an important role in
monitoring IT infrastructure. This is equally true for small
organisations with a few servers and for large companies with a
multitude of servers.

%files
%doc AUTHORS ChangeLog COPYING NEWS README
%dir %{_sysconfdir}/%{srcname}
%config(noreplace) %{_sysconfdir}/tmpfiles.d/zabbix.conf
%attr(0755,zabbix,zabbix) %dir %{_localstatedir}/lib/%{srcname}
%attr(0755,zabbix,zabbix) %dir %{_localstatedir}/log/%{srcname}
%{_bindir}/zabbix_get
%{_bindir}/zabbix_sender
%{_mandir}/man1/zabbix_get.1*
%{_mandir}/man1/zabbix_sender.1*

%pre
getent group zabbix > /dev/null || groupadd -r zabbix
getent passwd zabbix > /dev/null || \
    useradd -r -g zabbix -d %{_localstatedir}/lib/%{srcname} -s /sbin/nologin \
    -c "Zabbix Monitoring System" zabbix
:

#----------------------------------------------------------------------------

%package server
Summary:	Zabbix server common files
Group:		Monitoring
Requires:	%{name} = %{EVRD}
Requires:	%{name}-server-implementation = %{EVRD}
Requires:	fping
Requires:	traceroute

%description server
Zabbix server common files

%files server
%doc misc/snmptrap/zabbix_trap_receiver.pl
%attr(0640,root,zabbix) %config(noreplace) %{_sysconfdir}/zabbix_server.conf
%{_sysconfdir}/%{srcname}/zabbix_server.conf
%attr(0755,zabbix,zabbix) %dir %{_sysconfdir}/%{srcname}/externalscripts
%config(noreplace) %{_sysconfdir}/logrotate.d/zabbix-server
%ghost %{_unitdir}/zabbix-server.service
%{_mandir}/man8/zabbix_server.8*

#----------------------------------------------------------------------------

%package server-mysql
Summary:	Zabbix server compiled to use MySQL
Group:		Monitoring
Requires:	%{name} = %{EVRD}
Requires:	%{name}-server = %{EVRD}
Requires(post,preun,postun):	systemd-units
Provides:	%{name}-server-implementation = %{EVRD}
Conflicts:	%{name}-server-pgsql
Conflicts:	%{name}-server-sqlite3

%description server-mysql
Zabbix server compiled to use MySQL.

%files server-mysql
%{_docdir}/%{srcname}-server-mysql-%{version}/
%{_sbindir}/zabbix_server_mysql
%{_unitdir}/zabbix-server-mysql.service

%post server-mysql
if [ $1 -eq 1 ] ; then
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
fi
ln -sf %{_unitdir}/zabbix-server-mysql.service %{_unitdir}/zabbix-server.service

%preun server-mysql
if [ $1 -eq 0 ] ; then
    /bin/systemctl --no-reload disable zabbix-server-mysql.service > /dev/null 2>&1 || :
    /bin/systemctl stop zabbix-server-mysql.service > /dev/null 2>&1 || :
fi

%postun server-mysql
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    /bin/systemctl try-restart zabbix-server-mysql.service >/dev/null 2>&1 || :
fi

#----------------------------------------------------------------------------

%package server-pgsql
Summary:	Zabbix server compiled to use PostgresSQL
Group:		Monitoring
Requires:	%{name} = %{EVRD}
Requires:	%{name}-server = %{EVRD}
Requires(post,preun,postun):	systemd-units
Provides:	%{name}-server-implementation = %{EVRD}
Conflicts:	%{name}-server-mysql
Conflicts:	%{name}-server-sqlite3

%description server-pgsql
Zabbix server compiled to use PostgresSQL.

%post server-pgsql
if [ $1 -eq 1 ] ; then
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
fi
ln -sf %{_unitdir}/zabbix-server-pgsql.service %{_unitdir}/zabbix-server.service

%files server-pgsql
%{_docdir}/%{srcname}-server-pgsql-%{version}/
%{_sbindir}/zabbix_server_pgsql
%{_unitdir}/zabbix-server-pgsql.service

%preun server-pgsql
if [ $1 -eq 0 ] ; then
    /bin/systemctl --no-reload disable zabbix-server-pgsql.service > /dev/null 2>&1 || :
    /bin/systemctl stop zabbix-server-pgsql.service > /dev/null 2>&1 || :
fi

%postun server-pgsql
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    /bin/systemctl try-restart zabbix-server-pgsql.service >/dev/null 2>&1 || :
fi

#----------------------------------------------------------------------------

%package server-sqlite3
Summary:	Zabbix server compiled to use SQLite
Group:		Monitoring
Requires:	%{name} = %{EVRD}
Requires:	%{name}-server = %{EVRD}
Requires(post,preun,postun):	systemd-units
Provides:	%{name}-server-implementation = %{EVRD}
Conflicts:	%{name}-server-mysql
Conflicts:	%{name}-server-pgsql

%description server-sqlite3
Zabbix server compiled to use SQLite.

%files server-sqlite3
%{_docdir}/%{srcname}-server-sqlite3-%{version}/
%{_sbindir}/zabbix_server_sqlite3
%{_unitdir}/zabbix-server-sqlite3.service

%post server-sqlite3
if [ $1 -eq 1 ] ; then
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
fi
ln -sf %{_unitdir}/zabbix-server-sqlite3.service %{_unitdir}/zabbix-server.service

%preun server-sqlite3
if [ $1 -eq 0 ] ; then
    /bin/systemctl --no-reload disable zabbix-server-sqlite3.service > /dev/null 2>&1 || :
    /bin/systemctl stop zabbix-server-sqlite3.service > /dev/null 2>&1 || :
fi

%postun server-sqlite3
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    /bin/systemctl try-restart zabbix-server-sqlite3.service >/dev/null 2>&1 || :
fi

#----------------------------------------------------------------------------

%package agent
Summary:	Zabbix Agent
Group:		Monitoring
Requires:	%{name} = %{EVRD}
Requires(post,preun,postun):	systemd-units

%description agent
The Zabbix client agent, to be installed on monitored systems.

%files agent
%doc conf/zabbix_agentd/*.conf
%config(noreplace) %{_sysconfdir}/zabbix_agent.conf
%{_sysconfdir}/%{srcname}/zabbix_agent.conf
%config(noreplace) %{_sysconfdir}/zabbix_agentd.conf
%{_sysconfdir}/%{srcname}/zabbix_agentd.conf
%config(noreplace) %{_sysconfdir}/logrotate.d/zabbix-agent
%{_unitdir}/zabbix-agent.service
%{_sbindir}/zabbix_agent
%{_sbindir}/zabbix_agentd
%{_mandir}/man8/zabbix_agentd.8*

%post agent
if [ $1 -eq 1 ] ; then
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
fi

%preun agent
if [ $1 -eq 0 ] ; then
    /bin/systemctl --no-reload disable zabbix-agent.service > /dev/null 2>&1 || :
    /bin/systemctl stop zabbix-agent.service > /dev/null 2>&1 || :
fi

%postun agent
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    /bin/systemctl try-restart zabbix-agent.service >/dev/null 2>&1 || :
fi

#----------------------------------------------------------------------------

%package proxy
Summary:	Zabbix Proxy
Group:		Monitoring
Requires:	%{name} = %{version}-%{release}
Requires:	%{name}-proxy-implementation = %{EVRD}
Requires:	fping

%description proxy
The Zabbix proxy.

%files proxy
%doc misc/snmptrap/zabbix_trap_receiver.pl
%attr(0640,root,zabbix) %config(noreplace) %{_sysconfdir}/zabbix_proxy.conf
%{_sysconfdir}/%{srcname}/zabbix_proxy.conf
%attr(0755,zabbix,zabbix) %dir %{_sysconfdir}/%{srcname}/externalscripts
%config(noreplace) %{_sysconfdir}/logrotate.d/zabbix-proxy
%ghost %{_unitdir}/zabbix-proxy.service
%{_mandir}/man8/zabbix_proxy.8*

#----------------------------------------------------------------------------

%package proxy-mysql
Summary:	Zabbix proxy compiled to use MySQL
Group:		Monitoring
Requires:	%{name}-proxy = %{EVRD}
Requires(post,preun,postun):	systemd-units
Provides:	%{name}-proxy-implementation = %{EVRD}

%description proxy-mysql
The Zabbix proxy compiled to use MySQL.

%files proxy-mysql
%{_docdir}/%{srcname}-proxy-mysql-%{version}/
%{_sbindir}/zabbix_proxy_mysql
%{_unitdir}/zabbix-proxy-mysql.service

%post proxy-mysql
if [ $1 -eq 1 ] ; then
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
fi
ln -sf %{_unitdir}/zabbix-proxy-mysql.service %{_unitdir}/zabbix-proxy.service

%preun proxy-mysql
if [ $1 -eq 0 ] ; then
    /bin/systemctl --no-reload disable zabbix-proxy-mysql.service > /dev/null 2>&1 || :
    /bin/systemctl stop zabbix-proxy-mysql.service > /dev/null 2>&1 || :
fi

%postun proxy-mysql
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    /bin/systemctl try-restart zabbix-proxy-mysql.service >/dev/null 2>&1 || :
fi

#----------------------------------------------------------------------------

%package proxy-pgsql
Summary:	Zabbix proxy compiled to use PostgreSQL
Group:		Monitoring
Requires:	%{name}-proxy = %{EVRD}
Requires(post,preun,postun):	systemd-units
Provides:	%{name}-proxy-implementation = %{EVRD}

%description proxy-pgsql
The Zabbix proxy compiled to use PostgreSQL.

%files proxy-pgsql
%{_docdir}/%{srcname}-proxy-pgsql-%{version}/
%{_sbindir}/zabbix_proxy_pgsql
%{_unitdir}/zabbix-proxy-pgsql.service

%post proxy-pgsql
if [ $1 -eq 1 ] ; then
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
fi
ln -sf %{_unitdir}/zabbix-proxy-pgsql.service %{_unitdir}/zabbix-proxy.service

%preun proxy-pgsql
if [ $1 -eq 0 ] ; then
    /bin/systemctl --no-reload disable zabbix-proxy-pgsql.service > /dev/null 2>&1 || :
    /bin/systemctl stop zabbix-proxy-pgsql.service > /dev/null 2>&1 || :
fi

%postun proxy-pgsql
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    /bin/systemctl try-restart zabbix-proxy-pgsql.service >/dev/null 2>&1 || :
fi

#----------------------------------------------------------------------------

%package proxy-sqlite3
Summary:	Zabbix proxy compiled to use SQLite
Group:		Monitoring
Requires:	%{name}-proxy = %{EVRD}
Requires(post,preun,postun):	systemd-units
Provides:	%{name}-proxy-implementation = %{EVRD}

%description proxy-sqlite3
The Zabbix proxy compiled to use SQLite.

%files proxy-sqlite3
%{_docdir}/%{srcname}-proxy-sqlite3-%{version}/
%{_sbindir}/zabbix_proxy_sqlite3
%{_unitdir}/zabbix-proxy-sqlite3.service

%post proxy-sqlite3
if [ $1 -eq 1 ] ; then
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
fi
ln -sf %{_unitdir}/zabbix-proxy-sqlite3.service %{_unitdir}/zabbix-proxy.service

%preun proxy-sqlite3
if [ $1 -eq 0 ] ; then
    /bin/systemctl --no-reload disable zabbix-proxy-sqlite3.service > /dev/null 2>&1 || :
    /bin/systemctl stop zabbix-proxy-sqlite3.service > /dev/null 2>&1 || :
fi

%postun proxy-sqlite3
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    /bin/systemctl try-restart zabbix-proxy-sqlite3.service >/dev/null 2>&1 || :
fi

#----------------------------------------------------------------------------

%package web
Summary:	Zabbix Web Frontend
Group:		Monitoring
Requires:	php
Requires:	php-gd
Requires:	php-bcmath
Requires:	php-mbstring
Requires:	php-xml
Requires:	php-gettext
Requires:	fonts-ttf-dejavu
Requires:	%{name} = %{EVRD}
Requires:	%{name}-web-database = %{EVRD}
BuildArch:	noarch

%description web
The php frontend to display the Zabbix web interface.

%files web
%dir %attr(0750,apache,apache) %{_sysconfdir}/%{srcname}/web
%ghost %attr(0644,apache,apache) %config(noreplace) %{_sysconfdir}/%{srcname}/web/zabbix.conf.php
%config(noreplace) %{_sysconfdir}/httpd/conf.d/zabbix.conf
%{_datadir}/%{srcname}

#----------------------------------------------------------------------------

%package web-mysql
Summary:	Zabbix web frontend for MySQL
Group:		Monitoring
Requires:	%{name}-web = %{EVRD}
Requires:	php-mysql
Provides:	%{name}-web-database = %{EVRD}
Conflicts:	%{name}-web-pgsql
Conflicts:	%{name}-web-sqlite3
BuildArch:	noarch

%description web-mysql
Zabbix web frontend for MySQL.

%files web-mysql

#----------------------------------------------------------------------------

%package web-pgsql
Summary:	Zabbix web frontend for PostgreSQL
Group:		Monitoring
Requires:	%{name}-web = %{EVRD}
Requires:	php-pgsql
Provides:	%{name}-web-database = %{EVRD}
Conflicts:	%{name}-web-mysql
Conflicts:	%{name}-web-sqlite3
BuildArch:	noarch

%description web-pgsql
Zabbix web frontend for PostgreSQL.

%files web-pgsql

#----------------------------------------------------------------------------

%package web-sqlite3
Summary:	Zabbix web frontend for SQLite
Group:		Monitoring
Requires:	%{name}-web = %{EVRD}
# Need to use the same db file as the server
Requires:	%{name}-server-sqlite3 = %{EVRD}
Provides:	%{name}-web-database = %{EVRD}
Conflicts:	%{name}-web-mysql
Conflicts:	%{name}-web-pgsql
BuildArch:	noarch

%description web-sqlite3
Zabbix web frontend for SQLite.

%files web-sqlite3

#----------------------------------------------------------------------------

%prep
%setup0 -q -n %{srcname}-%{version}
%patch0 -p1
%patch1 -p1
%patch3 -p1

# remove bundled java libs
rm -rf src/zabbix_java/lib/*.jar

# remove included fonts
rm -rf frontends/php/fonts

# remove executable permissions
chmod a-x upgrades/dbpatches/*/mysql/upgrade

# All libraries are expected in /usr/lib or /usr/local/lib
# https://support.zabbix.com/browse/ZBXNEXT-1296
sed -i.orig -e 's|_LIBDIR=/usr/lib|_LIBDIR=%{_libdir}|g' \
    configure

# kill off .htaccess files, options set in SOURCE1
rm -f frontends/php/include/.htaccess
rm -f frontends/php/api/.htaccess
rm -f frontends/php/conf/.htaccess

# set timestamp on modified config file and directories
touch -r frontends/php/css.css frontends/php/include/config.inc.php \
    frontends/php/include/defines.inc.php \
    frontends/php/include \
    frontends/php/include/classes

# remove prebuilt Windows binaries
rm -rf bin

# remove flash applet
# https://support.zabbix.com/browse/ZBX-4794
rm -f frontend/php/images/flash/zbxclock.swf
%patch2 -p1

%build
common_flags="
    --enable-dependency-tracking
    --enable-server
    --enable-agent
    --enable-proxy
    --enable-ipv6
    --disable-java
    --with-net-snmp
    --with-ldap
    --with-libcurl
    --with-openipmi
    --with-jabber
    --with-unixodbc
    --with-ssh2
"

%configure2_5x $common_flags --with-mysql
%make
mv src/zabbix_server/zabbix_server src/zabbix_server/zabbix_server_mysql
mv src/zabbix_proxy/zabbix_proxy src/zabbix_proxy/zabbix_proxy_mysql

%configure2_5x $common_flags --with-postgresql
%make
mv src/zabbix_server/zabbix_server src/zabbix_server/zabbix_server_pgsql
mv src/zabbix_proxy/zabbix_proxy src/zabbix_proxy/zabbix_proxy_pgsql

%configure2_5x $common_flags --with-sqlite3
%make
mv src/zabbix_server/zabbix_server src/zabbix_server/zabbix_server_sqlite3
mv src/zabbix_proxy/zabbix_proxy src/zabbix_proxy/zabbix_proxy_sqlite3

touch src/zabbix_server/zabbix_server
touch src/zabbix_proxy/zabbix_proxy


%install
# set up some required directories
mkdir -p %{buildroot}%{_sysconfdir}/%{srcname}
mkdir -p %{buildroot}%{_sysconfdir}/%{srcname}/externalscripts
mkdir -p %{buildroot}%{_sysconfdir}/%{srcname}/web
mkdir -p %{buildroot}%{_sysconfdir}/logrotate.d
mkdir -p %{buildroot}%{_sysconfdir}/httpd/conf.d
mkdir -p %{buildroot}%{_unitdir}
mkdir -p %{buildroot}%{_datadir}
mkdir -p %{buildroot}%{_localstatedir}/lib/%{srcname}
mkdir -p %{buildroot}%{_localstatedir}/log/%{srcname}
mkdir -p %{buildroot}%{_localstatedir}/run/%{srcname}

# install the frontend
cp -a frontends/php %{buildroot}%{_datadir}/%{srcname}

# prepare ghosted config file
touch %{buildroot}%{_sysconfdir}/%{srcname}/web/zabbix.conf.php

# drop Apache config file in place
install -m 0644 -p %{SOURCE1} %{buildroot}%{_sysconfdir}/httpd/conf.d/%{srcname}.conf

# fix config file options
sed -i \
    -e 's|# PidFile=.*|PidFile=%{_localstatedir}/run/%{srcname}/zabbix_agentd.pid|g' \
    -e 's|^LogFile=.*|LogFile=%{_localstatedir}/log/%{srcname}/zabbix_agentd.log|g' \
    -e 's|# LogFileSize=.*|LogFileSize=0|g' \
    conf/zabbix_agentd.conf

sed -i \
    -e 's|# PidFile=.*|PidFile=%{_localstatedir}/run/%{srcname}/zabbix.pid|g' \
    -e 's|^LogFile=.*|LogFile=%{_localstatedir}/log/%{srcname}/zabbix_server.log|g' \
    -e 's|# LogFileSize=.*|LogFileSize=0|g' \
    -e 's|# AlertScriptsPath=/home/zabbix/bin/|AlertScriptsPath=%{_localstatedir}/lib/%{srcname}/|g' \
    -e 's|^DBUser=root|DBUser=zabbix|g' \
    -e 's|# DBSocket=/tmp/mysql.sock|DBSocket=%{_localstatedir}/lib/mysql/mysql.sock|g' \
    conf/zabbix_server.conf

sed -i \
    -e 's|# PidFile=.*|PidFile=%{_localstatedir}/run/%{srcname}/zabbix_proxy.pid|g' \
    -e 's|^LogFile=.*|LogFile=%{_localstatedir}/log/%{srcname}/zabbix_proxy.log|g' \
    -e 's|# LogFileSize=.*|LogFileSize=0|g' \
    -e 's|# AlertScriptsPath=/home/zabbix/bin/|AlertScriptsPath=%{_localstatedir}/lib/%{srcname}/|g' \
    -e 's|^DBUser=root|DBUser=zabbix|g' \
    -e 's|# DBSocket=/tmp/mysql.sock|DBSocket=%{_localstatedir}/lib/mysql/mysql.sock|g' \
    conf/zabbix_proxy.conf

# install log rotation
cat %{SOURCE5} | sed -e 's|COMPONENT|server|g' > \
     %{buildroot}%{_sysconfdir}/logrotate.d/zabbix-server
cat %{SOURCE5} | sed -e 's|COMPONENT|agentd|g' > \
     %{buildroot}%{_sysconfdir}/logrotate.d/zabbix-agent
cat %{SOURCE5} | sed -e 's|COMPONENT|proxy|g' > \
     %{buildroot}%{_sysconfdir}/logrotate.d/zabbix-proxy

# systemd units
install -m 0644 -p %{SOURCE10} %{buildroot}%{_unitdir}/zabbix-agent.service
install -m 0644 -p %{SOURCE11} %{buildroot}%{_unitdir}/zabbix-proxy-mysql.service
install -m 0644 -p %{SOURCE12} %{buildroot}%{_unitdir}/zabbix-proxy-pgsql.service
install -m 0644 -p %{SOURCE13} %{buildroot}%{_unitdir}/zabbix-proxy-sqlite3.service
install -m 0644 -p %{SOURCE14} %{buildroot}%{_unitdir}/zabbix-server-mysql.service
install -m 0644 -p %{SOURCE15} %{buildroot}%{_unitdir}/zabbix-server-pgsql.service
install -m 0644 -p %{SOURCE16} %{buildroot}%{_unitdir}/zabbix-server-sqlite3.service
touch %{buildroot}%{_unitdir}/zabbix-proxy.service
touch %{buildroot}%{_unitdir}/zabbix-server.service

# install
make DESTDIR=%{buildroot} install
rm %{buildroot}%{_sbindir}/zabbix_server
install -m 0755 -p src/zabbix_server/zabbix_server_* %{buildroot}%{_sbindir}/
rm %{buildroot}%{_sbindir}/zabbix_proxy
install -m 0755 -p src/zabbix_proxy/zabbix_proxy_* %{buildroot}%{_sbindir}/

# install compatibility links for config files
ln -sf %{_sysconfdir}/zabbix_agent.conf %{buildroot}%{_sysconfdir}/%{srcname}/zabbix_agent.conf
ln -sf %{_sysconfdir}/zabbix_agentd.conf %{buildroot}%{_sysconfdir}/%{srcname}/zabbix_agentd.conf
ln -sf %{_sysconfdir}/zabbix_server.conf %{buildroot}%{_sysconfdir}/%{srcname}/zabbix_server.conf
ln -sf %{_sysconfdir}/zabbix_proxy.conf %{buildroot}%{_sysconfdir}/%{srcname}/zabbix_proxy.conf

# nuke static libs and empty oracle upgrade sql
rm -rf %{buildroot}%{_libdir}/libzbx*.a

# copy sql files to appropriate per package locations
for pkg in proxy server ; do
    docdir=%{buildroot}%{_docdir}/%{srcname}-$pkg-mysql-%{version}
    install -dm 755 $docdir
    cp -p --parents database/mysql/schema.sql $docdir
    cp -p --parents database/mysql/data.sql $docdir
    cp -p --parents database/mysql/images.sql $docdir
    cp -pR --parents upgrades/dbpatches/1.6/mysql $docdir
    cp -pR --parents upgrades/dbpatches/1.8/mysql $docdir
    cp -pR --parents upgrades/dbpatches/2.0/mysql $docdir
    docdir=%{buildroot}%{_docdir}/%{srcname}-$pkg-pgsql-%{version}
    install -dm 755 $docdir
    cp -p --parents database/postgresql/schema.sql $docdir
    cp -p --parents database/postgresql/data.sql $docdir
    cp -p --parents database/postgresql/images.sql $docdir
    cp -pR --parents upgrades/dbpatches/1.6/postgresql $docdir
    cp -pR --parents upgrades/dbpatches/1.8/postgresql $docdir
    cp -pR --parents upgrades/dbpatches/2.0/postgresql $docdir
    docdir=%{buildroot}%{_docdir}/%{srcname}-$pkg-sqlite3-%{version}
    install -dm 755 $docdir
    cp -p --parents database/sqlite3/schema.sql $docdir
    cp -p --parents database/sqlite3/data.sql $docdir
    cp -p --parents database/sqlite3/images.sql $docdir
done
# remove extraneous ones
rm -rf %{buildroot}%{_datadir}/%{srcname}/create

# systemd must create /var/run/%{srcname}
mkdir -p %{buildroot}%{_sysconfdir}/tmpfiles.d
install -m 0644 %{SOURCE9} %{buildroot}%{_sysconfdir}/tmpfiles.d/zabbix.conf

