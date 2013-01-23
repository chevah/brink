#!/bin/bash
#
# Chevah Repository Downloader.
#
# This script is designed to create the initial clone of all repositories
# used by Chevah project.
#
# It will be downloaded outside of repositories and should not depend on
# any other file.
#

BASE_FOLDER=~

READ_ONLY_REMOTE_REPO_URI='http://172.20.0.1/git/'
REMOTE_REPO_URI='git@git.chevah.com:'


DEV_REPOS="brink agent utils compat empirical server"

BUILDSLAVE_REPOS="brink infrastructure"


# Get all requested repositories.
create_repositories() {
    echo "Using remote repository: $REMOTE_REPO_URI"

    repos=$@
    cd $BASE_FOLDER
    mkdir chevah
    cd chevah

    for repo in $repos; do
        remote_repo=${REMOTE_REPO_URI}${repo}.git
        git clone $remote_repo
    done
}


help_text_dev=\
"Clone repositories required for a development setup."
command_dev() {
    if [ "x$1" != "x" ]; then
        REMOTE_REPO_URI=$1
    fi
    create_repositories $DEV_REPOS
}


help_text_buildslave=\
"Clone repositories required for running buildslave."
command_buildslave(){
    if [ "x$1" != "x" ]; then
        REMOTE_REPO_URI=$1
    else
        REMOTE_REPO_URI=$READ_ONLY_REMOTE_REPO_URI
    fi
    create_repositories $BUILDSLAVE_REPOS
}


##############################################################################
# Copy of functions from functions.sh so that this script will not
# depend on other files.
# This code should be manually updated from time to time.
##############################################################################


help_text_help=\
"Show help for a command."
command_help() {
    local command=$1
    local help_command="help_$command"
    # Test to see if we have a valid help method, otherwise call
    # the general help.
    type $help_command &> /dev/null
    if [ $? -eq 0 ]; then
        $help_command
    else
        echo "Commands are:"
        for help_text in `compgen -A variable help_text_`
        do
            command_name=${help_text#help_text_}
            echo -e "  $command_name\t\t${!help_text}"
        done
    fi
}


select_command() {
    local command=$1
    shift
    case $command in
        "")
            command_help
            exit 1
            ;;
        *)
            # Test to see if we have a valid command, otherwise call
            # the general help.

            call_command="command_$command"
            type $call_command &> /dev/null
            if [ $? -eq 0 ]; then
                $call_command $@
            else
                command_help
                echo ""
                echo "Unknown command: ${command}."
                exit 1
            fi
        ;;
    esac
}


# Launch the whole thing.
select_command $@
