/*

Installs prerequisites needed to build the sources

Usage: cscript.exe make-windows-environment.js

By default, prerequisites are installed in the current user's profile
(home) folder, under subfolder "chevah".

To create the zip archive that is stored in the binary server :
- install git using the installer
- install msys using the installer
- install msys-wget package under msys and copy the files to git folder
- create a zip archive from git folder
- upload the zip archive to the server
- modify the archive name in this script

*/

var BINARIES_ROOT_URL = 'http://binary.chevah.com/production/msys-git'

// If CHEVAH_FOLDER_NAME is a relative path, then it will
// be relative to user's home folder.
// If CHEVAH_FOLDER_NAME is an absolute path, then that path is used.
//var CHEVAH_FOLDER_NAME = "c:\\chevah"
var CHEVAH_FOLDER_NAME = 'chevah'

var SOURCE_ARCHIVE_NAME_RE = /msys-git-windows-x86-.*\.zip/m

var RESULT = {
    'OK': 0,
    'DOWNLOAD_ERROR': 1
}

var StreamTypeEnum = { adTypeBinary : 1 }
var SaveOptionsEnum = { adSaveCreateOverWrite : 2 }

var Shell = new ActiveXObject('WScript.Shell')
var FSO = new ActiveXObject('Scripting.FileSystemObject')

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
    var filename = FSO.GetFileName(WScript.FullName).toLowerCase()

    if (filename == 'wscript.exe') {
        var path = WScript.ScriptFullName
        var cmd = '%comspec% /k cscript \"" + path + "\"'

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
    if (FSO.FolderExists(folder) == false) {
        FSO.CreateFolder(folder)
    }

    return RESULT.OK
}

function delete_folder(folder) {
    if (FSO.FolderExists(folder) == true) {
        FSO.DeleteFolder(folder, true)
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
    if (FSO.FileExists(version_file)) {
        var ForReading = 1
        var stream = FSO.OpenTextFile(version_file, ForReading)

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

    if (FSO.FileExists(version_file)) {
        stream = FSO.OpenTextFile(version_file, ForReading)

        lines = stream.ReadAll()

        stream.Close()
    }

    stream = FSO.OpenTextFile(version_file, ForWriting, true)

    var pos = lines.search(SOURCE_ARCHIVE_NAME_RE)

    if (pos == -1) {
        lines = lines + archive + '\n'
        stream.Write(lines)
    }
    else {
        var result = SOURCE_ARCHIVE_NAME_RE.exec(lines)

        if (result[0] != archive) {
            lines = lines.replace(SOURCE_ARCHIVE_NAME_RE, archive)
            stream.Write(lines)
        }
    }

    stream.Close()

    return RESULT.OK
}

function convert_path_to_mingw_format(path) {
    path = '/' + path
    path = path.replace(':', '')
    path = path.replace(/\\/g, '/')

    return path
}

/*
Main script logic
*/
function run() {
    var rc = 0
    var chevah_root

    var drive = FSO.GetDriveName(CHEVAH_FOLDER_NAME)

    if (drive.length > 0) {
        chevah_root = CHEVAH_FOLDER_NAME
    }
    else {
        chevah_root = FSO.BuildPath(get_current_user_profile_folder(),
                                CHEVAH_FOLDER_NAME)
    }

    create_folder(chevah_root)

    var mingw_root = FSO.BuildPath(chevah_root, 'mingw')
    create_folder(mingw_root)

    var temp_dir = FSO.BuildPath(chevah_root, 'temp')
    create_folder(temp_dir)

    var version_file = FSO.BuildPath(mingw_root, 'version.txt')

    var archives = ['msys-git-windows-x86-21052013.zip']

    for (var i in archives) {
        var needs_update = archive_needs_update(archives[i], version_file)

        if (needs_update) {
            var url = BINARIES_ROOT_URL + '/' + archives[i]
            var temp = FSO.BuildPath(temp_dir, archives[i])

            rc = download_file(url, temp)
            if (rc != RESULT.OK) {
                return rc
            }

            rc = unzip(temp, mingw_root)
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

    var path = get_env_var('PATH')
    set_process_env_var('PATH', mingw_root + '\\git\\bin' + path)

    var mingw_chevah_root = convert_path_to_mingw_format(chevah_root)

    var cmd = '\"' + mingw_root + '\\git\\bin\\bash.exe\" -c \"PATH=$PATH:' +
            mingw_chevah_root + '/mingw/git/bin bash -i -l\"'

    rc = Shell.Run(cmd, 1, false)
}

var rc = 0

// The script needs to be run with cscript in order to have all the output
// redirected to the console and not the GUI, so we enforce that here.
force_cscript()

rc = run()

exit(rc)

