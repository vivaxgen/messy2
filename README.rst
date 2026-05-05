
MESSy/2 - Molecular Epidemiology and Surveillance Support System 2
==================================================================

This is based on litestar / litestar-pulse addon library.

Installation
------------

Run the following command to install MESSy/2:

.. code-block:: bash

    "${SHELL}" <(curl -L https://raw.githubusercontent.com/vivaxgen/messy2/main/install.sh)

Setting up and running the server
---------------------------------

To set up the server, run the following command:

.. code-block:: bash

    INST_DIR/bin/activate
    cd $VVG_BASEDIR/instances
    mkdir messy2.localhost
    cd messy2.localhost
    mkdir db
    uv run litestar-pulse messy2-mgr db-init
    uv run litestar-pulse messy2-mgr user-passwd --username sysadm --password NEW_PASSWORD

This will create a new instance of MESSy/2 with the name "messy2.localhost" and initialize the database.

To run the server, use the following command:

.. code-block:: bash

    uv run litestar-pulse run --port 7979

