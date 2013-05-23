//******************************************************************************
// Outputs a message to the console
//******************************************************************************
function message(str) {
    WScript.Echo(str);
}

//******************************************************************************
// Exits from the script with provided return code
//******************************************************************************
function exit(code) {
    WScript.Quit(code);
}

//******************************************************************************
// Force the script to be run with cscript and not wscript
//******************************************************************************
function force_cscript() {
    var filename = g_fso.GetFileName(WScript.FullName).toLowerCase();

    if (filename == "wscript.exe") {
        var path = WScript.ScriptFullName;
        var cmd = "%comspec% /k cscript \"" + path + "\"";

        g_shell.Run(cmd);

        exit(0);
    }
}

//******************************************************************************
// Downloads a file from specified URL
//******************************************************************************
function download_file(url, file) {
    message("Downloading file '" + url + "' to '" + file + "'");

    var request = new ActiveXObject("Microsoft.XMLHTTP");

    // arg3 - async
    request.open("GET", url, false);
    request.send();

    if (request.Status == 200) {
        var adTypeBinary = 1;
        var adSaveCreateNotExist = 1;
        var adSaveCreateOverWrite = 2;

        var stream = new ActiveXObject("ADODB.Stream");

        try {
            stream.Open();
            stream.Type = adTypeBinary;
            stream.Write(request.ResponseBody);
            stream.Position = 0;
            stream.SaveToFile(file, adSaveCreateOverWrite);
            stream.Close();
        }
        catch (e) {
            message("--> Cannot write file, error : '" + e.message + "'");
            return g_errors.ERROR_DOWNLOAD;
        };
    }
    else {
        message("--> Cannot download file, error : '" + request.StatusText + "' (" + request.Status + ")");
        return g_errors.ERROR_DOWNLOAD;
    }

    return g_errors.E_OK;
}

//******************************************************************************
// Unzip an archive to a specified directory
//******************************************************************************
function unzip(archive, dir) {
    message("Unpacking archive '" + archive + "' to '" + dir + "'");

    var app = new ActiveXObject("Shell.Application");

    var src = app.NameSpace(archive).Items();
    var dst = app.NameSpace(dir);

    //16 - Respond with "Yes to All" for any dialog box that is displayed.
    dst.CopyHere(src, 16);

    return g_errors.E_OK;
}

//******************************************************************************
// Creates the directory if it doesn't exists
//******************************************************************************
function create_directory_if_not_exists(dir) {
    if (g_fso.FolderExists(dir) == false) {
        g_fso.CreateFolder(dir);
    }

    return g_errors.E_OK;
}

//******************************************************************************
// Deletes a directory is it exists
//******************************************************************************
function delete_directory_if_exists(dir) {
    if (g_fso.FolderExists(dir) == true) {
        g_fso.DeleteFolder(dir, true);
    }

    return g_errors.E_OK;
}

//******************************************************************************
// Gets profile (home) directory of current user
//******************************************************************************
function get_current_user_profile_dir() {
    var path = g_shell.ExpandEnvironmentStrings("%userprofile%");

    return path;
}

//******************************************************************************
// Gets value of a specified environment variable
//******************************************************************************
function get_env_var(variable) {
    var value = g_shell.ExpandEnvironmentStrings("%" + variable + "%");

    return value;
}

//******************************************************************************
// Gets current user temp directory
//******************************************************************************
function get_current_user_temp_dir() {
    var path = g_shell.ExpandEnvironmentStrings("%temp%");

    return path;
}

//******************************************************************************
// Sets value of a specified environment variable
//******************************************************************************
function set_process_env_var(variable, value) {
    var variables = g_shell.Environment("Process");

    variables.item(variable) = value;

    return g_errors.E_OK;
}

//******************************************************************************
// Checks if a newer version of a specified archive is available
//******************************************************************************
function archive_needs_update(archive, version_file) {
    if (g_fso.FileExists(version_file)) {
        var ForReading = 1;
        var stream = g_fso.OpenTextFile(version_file, ForReading);

        var lines = stream.ReadAll();

        stream.Close();

        var re = /msys-git-windows-x86-.*\.zip/m;

        var result = re.exec(lines);

        if (result[0] == archive) {
            return false;
        }

    }

    return true;
}

//******************************************************************************
// Writes the version information to version.txt
//******************************************************************************
function write_version_to_file(archive, version_file) {
    var stream;
    var lines = "";
    var ForReading = 1;
    var ForWriting = 2;

    if (g_fso.FileExists(version_file)) {
        stream = g_fso.OpenTextFile(version_file, ForReading);

        lines = stream.ReadAll();

        stream.Close();
    }

    stream = g_fso.OpenTextFile(version_file, ForWriting, true);

    var re = /msys-git-windows-x86-.*\.zip/m;

    var pos = lines.search(re);

    if (pos == -1) {
        lines = lines + archive + "\n";
        stream.Write(lines);
    }
    else {
        var result = re.exec(lines);

        if (result[0] != archive) {
            lines = lines.replace(re, archive);
            stream.Write(lines);
        }
    }

    stream.Close();

    return g_errors.E_OK;
}

//******************************************************************************
// Main script logic
//******************************************************************************
function run() {
    var rc = 0;

    var binaries_root_url = "http://binary.chevah.com/production/msys-git";

    var chevah_root = g_fso.BuildPath(get_current_user_profile_dir(), "chevah");
    create_directory_if_not_exists(chevah_root);

    var mingw_root = g_fso.BuildPath(chevah_root, "mingw");
    create_directory_if_not_exists(mingw_root);

    var temp_dir = g_fso.BuildPath(chevah_root, "temp");
    create_directory_if_not_exists(temp_dir);

    var version_file = g_fso.BuildPath(mingw_root, "version.txt");

    var archives = ['msys-git-windows-x86-21052013.zip'];

    for (var i in archives) {
        var needs_update = archive_needs_update(archives[i], version_file);

        if (needs_update) {
            var url = binaries_root_url + "/" + archives[i];
            var temp = g_fso.BuildPath(temp_dir, archives[i]);

            rc = download_file(url, temp);
            if (rc != g_errors.E_OK) {
                return rc;
            }

            rc = unzip(temp, mingw_root);
            if (rc != g_errors.E_OK) {
                return rc;
            }

            rc = write_version_to_file(archives[i], version_file);
            if (rc != g_errors.E_OK) {
                return rc;
            }
        }
    }

    g_shell.CurrentDirectory = chevah_root;

    var path = get_env_var("PATH");
    set_process_env_var("PATH", mingw_root + "\\git\\bin;" + path);

    var cmd = "\"" + mingw_root + "\\git\\bin\\bash.exe\" -c \"PATH=$PATH:~/chevah/mingw/git/bin bash -i -l\"";

    rc = g_shell.Run(cmd, 1, false);
}

//******************************************************************************
// Global stuff
//******************************************************************************
// error codes
var g_errors = {
    'E_OK'          : 0,
    'E_DOWNLOAD'    : 1
};

g_rc = 0;

var g_shell = new ActiveXObject("WScript.Shell");
var g_fso = new ActiveXObject("Scripting.FileSystemObject");

// the script needs to be run with cscript in order to have all the output
//redirected to the console and not the GUI, so we enforce that here
force_cscript();

g_rc = run();

exit(g_rc);

