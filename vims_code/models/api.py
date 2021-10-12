import datetime
import os
from abc import abstractmethod
from typing import Any, List
from urllib.parse import urlparse

import psycopg2
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.gevent import GeventScheduler
from gevent.threading import Lock
from psycopg2 import extras
from psycopg2._psycopg import connection, cursor

lock = Lock()


def using_connection(connection):
    def real_deco(func):
        def wrapper(*args, **kwargs):
            try:
                res = func(*args, **kwargs)
                connection.restart_level = 0
                return res
            except (psycopg2.errors.AdminShutdown, psycopg2.OperationalError):
                print("restarting...")
                connection.restart()
                return func(*args, **kwargs)

        return wrapper

    return real_deco


class DatabaseConnectionExecutor(object):
    @abstractmethod
    def call_query_multi(self, query: str, var_list: []):
        pass

    @abstractmethod
    def call_query(self, query: str, params: Any, has_return=False):
        pass

    @abstractmethod
    def call_select(self, query: str, params: Any) -> {}:
        pass

    @abstractmethod
    def call_function(self, function, params) -> Any:
        pass

    @abstractmethod
    def call_procedure(self, procedure, params):
        pass


class DatabaseConnection(DatabaseConnectionExecutor):
    def __init__(self, dns, lazy_acquire_func=None, *more, **kwargs):
        if "connection" in kwargs:
            self.conn = kwargs['connection']
        else:
            self.conn = connection(dns, *more)
        self.lazy_acquire = lazy_acquire_func
        self.busy: bool = False
        self.current_statement = ""
        self.execute_date: datetime.datetime = None
        self.release_date: datetime.datetime = None
        self.opening_date: datetime.datetime = datetime.datetime.now()
        self.pid = self.get_backend_pid()
        self.cur: cursor = self.conn.cursor(cursor_factory=extras.RealDictCursor)
        self.simple_cur: cursor = self.conn.cursor()
        self.restart_level = 0

    def __getattr__(self, item):
        return getattr(self.conn, item)

    @classmethod
    def use_conn(cls, conn: connection):
        return cls(None, connection=conn)

    def reconnect(self, num_of_restarts=5):
        def real_deco(func):
            def wrapper(*args, **kwargs):
                try:
                    res = func(*args, **kwargs)
                    self.restart_level = 0
                    return res
                except psycopg2.errors.AdminShutdown:
                    if self.restart_level < num_of_restarts:
                        self.restart()
                        return func(*args, **kwargs)
                    else:
                        raise

            return wrapper

        return real_deco

    # @reconnect
    def restart(self):
        dsn = self.conn.dsn
        try:
            self.conn.close()
        except:
            pass
        self.conn = connection(dsn)

    # @reconnect
    def call_query_multi(self, query: str, var_list: []):
        # cur: cursor = self.cursor()
        self.current_statement = f"multi: {query}"
        try:
            self.cur.executemany(query, var_list)
        finally:
            self.current_statement = ""
            # cur.close()

    # @reconnect
    def call_query(self, query: str, params: Any, has_return=False):
        # cursor_factory=extras.RealDictCursor
        # cur: cursor = self.cursor()
        # self.cur.cursor_factory = None
        self.current_statement = query
        self.execute_date = datetime.datetime.now()
        try:
            self.simple_cur.execute(query, params)
            if has_return:
                return self.simple_cur.fetchone()[0]
        finally:
            self.current_statement = ""
            # self.cur.cursor_factory = extras.RealDictCursor
            # cur.close()

    # @reconnect
    def call_select(self, query: str, params: Any) -> {}:
        # cur: cursor = self.cursor(cursor_factory=extras.RealDictCursor)
        self.current_statement = query
        self.execute_date = datetime.datetime.now()
        try:
            self.cur.execute(query, params)
            return self.cur.fetchall()
        finally:
            self.current_statement = ""
            # cur.close()

    # @reconnect
    def call_function(self, function, params) -> Any:
        # cur: cursor = self.cursor()
        self.current_statement = function
        self.execute_date = datetime.datetime.now()
        try:
            if isinstance(params, dict):
                sql_params = ",".join([el for el in map(lambda k: str(k) + " => %(" + str(k) + ")s", params)])
                self.cur.execute("select %s(%s)" % (function, sql_params), params)
                return self.cur.fetchone()[0]
            else:
                self.cur.callproc(function, params)
                return self.cur.fetchone()[0]

        finally:
            self.current_statement = ""
            # cur.close()

    # @reconnect
    def call_procedure(self, procedure, params):
        cur: cursor = self.cursor()
        self.current_statement = procedure
        try:
            self.cur.callproc(procedure, params)
        finally:
            self.current_statement = ""
            self.cur.close()


class DatabaseConnectionPool(DatabaseConnectionExecutor):
    dns: str = ""

    @staticmethod
    def generate_dns(db_name, user, pwd, host, port) -> str:
        return f"dbname={db_name} user={user} password={pwd} host={host} port={port}"

    @classmethod
    def by_connection_string(cls, connection_string):
        # connection_string = "postgresql://postgres:postgres@localhost/postgres"
        result = urlparse(connection_string)
        user = result.username
        pwd = result.password
        db_name = result.path[1:]
        host = result.hostname
        port = result.port
        min_number = os.environ.get('MIN_CONNECTIONS', 1)
        return cls(db_name=db_name, user=user, pwd=pwd, host=host, port=port, min_number=min_number)

    def __init__(self, db_name: str, user: str, pwd: str, host: str, port: int, min_number: int,
                 size_of_pool: int = None,
                 keepalive_time: int = 60):
        self.dns = self.generate_dns(db_name, user, pwd, host, port)
        self.size_of_pool = size_of_pool
        self.keepalive_time = keepalive_time
        self.min_number = min_number
        self.restart_level = 0
        self.connection_pool = {}
        self.start_pool()

    def restart_pool(self):
        lock.acquire()
        try:
            self.stop_pool()
            self.start_pool()
        finally:
            lock.release()

    def stop_pool(self):
        pid_list = [pid for pid in self.connection_pool]
        for pid in pid_list:
            self.remove(self.connection_pool[pid])
        self.start_pool()

    def start_pool(self):
        for i in range(0, self.min_number):
            connection = DatabaseConnection(self.dns)
            self.connection_pool[connection.get_backend_pid()] = connection

    def acquire(self) -> DatabaseConnection:
        for connection_pid in self.connection_pool:
            if not self.connection_pool[connection_pid].busy:
                self.connection_pool[connection_pid].busy = True
                return self.connection_pool[connection_pid]
        new_connection: DatabaseConnection = DatabaseConnection(self.dns)
        self.connection_pool[new_connection.get_backend_pid()] = new_connection
        new_connection.busy = True
        return new_connection

    def init_connection(self, conn: DatabaseConnection):

        pass

    def lazy_acquire(self):
        # new_connection: DatabaseConnection = DatabaseConnection(dns=None,
        #                                                        lazy_acquire_func=self.init_connection)
        return self

    def release(self, connection: DatabaseConnection):
        connection.busy = False
        connection.current_statement = ""
        connection.release_date = datetime.datetime.now()

    def remove(self, connection: DatabaseConnection):
        try:
            connection.close()
        except Exception as ex:
            print(ex)
        del self.connection_pool[connection.pid]
        del connection

    def get_busy(self):
        return len([_ for _ in filter(lambda el: self.connection_pool[el].busy == 1, self.connection_pool)])

    busy = property(get_busy)

    def get_opened(self):
        return len(self.connection_pool)

    opened = property(get_opened)

    def call_query_multi(self, query: str, var_list: []):
        conn = self.acquire()
        try:
            conn.call_query_multi(query, var_list)
        finally:
            self.release(conn)

            # @reconnect

    def call_query(self, query: str, params: Any, has_return=False):
        conn = self.acquire()
        try:
            res = conn.call_query(query, params, has_return)
        finally:
            self.release(conn)
        return res

    # @reconnect
    def call_select(self, query: str, params: Any) -> {}:
        conn = self.acquire()
        try:
            res = conn.call_select(query, params)
        finally:
            self.release(conn)
        return res

    # @reconnect
    def call_function(self, function, params) -> Any:
        conn = self.acquire()
        try:
            res = conn.call_function(function, params)
        finally:
            self.release(conn)
        return res

    # @reconnect
    def call_procedure(self, procedure, params):
        conn = self.acquire()
        try:
            conn.call_procedure(procedure, params)
        finally:
            self.release(conn)


def using_pool(connection_pool: DatabaseConnectionPool):
    def real_deco(func):
        def wrapper(*args, **kwargs):
            try:
                res = func(*args, **kwargs)
                connection_pool.restart_level = 0
                return res
            except psycopg2.errors.AdminShutdown:
                print("restarting...")
                connection_pool.restart_pool()
                return func(*args, **kwargs)

        return wrapper

    return real_deco


def session_killer(pool: DatabaseConnectionPool):
    while len(pool.connection_pool) > pool.min_number:
        conn: DatabaseConnection = conn
        p = pool.connection_pool.items()
        if len(pool.connection_pool) > pool.min_number:
            if conn.busy == 0 and conn.release_date - datetime.datetime.now() > datetime.timedelta(pool.keepalive_time):
                pool.remove(conn)


def start_session_scheduler(pool: DatabaseConnectionPool):
    scheduler = BackgroundScheduler()
    scheduler.add_job(session_killer, 'interval', args=(pool,), seconds=15)
    scheduler.start()  # g is the greenlet that runs the scheduler loop
    return scheduler


class DbTypes:
    bigint = "bigint"
    text = "text"
    integer = "integer"
    timestamp = "timestamp"

    @staticmethod
    def varchar(num):
        return f"varchar({num})"


class Field(object):
    def __init__(self, field_name, field_type, default=None, not_null=False, auto_increment=False) -> object:
        self.field_name = field_name
        self.field_type = field_type
        self.default = default
        self.not_null = not_null
        self.auto_increment = auto_increment

    def get_sequence_name(self, table_name):
        return f"{table_name}_{self.field_name}_seq"

    def create_sequence(self, table_name, schema_name):
        if self.auto_increment:
            return f"create sequence if not exists {schema_name}.{self.get_sequence_name(table_name)};\n"
        else:
            return ""

    def generate_sql(self, table_name, schema_name):

        sql = f"{self.field_name} {self.field_type}"
        if self.auto_increment:
            sql += f" default nextval('{schema_name}.{self.get_sequence_name(table_name)}')"
        else:
            if self.default:
                sql += f" default {self.default}"
        if self.not_null:
            sql += f" not null"
        return sql


class Index(object):
    def __init__(self, name, fields: List[str], unique=False):
        self.name = name
        self.fields: List[str] = fields
        self.unique = unique

    def generate_sql(self, table_name, schema_name):
        field_script = ', '.join(self.fields)
        sql = f"create {'unique ' if self.unique else ''}index {self.name} " \
              f"\n\ton {schema_name}.{table_name} ({field_script});"
        return sql


class DatabaseTable(object):
    fields = []
    field_list: List[Field] = List[Field]
    index_list: List[Index] = []
    schema: str = os.environ.get('DB_SCHEMA', 'e_code')
    primary_key_field = "id"
    table_name: str = None

    def __init__(self, conn: DatabaseConnectionExecutor):
        self.conn = conn

    def f_name(self, f):

        return f[0] if type(f) == list else f

    def _multi_set(self, vals: [], unique_keys=None, no_id=False):

        field_names = list(map(lambda el: el.field_name, self.field_list))
        field_names = field_names[1:] if no_id else field_names
        for f in self.field_list:
            print(f'%(arr_{f.field_name})s::{f.field_type}[]')
        params = [f'%(arr_{f.field_name})s::{f.field_type}[]' for f in self.field_list]
        params = params[1:] if no_id else params
        unique_fields = ','.join(unique_keys) if unique_keys else self.primary_key_field
        pk = self.primary_key_field
        # arr = [list(x.values())[0] for x in a]
        # arr2 = [list(x.values())[1] for x in a]
        param_dict = {}
        for f in self.field_list:
            param_dict[f'arr_{f.field_name}'] = [val.get(f.field_name) for val in vals]

        field_update_row = ",\n".join(f"{f} =  excluded.{f}" for f in field_names)
        # con.call_select("select * from unnest(%(arr)s, %(arr2)s)", dict(arr=arr,arr2=arr2))

        # field_param_row = ", ".join("%(" + self.f_name(f) + ")s" for f in self.fields[1:])
        id_row_script = f"coalesce({pk}, nextval('{self.schema}.{self.table_name}_id_seq'::regclass))," if not no_id else ""

        sql = f'''insert into {self.schema}.{self.table_name} ({','.join(field_names)})
                                        (select {id_row_script} {','.join(field_names if no_id else field_names[1:])}                                                
                                           from unnest({','.join(params)}) with ordinality as a({','.join(field_names)}))
                                             on conflict ({unique_fields}) do
                                          update set {field_update_row}
                                       returning {self.primary_key_field}
        '''
        print(sql)
        rows = self.conn.call_select(sql, param_dict)
        return rows

    def _set(self, **kwargs):
        pk = self.primary_key_field
        field_row = f'{", ".join(map(lambda f: f.field_name, self.field_list))}'
        field_param_row = ", ".join("%(" + f.field_name + ")s" for f in self.field_list[1:])
        field_update_row = ",\n".join(f"{f.field_name} = %({f.field_name})s" for f in self.field_list[1:])
        sql = f"""
              insert into {self.schema}.{self.table_name} ({field_row})
              values(coalesce(%({pk})s, nextval('{self.schema}.{self.table_name}_id_seq'::regclass)), {field_param_row})
                 on conflict ({pk}) do
                 update set {field_update_row}
                 returning {pk}
        """
        return self.conn.call_query(sql, kwargs, True)

    def _select(self, **kwargs):
        order_by = kwargs.get('order_by', "")
        if 'order_by' in kwargs:
            del kwargs['order_by']
        table_filter = "\nand ".join(f"({f} = %({f})s or %({f})s is null)"
                                     for f in kwargs.keys())
        sql = f"""select * 
                    from {self.schema}.{self.table_name}
                   where 1=1
                     and {table_filter} """ + order_by

        return self.conn.call_select(sql, kwargs)

    def _delete(self, field_name, field_value):
        sql = f"delete from {self.schema}.{self.table_name} where {field_name} = %({field_name})s"
        self.conn.call_query(sql, {field_name: field_value})

    def _multi_delete(self, **kwargs):
        condition = "and ".join([k + " = %(" + k + ")s" for k in kwargs])
        sql = f"delete from {self.schema}.{self.table_name} where {condition}"
        self.conn.call_query(sql, kwargs)

    def set_by_dict(self, input_dict: {}):
        params = {}
        for field in self.field_list:
            params[field.field_name] = input_dict.get(field.field_name)
        return self._set(**params)

    @classmethod
    def generate_create_script(cls):
        # field_sql =
        primary_key_script = f"alter table {cls.schema}.{cls.table_name} add primary key ({cls.primary_key_field});"
        seq_script = "".join(map(lambda f: f.create_sequence(cls.table_name, cls.schema), cls.field_list))
        field_script = ",\n\t".join(map(lambda f: f.generate_sql(cls.table_name, cls.schema), cls.field_list))
        sql = f"""create table {cls.schema}.{cls.table_name}(\n\t{field_script}\n);"""
        sql += "\n"
        sql += primary_key_script + "\n"
        indexes_script = "\n".join(map(lambda i: i.generate_sql(cls.table_name, cls.schema), cls.index_list))
        sql += indexes_script
        if seq_script != "":
            sql = seq_script + "\n" + sql
        return sql

        # create unique index table_name_name_uindex on table_name (name);

    def create(self):
        sql = self.generate_create_script()
        print(sql)
        self.conn.call_query(sql, {})
        self.conn.commit()
