#!/bin/bash


function usage {
    echo "Usage: vault.sh open | close | get"
    exit 1
}


function get_usage {
    echo "Usage: vault.sh get (-e env_var <name>) ( -f filedir )"
    exit 1
}



function get {
    
    OPTION="$1"
    KEY="$2"
    SERCRET="$3"
    TARGET="$4"
    
    case "$OPTION" in
        
        -e)
            export "$TARGET"="$(vault read -field "$KEY" -tls-skip-verify cubbyhole/"$SERCRET")"
        ;;
        
        -f)
            echo "$(vault read -field "$KEY" -tls-skip-verify cubbyhole/"$SERCRET")" > "$TARGET"
        ;;
        
        *)
            usage
        ;;
        
        
    esac
    
}


# Read Arg

case "$1" in
    
    open)
        
    ;;
    
    close)
        
    ;;
    
    get)
        # option key sercret file|env
        get $2 $3 $4 $5
    ;;
    
    *)
        usage
    ;;
    
esac


