"""Non-destructive MySQL -> SQLite migration helper.

Run this while the old MySQL DATABASE_URL is supplied explicitly. The script
backs up the source database with mysqldump when available, copies all model
tables through SQLAlchemy, then applies the requested menu cleanup. It never
deletes or alters the MySQL source.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, MetaData, Table, select

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main():
    source_url = os.getenv('SOURCE_MYSQL_DATABASE_URL')
    if not source_url or not source_url.startswith('mysql+'):
        raise SystemExit('Set SOURCE_MYSQL_DATABASE_URL=mysql+pymysql://... before running.')

    target = ROOT / 'data' / 'smart_food_court.sqlite3'
    target.parent.mkdir(parents=True, exist_ok=True)
    backup = ROOT / 'data' / 'mysql_pre_migration.sql'
    mysql_dump = shutil.which('mysqldump')
    if mysql_dump:
        subprocess.run([
            mysql_dump, '--single-transaction', '--routines', '--triggers',
            source_url.rsplit('/', 1)[-1].split('?')[0], '--result-file', str(backup)
        ], check=True)
    else:
        print('WARNING: mysqldump not found; continuing without a SQL dump backup.')

    from app import create_app
    from app.extensions import db
    from app.models import MenuItem

    source = create_engine(source_url)
    app = create_app('default')
    with app.app_context():
        db.create_all()
        source_meta = MetaData()
        source_meta.reflect(bind=source)
        destination = db.engine
        with destination.begin() as connection:
            for table_name in source_meta.sorted_tables:
                destination_table = Table(table_name.name, MetaData(), autoload_with=destination)
                rows = [dict(row) for row in source.execute(select(table_name)).mappings()]
                if rows:
                    connection.execute(destination_table.insert(), rows)
        db.session.commit()
        MenuItem.query.filter(MenuItem.name.ilike('%peri%peri%french%fries%')).delete(synchronize_session=False)
        db.session.commit()
    print(f'Migrated to {target}')
    print(f'MySQL source was not modified. Backup: {backup if backup.exists() else "not created"}')


if __name__ == '__main__':
    main()
