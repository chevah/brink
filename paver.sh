#!/usr/bin/env bash
#
# Do not modify this file inside the branch.
# Only modify this script in deps/chevah-paver-lib folder.
# Inside a branch, paver.sh should be a symlink or copy (on windows).
#
# Copyright (c) 2011 Adi Roiban.
# See LICENSE for details.
# Helper script for running paver on Unix systems.
# It will write the default values into 'DEFAULT_VALUES' file.

# Set default locale.
# We use C (alias for POSIX) for having a basic default value and
# to make sure we explictly convert all unicode values.
export LANG='C'
export LANGUAGE='C'
export LC_ALL='C'
export LC_CTYPE='C'
export LC_COLLATE='C'
export LC_MESSAGES='C'
export PATH=$PATH:'/sbin:/usr/sbin'


# Global variable for arbitrary return value from functions.
RESULT=''

# Initialize PROJECT_ROOT and later fix it.
PROJECT_ROOT=`pwd`

WAS_PYTHON_JUST_INSTALLED=0


clean_build() {
    # Shortcut for clear since otherwise it will depend on python
    echo "Removing ${BUILD_FOLDER}..."
    rm -rf ${BUILD_FOLDER}
    echo "Removing dist..."
    rm -rf ${DIST_FOLDER}
    echo "Removing publish..."
    rm -rf 'publish'
    echo "Cleaning project temporary files..."
    rm -f DEFAULT_VALUES
    rm -f pavement_lib.py*
}


find_project_root() {
    PROJECT_ROOT=${PROJECT_ROOT%chevah*}
    PROJECT_ROOT=${PROJECT_ROOT}chevah
}


write_default_values() {
    echo ${BUILD_FOLDER} ${PYTHON_VERSION} ${OS} ${ARCH} > DEFAULT_VALUES
}


# Set default Python version.
# It can be overwritten by specific operating system versions.
PYTHON_BIN="/bin/python"

PYTHON_VERSION="python2.5"
PYTHON_LIB="/lib/${PYTHON_VERSION}/"

ARCH='x86'

OS=`uname -s | tr '[:upper:]' '[:lower:]'`

if [ "${OS%mingw*}" = "" ] ; then

    OS='windows'
    ARCH='x86'
    PYTHON_BIN="/lib/python.exe"
    PYTHON_LIB="/lib/Lib/"

elif [ "${OS}" = "sunos" ] ; then

    OS="solaris"
    ARCH=`uname -p`	
    VERSION=`uname -r`

    if [ "$ARCH" = "i386" ] ; then
        ARCH='x86'
    fi

    if [ "$VERSION" = "5.10" ] ; then
        OS="solaris10"
    fi

elif [ "${OS}" = "aix" ] ; then

    release=`oslevel`
    case $release in
        5.1.*)
            OS='aix51'
            ARCH='ppc'
            ;;
        *)
            # By default we go for AIX 5.3 on PPC64
            OS='aix53'
            ARCH='ppc64'
        ;;
    esac

elif [ "${OS}" = "hp-ux" ] ; then

    OS="hpux"
    ARCH=`uname -m`

elif [ "${OS}" = "linux" ] ; then

    ARCH=`uname -m`

    if [ -f /etc/redhat-release ] ; then
        # Careful with the indentation here.
        # Make sure rhel_version does not has spaces before and after the
        # number.
        rhel_version=`\
            cat /etc/redhat-release | sed s/.*release\ // | sed s/\ .*//`
        # RHEL4 glibc is not compatible with RHEL 5 and 6.
        rhel_major_version=${rhel_version%.*}
        if [ "$rhel_major_version" = "4" ] ; then
            OS='rhel4'
        elif [ "$rhel_major_version" = "5" ] ; then
            OS='rhel5'
        elif [ "$rhel_major_version" = "6" ] ; then
            OS='rhel6'
        else
            echo 'Unsuported RHEL version.'
            exit 1
        fi
    elif [ -f /etc/SuSE-release ] ; then
        sles_version=`\
            grep VERSION /etc/SuSE-release | sed s/VERSION\ =\ //`
        if [ "$sles_version" = "11" ] ; then
            OS='sles11'
        else
            echo 'Unsuported SLES version.'
            exit 1
        fi
    elif [ -f /etc/lsb-release ] ; then
        release=`lsb_release -sr`
        case $release in
            '10.04' | '10.10' | '11.04' | '11.10')
                OS='ubuntu1004'
            ;;
            '12.04' | '12.10' | '13.04' | '13.10')
                OS='ubuntu1204'
                PYTHON_VERSION="python2.5"
                PYTHON_LIB="/lib/${PYTHON_VERSION}/"
            ;;
            *)
                echo 'Unsuported Ubuntu version.'
                exit 1
            ;;
        esac
	    
    elif [ -f /etc/slackware-version ] ; then

        # For Slackware, for now we use Ubuntu 10.04.
        # Special dedication for all die hard hackers like Ion.
	    OS="ubuntu1004"

    elif [ -f /etc/debian_version ] ; then
        OS="debian"

    fi

elif [ "${OS}" = "darwin" ] ; then
    osx_version=`sw_vers -productVersion`
    osx_major_version=${osx_version%.*}
	if [ "$osx_major_version" = "10.4" ] ; then
		OS='osx104'
	else
		echo 'Unsuported OS X version.'
		exit 1
	fi
	
	osx_arch=`uname -m`
	if [ "$osx_arch" = "Power Macintosh" ] ; then
		ARCH='ppc'
	else
		echo 'Unsuported OS X architecture.'
		exit 1
	fi
else
    echo 'Unsuported operating system.'
    exit 1
fi


# Fix arch names.
if [ "$ARCH" = "i686" ] ; then
    ARCH='x86'

fi
if [ "$ARCH" = "i386" ] ; then
    ARCH='x86'
fi

if [ "$ARCH" = "x86_64" ] ; then
    ARCH='x64'
fi


find_project_root

BOOTSTRAP_PATH=${PROJECT_ROOT}/brink
DIST_FOLDER='dist'
BUILD_FOLDER="build-${OS}-${ARCH}"
PYTHON_FOLDER=${BUILD_FOLDER}
PYTHON_DIST="${PYTHON_VERSION}-${OS}-${ARCH}"
PYTHON_BIN="${BUILD_FOLDER}${PYTHON_BIN}"
PYTHON_LIB="${BUILD_FOLDER}${PYTHON_LIB}"
export PYTHONPATH=${PYTHON_FOLDER}
PYTHON_DISTRIBUTABLE=${BOOTSTRAP_PATH}/cache/${PYTHON_DIST}
PAVEMENT_LIB_PATH=${BOOTSTRAP_PATH}/pavement_commons.py


if [ "$1" = "clean" ] ; then
    clean_build
    exit 0
fi


if [ "$1" = "get_default_values" ] ; then
    write_default_values
    exit 0
fi


# Chech that we have a pavement.py in the current dir.
# otherwise it means we are out of the branch.
if [ ! -e pavement.py ]; then
    echo 'No pavement.py file found in current folder.'
    echo 'Make sure you are running paver from a branch.'
    exit 1
fi

write_default_values


# Check that python dist was installed
if [ ! -s ${PYTHON_BIN} ]; then
    # Install python-dist since everthing else depends on it.
    echo "Bootstraping Python environment to ${PYTHON_FOLDER}..."
    mkdir -p ${PYTHON_FOLDER}

    # If we don't have a cached python distributable,
    # get one.
    if [ ! -d ${PYTHON_DISTRIBUTABLE} ]; then
        echo "Base Python environemt not found. Start downloading it..."
        pushd ${BOOTSTRAP_PATH}
        ./make-it-happen.sh get
        popd
    fi

    cp -R ${PYTHON_DISTRIBUTABLE}/* ${PYTHON_FOLDER}
    cp -r ${PYTHON_FOLDER}/lib/config/include ${PYTHON_FOLDER}/
    # Copy pywintypes25.dll as it is required by paver on windows.
    if [ "$OS" = "windows" ]; then
        cp -R ${PYTHON_DISTRIBUTABLE}/lib/pywintypes25.dll .
    fi

    WAS_PYTHON_JUST_INSTALLED=1
fi

# Always update paver ... at least until we have a stable buildsystem.
cp -RL ${BOOTSTRAP_PATH}/paver/paver ${PYTHON_LIB}
cp -RL ${BOOTSTRAP_PATH}/pip/pip ${PYTHON_LIB}
cp -RL ${BOOTSTRAP_PATH}/distribute/setuptools ${PYTHON_LIB}
cp -RL ${BOOTSTRAP_PATH}/distribute/distribute.egg-info ${PYTHON_LIB}
cp ${BOOTSTRAP_PATH}/distribute/pkg_resources.py ${PYTHON_LIB}/
cp ${BOOTSTRAP_PATH}/distribute/easy_install.py ${PYTHON_LIB}/

# Copy latest version of pavement_lib if we are not in the commons module.
# This is implemented using copy functionality since Windows does not support
# (or makes symlinking a bit complicated).
# Maybe we can add a condition and only use copy on Windows and symlinks on
# Unix.
current_root=`pwd`

echo "Update pavement_lib.py."
cp ${PAVEMENT_LIB_PATH} pavement_lib.py

if [ $WAS_PYTHON_JUST_INSTALLED -eq 1 ]; then
    ${PYTHON_BIN} -c 'from paver.tasks import main; main()' deps
    python_exit_code=$?
    if [ $python_exit_code -ne 0 ]; then
        echo 'Failed to run the inital "paver deps" command.'
        exit python__exit_code
    fi
fi

# Now that we have Python and Paver, let's call Paver
${PYTHON_BIN} -c 'from paver.tasks import main; main()' $@
python_exit_code=$?
exit $python_exit_code
