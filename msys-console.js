/*

Opens a msys environment console and installs prerequisites needed
to build the sources if necessary.

Usage: cscript.exe SCRIPT_FILE

By default, prerequisites are installed in the current user's profile
(home) folder, under subfolder 'chevah'.

A .bash_profile file will be automatically created if it does not exist
and the PATH environment variable extended to include the binary folder
in the distribution.

When the script is run for the first time, it will download the git
archive from the binary server, unpack it to 'chevah' folder, set the
required environment variables and opens a bash console from git.
The following times when the script is run, it will see that git was
already installed and only the bash console will be opened.

To create the zip archive that is stored in the binary server :
- decompress Portable Git For Windows (https://git-scm.com/download/win)
- decompress wget binary and place it in Git\bin folder (
    https://eternallybored.org/misc/wget/)
- create a zip archive from git folder
- upload the zip archive to the server
- modify the archive name in this script

The whys:
---------

The `msysgit` which is bundled with Git for Windows does not include a package
manager (pacman) in our case. This is intentional:

https://github.com/git-for-windows/git/issues/397#issuecomment-140984199

Installing it manually does not work as well. Packages installed via pacman
are not seen by msysgit and viceversa.

Since `wget` is not part of the included distribution and paver relies on
wget to download specific files we need to include it ourselves.

The simplest solution for the moment is to include the Windows 32 bit binary
that it's linked above.

Later, we can fork the Git for Windows SDK and built it ourselves with an
included wget.

---

We cannot use `git-bash.exe` as the shell as it's handling of the input/output
clashes with python (readline) and nothing gets printed in the console once
Python shell/interpreter is executed.

There is a workaround by calling `winpty python` but this implies altering
paver and so far it looks like the most complicated option.

http://stackoverflow.com/questions/32597209/
*/

// Set to 1 to enable debug mode.
var DEBUG = 0

var BINARIES_ROOT_URL = 'http://binary.chevah.com/production/msys-console'

/*
If CHEVAH_FOLDER_NAME is a relative path, then it will
be relative to user's home folder.

If CHEVAH_FOLDER_NAME is an absolute path, then that path is used.
*/
var CHEVAH_FOLDER_NAME = 'chevah'

var SOURCE_ARCHIVE_NAME_RE = /git-windows-x86-.*\.zip/m

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
Force the script to be run with cscript and not wscript
*/
function force_cscript() {
    var filename = Filesystem.GetFileName(WScript.FullName).toLowerCase()

    if (filename == 'wscript.exe') {
        var path = WScript.ScriptFullName
        var cmd = '%comspec% /k cscript \"' + path + '\"'

        Shell.Run(cmd)

        exit(0)
    }
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
Gets profile (home) folder of current user
*/
function get_current_user_profile_folder() {
    var path = Shell.ExpandEnvironmentStrings('%userprofile%')

    return path
}

/*
Gets value of a specified environment variable
*/
function get_env_var(variable) {
    var value = Shell.ExpandEnvironmentStrings('%' + variable + '%')

    return value
}

/*
Gets current user temp folder
*/
function get_current_user_temp_folder() {
    var path = Shell.ExpandEnvironmentStrings('%temp%')

    return path
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
Checks if a newer version of a specified archive is available
*/
function archive_needs_update(archive, version_file) {
    if (Filesystem.FileExists(version_file)) {
        var ForReading = 1
        var stream = Filesystem.OpenTextFile(version_file, ForReading)

        var lines = stream.ReadAll()

        stream.Close()

        var result = SOURCE_ARCHIVE_NAME_RE.exec(lines)

        if (result[0] == archive) {
            return false
        }

    }

    return true
}

/*
Writes the version information to version.txt
*/
function write_version_to_file(archive, version_file) {
    var stream
    var lines = ''
    var ForReading = 1
    var ForWriting = 2

    if (Filesystem.FileExists(version_file)) {
        stream = Filesystem.OpenTextFile(version_file, ForReading)

        lines = stream.ReadAll()

        stream.Close()
    }

    stream = Filesystem.OpenTextFile(version_file, ForWriting, true)

    var pos = lines.search(SOURCE_ARCHIVE_NAME_RE)

    if (pos == -1) {
        lines = lines + archive + '\n'
        stream.Write(lines)
    } else {
        var result = SOURCE_ARCHIVE_NAME_RE.exec(lines)

        if (result[0] != archive) {
            lines = lines.replace(SOURCE_ARCHIVE_NAME_RE, archive)
            stream.Write(lines)
        }
    }

    stream.Close()

    return RESULT.OK
}

/*
Creates a .bash_profile file in the users home folder and adds
binary folder to the path.

If the profile already exists it will return without changing the
file.
*/
function create_bash_profile(home_folder, chevah_root) {
    var profile_file = home_folder + '\\.bash_profile'
    var ForWriting = 2

    if (Filesystem.FileExists(profile_file)) {
        return RESULT.OK
    }

    stream = Filesystem.OpenTextFile(profile_file, ForWriting, true)
    try {
        stream.Write('# Generated by Chevah msys-console.js script.\n')
        stream.Write('PATH="$PATH:' + chevah_root + '\\git\\bin"\n')
        stream.Write('\n# Git enhanced prompt.\n')
        stream.Write('PS1=\'\\[\\033[1;36m\\]\\u@\\h:\\[\\033[0m\\]')
        stream.Write('\\[\\033[1;35m\\]\\w\\[\\033[0m\\]\\[\\033[1;32m\\]')
        stream.Write('$(__git_ps1)\\[\\033[0m\\] \\$ \'\n')
        stream.Write('\n# Use visible colors for LS.\n')
        stream.Write('LS_COLORS="$LS_COLORS:di=01;35:"\n')
        stream.Write('export LS_COLORS\n')
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
    var profile_folder = get_current_user_profile_folder()

    if (drive.length > 0) {
        chevah_root = CHEVAH_FOLDER_NAME
    } else {
        chevah_root = Filesystem.BuildPath(profile_folder, CHEVAH_FOLDER_NAME)
    }

    create_folder(chevah_root)

    var temp_dir = Filesystem.BuildPath(chevah_root, 'temp')
    create_folder(temp_dir)

    var version_file = Filesystem.BuildPath(chevah_root, 'version.txt')

    var archives = ['git-windows-x86-2110.zip']

    for (var i in archives) {
        var needs_update = archive_needs_update(archives[i], version_file)

        if (needs_update) {
            var url = BINARIES_ROOT_URL + '/' + archives[i]
            var temp = Filesystem.BuildPath(temp_dir, archives[i])

            rc = download_file(url, temp)
            if (rc != RESULT.OK) {
                return rc
            }

            rc = unzip(temp, chevah_root)
            if (rc != RESULT.OK) {
                return rc
            }

            rc = write_version_to_file(archives[i], version_file)
            if (rc != RESULT.OK) {
                return rc
            }
        }
    }

    Shell.CurrentDirectory = chevah_root

    // Add chevah/git/bin to the current process path.
    var path = get_env_var('PATH')
    set_process_env_var('PATH', chevah_root + '\\git\\bin' + path)
    // Create a .bash_profile if not already present.
    create_bash_profile(profile_folder, chevah_root)

    var cmd = '\"' + chevah_root + '\\git\\bin\\bash.exe\" -i -l'

    rc = Shell.Run(cmd, 1, false)
}

var rc = 0

if (DEBUG) {
    // The script needs to be run with cscript in order to have all the output
    // redirected to the console and not the GUI, so we enforce that here.
    force_cscript()
}

rc = run()

exit(rc)
