/*

Opens a msys environment console and installs prerequisites needed
to build the sources if necessary.

Usage: cscript.exe SCRIPT_FILE

By default, the environment is installed in the current user's profile
(home) folder, under subfolder 'chevah'.

The profile is updated via /etc/profile.d/chevah.sh

When the script is run for the first time, it will download the git
archive from the binary server, unpack it to 'chevah' folder, set the
required environment variables and opens a bash console from git.
The following times when the script is run, it will see that git was
already installed and only the bash console will be opened.

When non running in DEBUG mode, the UI/UX is bad as it will just confirm
that it will download and extract, but there is no visual progress,
and it can take a lot of time to download or extract.
*/

// Set to 1 to enable debug mode.
var DEBUG = 0
// Localtion from where the environemnt archive is downloaded.
var BINARIES_ROOT_URL = 'http://binary.chevah.com/production/msys-console'
// A string indetifying the version of the environmet.
// To keep it simple, it's set to the archive from which the env is created.
var ENV_VERSION = 'git-windows-x86-2.11.0.chevah1.zip'

/*
If CHEVAH_FOLDER_NAME is a relative path, then it will
be relative to user's home folder.

If CHEVAH_FOLDER_NAME is an absolute path, then that path is used.
*/
var CHEVAH_FOLDER_NAME = 'chevah'

var RESULT = {
    'OK': 0,
    'DOWNLOAD_ERROR': 1,
    'ERROR': 2
}

var StreamTypeEnum = { adTypeBinary : 1 }
var SaveOptionsEnum = { adSaveCreateOverWrite : 2 }

var Shell = new ActiveXObject('WScript.Shell')
var Filesystem = new ActiveXObject('Scripting.FileSystemObject')

function log(str) {
    WScript.Echo(str)
}

function exit(code) {
    WScript.Quit(code)
}



/*
Downloads a file from specified 'url' and save it to 'file'
*/
function download_file(url, file) {
    log("Downloading file '" + url + "' to '" + file + "'")

    var request = new ActiveXObject('Microsoft.XMLHTTP')

    request.open('GET', url, false)
    request.send()

    if (request.Status == 200) {
        var stream = new ActiveXObject('ADODB.Stream')

        try {
            stream.Open()
            stream.Type = StreamTypeEnum.adTypeBinary
            stream.Write(request.ResponseBody)
            stream.Position = 0
            stream.SaveToFile(file, SaveOptionsEnum.adSaveCreateOverWrite)
            stream.Close()
        }
        catch (e) {
            log("--> Cannot write file, error : '" + e.log + "'")
            return RESULT.DOWNLOAD_ERROR
        }
    }
    else {
        log('--> Cannot download file, error : ' + request.StatusText +
            '(' + request.Status + ')')

        return RESULT.DOWNLOAD_ERROR
    }

    return RESULT.OK
}

/*
Unzip the archive located at path 'archive' and extract all
content in an already existing folder  at 'folder' path.
*/
function unzip(archive, folder) {
    log("Unpacking archive '" + archive + "' to '" + folder + "'")

    var app = new ActiveXObject('Shell.Application')

    var src = app.NameSpace(archive).Items()
    var dst = app.NameSpace(folder)

    //16 - Respond with "Yes to All" for any dialog box that is displayed.
    dst.CopyHere(src, 16)

    return RESULT.OK
}

function create_folder(folder) {
    if (Filesystem.FolderExists(folder) == false) {
        Filesystem.CreateFolder(folder)
    }

    return RESULT.OK
}

function delete_folder(folder) {
    if (Filesystem.FolderExists(folder) == true) {
        Filesystem.DeleteFolder(folder, true)
    }

    return RESULT.OK
}

/*
Gets value of a specified environment variable
*/
function get_env_var(variable) {
    var value = Shell.ExpandEnvironmentStrings('%' + variable + '%')
    return value
}


/*
Sets value of a specified environment variable
*/
function set_process_env_var(variable, value) {
    var variables = Shell.Environment('Process')

    variables.item(variable) = value

    return RESULT.OK
}

/*
Checks if environment need to be updated, and do it.
*/
function check_for_update(archive, chevah_root) {

    var temp_dir = Filesystem.BuildPath(chevah_root, 'temp')
    var git_dir =  Filesystem.BuildPath(chevah_root, 'git')
    var version_file = Filesystem.BuildPath(git_dir, 'version.txt')
    var url = BINARIES_ROOT_URL + '/' + ENV_VERSION
    var temp = Filesystem.BuildPath(temp_dir, ENV_VERSION)

    if (Filesystem.FileExists(version_file)) {
        var ForReading = 1
        var stream = Filesystem.OpenTextFile(version_file, ForReading)
        var lines = stream.ReadAll()
        stream.Close()

        if (lines == ENV_VERSION) {
            // No need to update.
            return RESULT.OK
        }
    }

    create_folder(temp_dir)

    rc = download_file(url, temp)
    if (rc != RESULT.OK) {
        return rc
    }

    delete_folder(git_dir)
    rc = unzip(temp, chevah_root)
    if (rc != RESULT.OK) {
        return rc
    }

    create_bash_profile(chevah_root)

    return RESULT.OK
}


/*
Creates a profile for the installation.

If the profile already exists it will return without changing the
file.
*/
function create_bash_profile(chevah_root) {
    var profile_file = chevah_root + '\\git\\etc\\profile.d\\chevah.sh'
    var ForWriting = 2

    stream = Filesystem.OpenTextFile(profile_file, ForWriting, true)
    try {
        stream.Write('#\n# Generated by Chevah msys-console.js script.\n#\n')
        stream.Write('\n# Git enhanced prompt.\n')
        stream.Write('PS1=\'\\[\\033[1;36m\\]\\u@\\h:\\[\\033[0m\\]')
        stream.Write('\\[\\033[1;35m\\]\\w\\[\\033[0m\\]\\[\\033[1;32m\\]')
        stream.Write('$(__git_ps1)\\[\\033[0m\\] \\$ \'\n')
        stream.Write('\n# Use visible colors for LS.\n')
        stream.Write('LS_COLORS="$LS_COLORS:di=01;35:"\n')
        stream.Write('export LS_COLORS\n')
        stream.Write('\n# A few common aliases.\n')
        stream.Write('alias paver=./paver.sh\n')
        stream.Close()
    } catch (e) {
        log("--> Cannot generate profile, error : '" + e.log + "'")
        return RESULT.ERROR
    }

    return RESULT.OK
}


/*
Main script logic
*/
function run() {
    var rc = 0
    var chevah_root

    var drive = Filesystem.GetDriveName(CHEVAH_FOLDER_NAME)
    var profile_folder = Shell.ExpandEnvironmentStrings('%userprofile%')

    if (drive.length > 0) {
        chevah_root = CHEVAH_FOLDER_NAME
    } else {
        chevah_root = Filesystem.BuildPath(profile_folder, CHEVAH_FOLDER_NAME)
    }

    create_folder(chevah_root)
    check_for_update(ENV_VERSION, chevah_root)

    Shell.CurrentDirectory = chevah_root

    // Add chevah/git/bin to the current process path.
    var path = get_env_var('PATH')
    set_process_env_var('PATH', chevah_root + '\\git\\bin' + path)

    var cmd = '\"' + chevah_root + '\\git\\bin\\bash.exe\" -i -l'

    rc = Shell.Run(cmd, 1, false)
}

var rc = 0

if (DEBUG) {
    // The script needs to be run with cscript in order to have all the output
    // redirected to the console and not the GUI, so we enforce that here.
    var filename = Filesystem.GetFileName(WScript.FullName).toLowerCase()

    if (filename == 'wscript.exe') {
        var path = WScript.ScriptFullName
        var cmd = '%comspec% /k cscript \"' + path + '\"'

        Shell.Run(cmd)

        exit(0)
    }
}

rc = run()

exit(rc)
