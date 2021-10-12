from sqlalchemy import Table, text

from vims_code.db.schema import metadata
from sqlalchemy.ext.asyncio import AsyncConnection


class SqlBase:
    metadata = metadata

    def __init__(self, conn: AsyncConnection):
        self.conn = conn


class SqlTable(SqlBase):
    table_name = None
    table: Table = None

    def __init__(self, conn: AsyncConnection):
        super().__init__(conn)

    async def get(self, id):
        sql = self.table.select().where(self.table.c.id == id)
        res = (await self.conn.execute(sql)).fetchone()
        return dict(res) if res else None

    async def set(self, **kwargs):
        field_names = set([c.name for c in list(self.table.c)])
        for k in list(kwargs.keys()):
            if k not in field_names:
                del kwargs[k]
        if not kwargs.get("id"):
            try:
                del kwargs["id"]
            except KeyError:
                pass

            return (await self.create(**kwargs))['id']
        else:
            res = await self.update(**kwargs)
            return res['id'] if res else None

    async def create(self, **kwargs):
        sql = self.table.insert().values(**kwargs).returning(self.table.c.id)
        return (await self.conn.execute(sql)).fetchone()

    async def update(self, **kwargs):
        sql = (
            self.table.update()
                .where(self.table.c.id == kwargs.get("id"))
                .values(
                **kwargs
            )
                .returning(self.table.c.id)
        )
        res = (await self.conn.execute(sql)).fetchone()
        return res


    async def delete(self, id):
        sql = self.table.delete().where(self.table.c.id == id)
        await self.conn.execute(sql)

    async def _multi_set(self, vals: [], unique_keys=None, no_id=False):
        table_name = self.table.name
        field_names = [f.name for f in self.table.c]
        field_list = [f for f in self.table.c]
        field_names = field_names[1:] if no_id else field_names
        for f in field_list:
            print(f'(:arr_{f.name}))::{f.type}[]')
        params = [f'(:arr_{f.name})::{f.type}[]' for f in field_list]
        params = params[1:] if no_id else params
        unique_fields = ','.join(unique_keys) if unique_keys else 'id'
        pk = 'id'
        # arr = [list(x.values())[0] for x in a]
        # arr2 = [list(x.values())[1] for x in a]
        param_dict = {}
        for f in field_list:
            param_dict[f'arr_{f.name}'] = [val.get(f.name) for val in vals]

        field_update_row = ",\n".join(f"{f} =  excluded.{f}" for f in field_names)
        # con.call_select("select * from unnest(%(arr)s, %(arr2)s)", dict(arr=arr,arr2=arr2))

        # field_param_row = ", ".join("%(" + self.f_name(f) + ")s" for f in self.fields[1:])
        id_row_script = f"coalesce({pk}, nextval('{self.table.schema}.{self.table.name}_id_seq'::regclass))," if not no_id else ""

        sql = f'''insert into {self.table.schema}.{self.table.name} ({','.join(field_names)})
                                        (select {id_row_script} {','.join(field_names if no_id else field_names[1:])}                                                
                                           from unnest({','.join(params)}) with ordinality as a({','.join(field_names)}))
                                             on conflict ({unique_fields}) do
                                          update set {field_update_row}
                                       returning id
        '''

        rows = (await self.conn.execute(text(sql), param_dict)).fetchall()
        return [dict(r) for r in rows]

    async def call_select(self, sql, params):
        rows = (await self.conn.execute(sql, parameters=params)).fetchall()
        return [dict(r) for r in rows]
