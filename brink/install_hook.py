# Copyright (c) 2012 Adi Roiban.
# See LICENSE for details.
"""
Module executed after a package was installed.
"""
import os
import shutil

LICENSE_FILENAMES = [
    'license',
    'license.txt',
    'copying.lesser',
    'copying',
    'lgpl.txt',
    ]

AUTHORS_FILENAMES = [
    'authors',
    ]


def run(installed_requirement):
    """
    It received an :class:`pip.req.InstallRequirement`.
    """
    source_folder = installed_requirement.source_dir
    pip_build_folder = os.path.dirname(source_folder)
    build_folder = os.path.dirname(pip_build_folder)
    legal_folder = os.path.join(build_folder, 'legal')
    projects_path = os.path.join(legal_folder, '3rd-party-projects')

    # Create legal folder if missing.
    if not os.path.isdir(legal_folder):
        os.makedirs(legal_folder)

    pkg_info = installed_requirement.pkg_info()

    # Write list of 3rd party projects.
    with open(projects_path, 'a') as projects_file:
        projects_file.write("%s version %s licensed under %s.\n" % (
            pkg_info['name'],
            pkg_info['version'],
            pkg_info['license'],
            ))

    # Copy license file as legal/project-LICENSE
    project_license_path = os.path.join(
        legal_folder, pkg_info['name'].lower() + '-license')
    license_present = False
    for filename in os.listdir(source_folder):
        if license_present:
            break

        for license_file in LICENSE_FILENAMES:
            if filename.lower() != license_file:
                continue
            license_present = True
            shutil.copy2(
                os.path.join(source_folder, filename), project_license_path)

    if not license_present:
        # Write a default license file if can not find license.
        default_license = 'Project licensed under %s. Author %s.' % (
            pkg_info['license'], pkg_info['author'])
        with open(project_license_path, 'w') as project_license:
            project_license.write(default_license)

    # Copy authors file as legal/project-authors
    authors_path = os.path.join(
        legal_folder, pkg_info['name'].lower() + '-authors')
    authors_present = False
    for filename in os.listdir(source_folder):
        if authors_present:
            break
        for authors_file in AUTHORS_FILENAMES:
            if filename.lower() != authors_file:
                continue
            authors_present = True
            shutil.copy2(os.path.join(source_folder, filename), authors_path)

    # No files should be removed by uninstall.
    return []
