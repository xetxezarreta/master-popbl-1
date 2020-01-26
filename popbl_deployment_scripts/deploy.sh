#!/bin/bash
set -x

function usage {
    echo "Usage: deploy app"
    exit 1
}

function send_cfn_signal {
    echo send_cfn_signal $1 $2
    if [ "$1" = "error" ]; then
        if (($2 != 0)); then
            echo sending error signal
            /opt/aws/bin/cfn-signal --stack $AWS_STACKNAME --resource $AWS_RESOURCE --region $AWS_REGION -e 2   
            exit 1
        fi
    fi

    if [ "$1" = "success" ]; then
        echo send success signal
        /opt/aws/bin/cfn-signal --stack $AWS_STACKNAME --resource $AWS_RESOURCE --region $AWS_REGION
    fi
}

function dir_exits {

    if [ -d "$1" ]; then
        return 0
    else
        return 1
    fi

}



# CONST

APP_GIT=https://gitlab.danz.eus/ivan.valdesi/servicesapp_popbl.git
HONEY_GIT=https://github.com/xetxezarreta/docker-elk.git
VAULT_CLI=/home/ec2-user/popbl_vault/vault.sh

# Read Arg

TARGET="$1" 

case "$TARGET" in
    
    haproxy)
        pushd /home/ec2-user
        git clone $APP_GIT
        send_cfn_signal error $?
        cd servicesapp_popbl
        cp dot_env_example .env
        docker-compose up -d haproxy
        send_cfn_signal error $?
        popd
        send_cfn_signal success
        
    ;;

    app)
        pushd /home/ec2-user
        git clone $APP_GIT
        send_cfn_signal error $?

        $VAULT_CLI get -e username rabbitmq RABBITMQ_USER
        $VAULT_CLI get -e password rabbitmq RABBITMQ_PASSWORD

        $VAULT_CLI get -f ca_certificate rabbitmq servicesapp_popbl/cert_rabbitmq/client/ca_certificate.pem
        $VAULT_CLI get -f client_certificate rabbitmq servicesapp_popbl/cert_rabbitmq/client/client_certificate.pem
        $VAULT_CLI get -f client_key rabbitmq servicesapp_popbl/cert_rabbitmq/client/client_key.pem

        $VAULT_CLI get -f ca_certificate rabbitmq servicesapp_popbl/cert_rabbitmq/server/ca_certificate.pem
        $VAULT_CLI get -f server_certificate rabbitmq servicesapp_popbl/cert_rabbitmq/server/server_certificate.pem
        $VAULT_CLI get -f server_key rabbitmq servicesapp_popbl/cert_rabbitmq/server/server_key.pem

        cd servicesapp_popbl
        cp dot_env_example .env
        docker-compose up -d rabbitmq
        send_cfn_signal error $?
        sleep 30  
        docker-compose up -d auth delivery machine order payment logger consul
        send_cfn_signal error $?
        popd
        send_cfn_signal success

    ;;

    honey)
        pushd /home/ec2-user
        # Check if git repo exits
        if  dir_exits ./docker-elk; then 
            echo git already exits
        else 
            git clone $HONEY_GIT
            send_cfn_signal error $?
        fi

        pushd docker-elk
        git checkout elastic
        cd sb-honey
        docker-compose up -d
        send_cfn_signal error $?
        popd 

        popd
        send_cfn_signal success
    ;;

    sniffer)
        pushd /home/ec2-user
        # Check if git repo exits
        if  dir_exits ./docker-elk; then 
            echo git already exits
        else 
            git clone $HONEY_GIT
            send_cfn_signal error $?
        fi

        pushd docker-elk
        git checkout elastic
        cd sb-sniffer
        docker-compose up -d
        send_cfn_signal error $?
        popd 

        popd
        send_cfn_signal success
    ;;

    ml)
        pushd /home/ec2-user
        # Check if git repo exits
        if  dir_exits ./docker-elk; then 
            echo git already exits
        else 
            git clone $HONEY_GIT
            send_cfn_signal error $?
        fi

        pushd docker-elk
        git checkout elastic
        cd sb-ml
        docker-compose up -d
        send_cfn_signal error $?
        popd 

        popd
        send_cfn_signal success
    ;;


    *)
        usage
    ;;
    
esac
