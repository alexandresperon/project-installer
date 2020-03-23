from lxml import etree
from collections import defaultdict
import subprocess
import argparse
import os
import os.path as path

class changeDir:
  def __init__(self, newPath):
    self.newPath = os.path.expanduser(newPath)

  def __enter__(self):
    self.savedPath = os.getcwd()
    os.chdir(self.newPath)

  def __exit__(self, etype, value, traceback):
    os.chdir(self.savedPath)

def exit_script():
    print 'Exiting script'
    exit()

def installation_failed(dependency):
    print 'Failed to install ' + dependency
    exit_script()
    

def pom_definition(pom):
    print 'Getting pom definition of ' + pom

    root = etree.parse(pom)
    tree = root

    if isinstance(root, etree._Element):
        tree = etree.ElementTree(root)

    depend = tree.xpath("//*[local-name()='dependency']")
    dependencies = []

    for dep in depend:
        info_list = []
        for child in dep.getchildren():
            info_list.append(child.tag.split('}')[1])
            info_list.append(child.text)

        artifact = info_list[3]
        version = info_list[5]
        if '$' in version:
            version = tree.xpath("//*[local-name()='" + info_list[5][2:-1] + "']")[0].text
        dependencies.append(artifact + path.sep + version)

    print dependencies
    return dependencies

def pom_file(workdir, artifact, version):
    pom_file = project_path(workdir, artifact, version) + path.sep + 'pom.xml'
    if path.isfile(pom_file):
        return pom_file
    print 'Project ' + artifact + '-' + version + ' not found'
    exit_script()

def project_path(workdir, artifact, version):
    return workdir + path.sep + artifact + path.sep + version

def corrects_if_module(dir_path):
    if path.isdir(dir_path):
        return dir_path
    artifact = dir_path.split(path.sep)[-2]
    parent_artifact = artifact.rsplit('-', 1)[0]
    parent_path = dir_path.replace(artifact, parent_artifact)
    if path.isdir(parent_path):
        return parent_path
    print 'Directory ' + dir_path + ' not found'
    exit_script()
    

def install_dependencies(dependencies, workdir):
    for dependency in dependencies:
        project_dir_path = corrects_if_module(workdir + path.sep + dependency)
        children_dependencies = pom_definition(project_dir_path + path.sep + 'pom.xml')
        if children_dependencies:
            install_dependencies(children_dependencies, workdir)
        install(dependency, project_dir_path)

def install(dependency, project_dir_path):
    with changeDir(project_dir_path):
                print 'Installing package ' + dependency
                status = subprocess.call(["mvn", "clean", "install"], shell=True)
                if status != 0:
                    installation_failed(dependency)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Easily clone all repositories from server.')
    parser.add_argument('--workdir', type=str, help='Directory to clone projects', required=True)
    parser.add_argument('--artifact',type=str, help='Artifact to install')
    parser.add_argument('--version', type=str, help='Version of the artifact')

    args = parser.parse_args()

    dependencies = pom_definition(pom_file(args.workdir, args.artifact, args.version))

    install_dependencies(dependencies, args.workdir)

    project_dir_path = project_path(args.workdir, args.artifact, args.version)
    dependency = args.artifact + path.sep + args.version

    install(dependency, project_dir_path)