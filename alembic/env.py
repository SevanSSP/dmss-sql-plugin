from alembic import context
from sqlalchemy import create_engine
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from plugin.config import Config
from plugin.models import Base

# this is the Alembic Config object, which provides access to the values within the .ini file in use.
config = context.config

# add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata


def get_url():
    """Return the database URL"""
    # Get url from alembic config
    url = config.get_main_option("sqlalchemy.url")

    # url is None if not set in test fixture using config.set_main_option('sqlalchemy.url', ...)
    # (as the url variable in alembic.ini is empty)
    if not url:
        # In development and production mode get database URL from environmental variable
        return Config().SQLALCHEMY_DATABASE_URI

    # use url specified using config.set_main_option('sqlalchemy.url', ...)
    return url


def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table" and reflected:
        return False
    elif type_ == 'foreign_key_constraint' and reflected:
        return False
    elif name and 'id' in name and reflected:
        return False
    else:
        return True


def run_migrations_offline():
    """Run migrations in 'offline' mode.
    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.
    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_url()
    context.configure(
        compare_type=True,
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        include_schemas=True,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.
    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = create_engine(get_url())
    def process_revision_directives(context, revision, directives):
        if not directives[0].upgrade_ops.ops:
            directives[:] = []
            print('No changes in schema detected.')

    with connectable.connect() as connection:
        context.configure(
            compare_type=True,
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            include_object=include_object,
            process_revision_directives=process_revision_directives

        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
