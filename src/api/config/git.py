from datetime import datetime
from os import environ, path

from github import Github, InputGitTreeElement

from definitions import ROOT_DIR, github_token_env_value


def append_commit_files(file_list, file_names, root, data, file):
    file_list.append(data)
    rel_dir = path.relpath(root, ROOT_DIR)
    rel_file = path.join(rel_dir, file).replace('\\', '/')
    file_names.append(rel_file)


def update_git_files(file_names, file_list, repo_name, branch, commit_message=''):
    if commit_message == '':
        commit_message = 'Data Updated - ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    access_token = environ.get(github_token_env_value)
    g = Github(access_token)
    repo = g.get_user().get_repo(repo_name)
    master_ref = repo.get_git_ref('heads/' + branch)
    master_sha = master_ref.object.sha
    base_tree = repo.get_git_tree(master_sha)
    element_list = []
    for i in range(0, len(file_list)):
        element = InputGitTreeElement(file_names[i], '100644', 'blob', file_list[i])
        element_list.append(element)
    tree = repo.create_git_tree(element_list, base_tree)
    parent = repo.get_git_commit(master_sha)
    commit = repo.create_git_commit(commit_message, tree, [parent])
    master_ref.edit(commit.sha)
    print('Update complete')
