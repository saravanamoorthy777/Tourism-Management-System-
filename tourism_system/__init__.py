import pymysql

# Patch MySQLdb with PyMySQL for cross-platform XAMPP/MySQL compatibility without C++ compiler
pymysql.version_info = (2, 2, 7, "final", 0)
pymysql.install_as_MySQLdb()

# ---------------------------------------------------------------------------
# DEV-ONLY: MySQL 5.5.20 compatibility shims for Django 5.x
#
# Root cause: Django 5.x requires MySQL 8.0.11+.  The installed server is
# MySQL 5.5.20 (Community Edition).  Two problems arise:
#
#   1. Django rejects the connection because VERSION() returns "5.5.20".
#   2. Django uses datetime(6) / time(6) column types that MySQL 5.5 does
#      not understand (fractional-second precision was added in MySQL 5.6).
#
# Both issues are patched below at the Python level so development can
# proceed without modifying the Django package or the MySQL installation.
#
# ACTION REQUIRED before production:
#   Upgrade MySQL to 8.0+ (or switch to MariaDB 10.5+) and remove this file.
# ---------------------------------------------------------------------------

def _apply_mysql55_compat_patches():
    import re

    try:
        from django.db.backends.mysql.base import DatabaseWrapper

        # ── Patch 1: Version-check bypass ──────────────────────────────────
        # Spoof mysql_server_data so Django sees "8.0.11" instead of "5.5.20".
        _orig_server_data_descriptor = DatabaseWrapper.__dict__.get("mysql_server_data")

        class _SpoofedServerDataDescriptor:
            """
            Replaces DatabaseWrapper.mysql_server_data (a cached_property).
            Reports MySQL 8.0.11 to pass Django's minimum-version guard while
            leaving all other server metadata untouched.
            """
            def __set_name__(self, owner, name):
                self.attr_name = name

            def __get__(self, instance, owner):
                if instance is None:
                    return self
                cache = instance.__dict__
                key = getattr(self, "attr_name", "mysql_server_data")
                if key in cache:
                    return cache[key]
                real_data = _orig_server_data_descriptor.__get__(instance, owner)
                real_version = real_data.get("version", "")
                m = re.match(r"(\d+)\.(\d+)\.(\d+)", real_version)
                if m and int(m.group(1)) < 8:
                    real_data = dict(real_data)
                    real_data["version"] = "8.0.11"
                cache[key] = real_data
                return real_data

        spoof_desc = _SpoofedServerDataDescriptor()
        spoof_desc.attr_name = "mysql_server_data"
        DatabaseWrapper.mysql_server_data = spoof_desc

        # ── Patch 2: datetime(6) / time(6) → datetime / time ───────────────
        # MySQL 5.5 does not support fractional-second precision in column
        # type declarations.  Strip the precision suffix so that DDL is
        # valid on MySQL 5.5.
        original_data_types = DatabaseWrapper._data_types.copy()
        original_data_types["DateTimeField"] = "datetime"
        original_data_types["TimeField"] = "time"
        DatabaseWrapper._data_types = original_data_types

        print(
            "[TMS-COMPAT] MySQL 5.5 shims active: version spoofed to 8.0.11, "
            "datetime(6)/time(6) downgraded to datetime/time. "
            "Upgrade MySQL to 8.0+ and remove tourism_system/__init__.py shim."
        )

    except ImportError:
        # Django may not yet be set up (e.g., very early import); safe to skip.
        pass


_apply_mysql55_compat_patches()
