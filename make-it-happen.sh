#!/bin/bash
#
# To run the command in debug mode, run it as:
# $ DEBUG=1 ./make-it-happen.sh command
#
# To use a different location for binary-dist, run it as:
# $ BINARY_DIST_URI=new_uri ./make-it-happen.sh command
#
# To add a new command to this script, add a 'command_COMMANDNAME' function.
# To publish the command in the general help,
# add a 'help_text_COMMANDNAME' variable with the text for that command.
# To add a detailed help for the new command add
# a 'help_COMMANDNAME' function.
#
# If 'help_text_COMMANDNAME' variable is missing, the command will not be
# advertised by the help commabd.
#
# If 'help_COMMANDNAME' function is missing the command will not have a
# detailded help text.
#
# Import shared code.
BRINK_FOLDER=~/chevah/brink/
. ${BRINK_FOLDER}/functions.sh

# URI from where to download python binary distribution.
if [ "$BINARY_DIST_URI" = "" ]; then
    BINARY_DIST_URI=http://binary.chevah.com/production
fi
PYTHON_URI=${BINARY_DIST_URI}/python
AGENT_URI=${BINARY_DIST_URI}/agent

ALL_PYTHON_BINARY_DIST="\
    python2.5-aix-ppc64 \
    python2.5-hpux-ia64 \
    python2.5-osx104-ppc \
    python2.5-rhel4-ppc64 \
    python2.5-rhel4-x64 \
    python2.5-rhel4-x86 \
    python2.5-rhel5-x64 \
    python2.5-rhel5-x86 \
    python2.5-rhel6-x64 \
    python2.5-rhel6-x86 \
    python2.5-sles11-x64 \
    python2.5-sles11-x86 \
    python2.5-solaris10-x86 \
    python2.5-ubuntu1004-x64 \
    python2.5-ubuntu1004-x86 \
    python2.5-ubuntu1204-x64 \
    python2.5-ubuntu1204-x86 \
    python2.7-ubuntu1004-x64 \
    python2.7-ubuntu1004-x86 \
    python2.7-ubuntu1204-x64 \
    python2.7-ubuntu1204-x86 \
    python2.5-windows-x86 \
    "

ALL_AGENT_BINARY_DIST="\
    agent-1.5-aix51-ppc \
    agent-1.5-aix53-ppc64 \
    agent-1.5-hpux-ia64 \
    agent-1.5-rhel4-ppc64 \
    agent-1.5-rhel4-x86 \
    agent-1.5-rhel5-x86 \
    agent-1.5-rhel6-x86 \
    agent-1.5-sles11-x86 \
    agent-1.5-solaris10-x86 \
    agent-1.5-solaris10-sparc64 \
    agent-1.5-ubuntu1004-x86 \
    agent-1.5-windows-x86 \
    "

PHANTOMJS_X86="phantomjs-1.4.1-ubuntu1004-x86"
PHANTOMJS_X64="phantomjs-1.4.1-ubuntu1004-x64"

EXTRA_LIBRARIES="\
    pyopenssl/pyOpenSSL-0.13 \
    pycrypto/pycrypto-2.3 \
    pysqlite/pysqlite-2.6.3 \
    python-setproctitle/python-setproctitle-1.1.4.dev0 \
    "

ALL_REPOS=`ls -1 ~/chevah/ | grep -v tmp`

PROG=$0
DIST_FOLDER='dist'
BUILD_FOLDER='build'
CACHE_FOLDER=${BRINK_FOLDER}/cache

# Get default values from main paver script.
pushd ${BRINK_FOLDER} > /dev/null
    ./paver.sh get_default_values
    if [ "$?" -ne 0 ]; then
        exit 1
    fi

    PYTHON_VERSION=`cut -d' ' -f 2 DEFAULT_VALUES`
    OS=`cut -d' ' -f 3 DEFAULT_VALUES`
    ARCH=`cut -d' ' -f 4 DEFAULT_VALUES`
    TIMESTAMP=`date +'%Y%m%d'`
    rm DEFAULT_VALUES
popd > /dev/null


LOCAL_PYTHON_BINARY_DIST="$PYTHON_VERSION-$OS-$ARCH"
INSTALL_FOLDER=$PWD/${BUILD_FOLDER}/$LOCAL_PYTHON_BINARY_DIST
PYTHON_BIN=$INSTALL_FOLDER/bin/python
PYTHON_BUILD_FOLDER="$PYTHON_VERSION-$OS-$ARCH"

LOCAL_AGENT_BINARY_DIST="agent-1.5-$OS-$ARCH"
AGENT_BUILD_FOLDER="agent-1.5-$OS-$ARCH"


# Compile and install all Python extra libraries.
command_build_python_extra_libraries() {
    # Update Python config Makefile to use the python that we have just
    # created.
    makefile=$INSTALL_FOLDER/lib/$PYTHON_VERSION/config/Makefile
    makefile_orig=$INSTALL_FOLDER/lib/$PYTHON_VERSION/config/Makefile.orig
    execute cp $makefile $makefile_orig
    sed "s#^prefix=.*#prefix= $INSTALL_FOLDER#" $makefile_orig > $makefile

    for library in $EXTRA_LIBRARIES ; do
        # Library is in the form pyopenssl/PyOpenssl-2.4.5
        version_folder=${library#*/}
        target_folder=${BUILD_FOLDER}/$version_folder

        execute rm -rf $target_folder
        execute cp -r src/$library $target_folder
        execute pushd $target_folder
            if [ -f setup.cfg ] ; then
                echo "include_dirs=$INSTALL_FOLDER/include" >> setup.cfg
                echo "library_dirs=$INSTALL_FOLDER/lib" >> setup.cfg
            fi
            execute $PYTHON_BIN setup.py install
        execute popd
    done
    execute mv $makefile_orig $makefile
}


help_text_build_python="Create the Python binaries for current OS."
command_build_python() {
    build 'python' 'Python-2.5.6.chevah' ${PYTHON_BUILD_FOLDER}
    build 'sqlite' 'SQLite-3.7.10' ${PYTHON_BUILD_FOLDER}
    command_build_python_extra_libraries

    execute pushd ${BUILD_FOLDER}/${PYTHON_BUILD_FOLDER}
        # Clean the build folder.
        execute mkdir -p lib/config
        safe_move include lib/config
        safe_move share lib/config
        safe_move pysqlite2-doc lib/config
        # Move all bin to lib/config
        safe_move bin lib/config
        execute mkdir bin
        # Copy back python binary
        execute cp lib/config/bin/$PYTHON_VERSION bin/python
    execute popd

    make_dist $PYTHON_VERSION ${PYTHON_BUILD_FOLDER}
}


help_text_build_agent=\
"Create the Agent binaries for current OS."
command_build_agent() {
    build 'regina' 'Regina-REXX-3.5' ${AGENT_BUILD_FOLDER}
    build 'rexxre' 'RexxRe-1.0.1' ${AGENT_BUILD_FOLDER}
    build 'rxsock' 'RxSock-1.4.chevah' ${AGENT_BUILD_FOLDER}
    build 'curl' 'curl-7.25.0' ${AGENT_BUILD_FOLDER}
    build '.' 'md5sum' ${AGENT_BUILD_FOLDER}
    build 'putty' 'putty-0.61.chevah' ${AGENT_BUILD_FOLDER}

    execute pushd ${BUILD_FOLDER}/${AGENT_BUILD_FOLDER}
        # Clean the build folder.
        execute mkdir -p lib/config
        safe_move etc lib/config
        safe_move share lib/config
        safe_move include lib/config
    execute popd

    make_dist 'agent' ${AGENT_BUILD_FOLDER}
}


#
# Test the newly created Python binary dist.
#
help_text_test_python=\
"Run a quick test for the Python from build."
command_test_python() {
    test_file='test_python_binary_dist.py'
    execute mkdir -p build/
    execute cp src/chevah-python-test/${test_file} build/
    execute pushd build
    execute ./$LOCAL_PYTHON_BINARY_DIST/bin/python ${test_file}
    execute popd
}


help_text_get_python=\
"Download Python binary distribution."
help_get_python() {
    echo "usage: get_python [PYTHON_VERSION OS-ARCH]"
    echo ""
    echo "When no arguments are provided, it will download default Python "
    echo "version for current OS."
}
command_get_python() {

    if [ $# -eq 0 ]; then
        python_get_list=${LOCAL_PYTHON_BINARY_DIST}

    elif [ $# -ne 2 ]; then
        help_get_python
        exit 1
    else
        python_get_list="$1-$2"
    fi

    mkdir -p ${CACHE_FOLDER}
    pushd ${CACHE_FOLDER}
        echo "Getting Python..."
        for build_folder in $python_get_list
        do
            get_binary_dist ${build_folder} $PYTHON_URI
        done
    popd
}


help_text_get_agent=\
"Download Agent binaries."
command_get_agent() {

    if [ $# -eq 0 ]; then
        agent_get_list=${LOCAL_AGENT_BINARY_DIST}

    elif [ $# -ne 1 ]; then
        help_get_python
        exit 1
    else
        agent_get_list="agent-1.5-$1"
    fi

    mkdir -p ${CACHE_FOLDER}
    pushd ${CACHE_FOLDER}
        echo "Getting agent..."
        for build_folder in $agent_get_list
        do
            get_binary_dist ${build_folder} $AGENT_URI
        done
    popd
}


help_text_remove_dependencies=\
"Remove python binary dist build dependencies"
command_remove_dependencies() {
    remove_dependencies
}

help_text_install_dependencies=\
"Install python binary dist build dependencies"
command_install_dependencies() {
    install_dependencies
}


#
# Download and extract a binary distribution.
#
get_binary_dist() {
    dist_name=$1
    base_uri=$2

    tar_gz_file=${dist_name}.tar.gz
    tar_file=${dist_name}.tar

    # Get and extract Python.
    rm -rf $dist_name
    rm -f $tar_gz_file
    rm -f $tar_file
    execute wget ${base_uri}/${tar_gz_file}
    execute gunzip $tar_gz_file
    execute tar -xf $tar_file
    rm -f $tar_gz_file
    rm -f $tar_file
}


get_phantomjs() {
    # Only get phantomjs on Ubuntu.
    if [ $OS != 'ubuntu*' ]; then
        return
    fi
    if [ $ARCH = 'x86' ]; then
        phantom_file=$PHANTOMJS_X86
    elif [ $ARCH = 'x64' ]; then
        phantom_file=$PHANTOMJS_X64
    else
        return
    fi

    echo "Getting $phantom_file..."
    tar_file=${phantom_file}.tar
    rm -rf phantomjs
    rm -f $tar_file
    execute wget $BINARY_DIST_URI/other/phantomjs/$tar_file
    execute tar -xf $tar_file
    execute mv $phantom_file phantomjs
}


help_text_buildslave_update=\
"Command to be executed on buildslaves for updating the state."
command_buildslave_update() {

    pushd ~/chevah/deps
        git pull origin master
        command_get
    popd
}


help_text_delete_local_branches=\
"Delete all merged local branches."
command_delete_local_branches(){
    pushd ~/chevah > /dev/null
    for repo in $ALL_REPOS; do
        pushd $repo > /dev/null
        echo "Cleaning local for $repo"
        git fetch
        BRANCHES=`git branch --merged | grep -v '^\*' \
            | grep -v master | grep -v production`
        git branch -d $BRANCHES
        popd > /dev/null
    done
    popd > /dev/null
}


help_text_delete_remote_branches=\
"Delete all merged remote branches."
command_delete_remote_branches(){
    pushd ~/chevah > /dev/null
    for repo in $ALL_REPOS; do
        pushd $repo > /dev/null
        echo "Cleaning remote for $repo"
        git fetch origin
        git remote prune origin
        BRANCHES=`git branch -r --merged master \
            | grep -v master | grep -v production`
        for branch in $BRANCHES; do
            remote=${branch%%/*}
            branch_name=${branch#*/}
            git push $remote :$branch_name
        done
        popd > /dev/null
    done
    popd > /dev/null
}


# Check status for all repositories.
help_text_code_status=\
"Check local repositories status."
command_code_status() {
    pushd ~/chevah > /dev/null
    for repo in $ALL_REPOS; do
        pushd $repo >> /dev/null
            echo "Checking $repo"
            git status -s
            git stash list
        popd >> /dev/null
    done
    popd > /dev/null
}


help_text_code_pull=\
"Pull all remote repositories."
command_code_pull() {
    pushd ~/chevah >> /dev/null
    for repo in $ALL_REPOS; do
        pushd $repo >> /dev/null
            echo "Pulling $repo..."
            git pull --all
        popd >> /dev/null
    done
    popd >> /dev/null
}


help_text_code_push=\
"Push all remote repositories."
command_code_push() {
    pushd ~/chevah >> /dev/null
    for repo in $ALL_REPOS; do
        pushd $repo >> /dev/null
            echo "Pushing $repo to origin..."
            git push --all origin
        popd >> /dev/null
    done
    popd >> /dev/null
}


help_text_code_release=\
"Create a release tag for current repository."
help_code_release() {
    echo "code_release VERSION [PAST_COMMIT]"
    echo ""
    echo "VERSION     - The name of the version to mark as released."
    echo "PAST_COMMIT - The hash for a past commit to mark."
    echo "              By default, it will use the latest commit."
    echo ""
    echo ""
    echo "This will create a tag containing information about dependency"
    echo "repositories."
}
command_code_release() {
    version=$1
    if [ "$version" = "" ]; then
        echo "Please pass the release number."
        echo
        help_code_release
        exit 1
    fi

    commit=$2

    # Get brink revision.
    pushd ~/chevah/brink >> /dev/null
        brink=`git rev-parse master`
    popd >> /dev/null

    message="Release version $version.\n\nbrink(master): \
        $brink"
    git tag -a $version $commit -m "$(echo -e "$message")"
    echo "Tag created for $version"
}


help_text_clean=\
"Clean the build and running environemnt."
command_clean() {
    rm -rf ${DIST_FOLDER}
    rm -rf ${BUILD_FOLDER}
    rm -rf ${CACHE_FOLDER}
}


# Launch the whole thing.
select_command $@
