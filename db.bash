#!/bin/bash -ex

function usage() {
    echo "usage:"
    echo
    echo "  db.bash <create|run|stop>"
    echo
    echo "where"
    echo
    echo "  create -  create empty local MySQL database using upgrade scripts"
    echo "  run     - start MySQL in a Docker container (must follow 'create')"
    echo "  stop    - stop and remove MySQL Docker container"
    echo
}

## The absolute path of the directory in which this file resides.
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
DATA_DIR="$SCRIPT_DIR/data"
UPGRADE_DIR="$SCRIPT_DIR/upgrade"
MYSQL_VERSION=8.4

## API process credentials for MySQL authentication.
## Also determines the root MySQL password.
DB_NAME="elite102"
DB_USERNAME="elite102"
DB_PASSWORD="password"

## Docker container names
CREATE_CONTAINER_NAME="elite102-mysql-create"
RUN_CONTAINER_NAME="elite102-mysql"

function create() {
    ## Ensure database upgrade and data directories exist.
    mkdir -p "$DATA_DIR"
    mkdir -p "$UPGRADE_DIR"

    ## Stop MySQL and remove existing data files.
    (sudo docker stop  $CREATE_CONTAINER_NAME $RUN_CONTAINER_NAME || true)
    (sudo docker rm -v $CREATE_CONTAINER_NAME $RUN_CONTAINER_NAME || true)
    sleep 1s
    sudo rm -Rf "$DATA_DIR/*"

    ## Start a local MySQL server, which re-creates the on-disk data files.
    sudo docker run \
        --name "$CREATE_CONTAINER_NAME" \
        --publish 3306:3306 \
        --detach \
        --volume "$DATA_DIR:/var/lib/mysql" \
        --env MYSQL_ROOT_PASSWORD=$DB_PASSWORD \
        --env MYSQL_PASSWORD=$DB_PASSWORD \
        --env MYSQL_USER=$DB_USERNAME \
        --env MYSQL_DATABASE=$DB_NAME \
        mysql:$MYSQL_VERSION

    ## Wait until MySQL is running.
    until sudo docker exec -i "$CREATE_CONTAINER_NAME" sh -c \
            'MYSQL_PWD=$MYSQL_ROOT_PASSWORD mysql -e "select 1" "$DB_NAME"'; do
        sleep 1s
        done

    ## Create the database schema using the upgrade scripts.
    for f in $(ls "$UPGRADE_DIR"); do
        sudo docker exec -i "$CREATE_CONTAINER_NAME" sh -c \
            'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql "$MYSQL_DATABASE"' \
            < "$UPGRADE_DIR/$f"
        done;

    echo You may optionally connect to the database and configure it manually.
    echo host: localhost
    echo port: 3306
    echo db:   $DB_NAME
    echo user: $DB_USERNAME
    echo pass: $DB_PASSWORD
    read -n1 -s -r -p $'Then press any key to continue.\n' key

    ## Stop the container we used to create the data.
    sudo docker stop  $CREATE_CONTAINER_NAME
    sudo docker rm -v $CREATE_CONTAINER_NAME
}

function run() {
    if [ ! -d "$DATA_DIR/mysql" ]; then
        echo "No data found in $DATA_DIR.  Run the "create" command first."
        exit 1
        fi

    ## Start a local MySQL server, using state in the ./data directory.
    if sudo docker ps --format 'table {{.Names}}' | grep "$RUN_CONTAINER_NAME"; then
        echo "MySQL already running in container $RUN_CONTAINER_NAME."
    elif sudo docker ps --all --format 'table {{.Names}}' | grep "$RUN_CONTAINER_NAME"; then
        echo "Starting MySQL in stopped Docker container $RUN_CONTAINER_NAME..."
        sudo docker start "$RUN_CONTAINER_NAME"
    else
        echo "Creating MySQL Docker container $RUN_CONTAINER_NAME..."
        sudo docker run \
            --name "$RUN_CONTAINER_NAME" \
            --publish 3306:3306 \
            --detach \
            --volume "$DATA_DIR:/var/lib/mysql" \
            --env "MYSQL_PWD=$DB_PASSWORD" \
            mysql:$MYSQL_VERSION
        fi

    ## Wait until MySQL is running.
    until sudo docker exec -i $RUN_CONTAINER_NAME mysql -e "select 1" $DB_NAME; do
        sleep 1s
        done

    echo "    MySQL container is ready."
}

function stop() {
    echo "Stopping $RUN_CONTAINER_NAME..."
    (sudo docker stop  $RUN_CONTAINER_NAME || true)
    echo "    Done."

    echo "Removing $RUN_CONTAINER_NAME..."
    (sudo docker rm -v $RUN_CONTAINER_NAME || true)
    echo "    Done."
}

if [ "$#" -ne 1 ]; then
    usage
    exit 1
    fi

case "$1" in
    "create" ) create  ;;
    "run"    ) run     ;;
    "stop"   ) stop    ;;
    *        ) usage; exit 1
    esac
