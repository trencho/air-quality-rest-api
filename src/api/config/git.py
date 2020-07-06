from datetime import datetime
from io import BytesIO, StringIO
from os import environ, path

from github import Github, InputGitTreeElement
from pandas import read_csv

from definitions import ROOT_DIR, github_token_env_value

g = Github(environ.get(github_token_env_value))


def append_commit_files(file_list, file_names, root, data, file):
    file_list.append(data)
    rel_dir = path.relpath(root, ROOT_DIR)
    rel_file = path.join(rel_dir, file).replace('\\', '/')
    file_names.append(rel_file)


def merge_csv_files(repo_name, file_name, data):
    repo = g.get_user().get_repo(repo_name)
    repo_file = repo.get_contents(file_name)
    repo_file_content = read_csv(BytesIO(repo_file.decoded_content))
    local_file_content = read_csv(StringIO(data))
    repo_file_content = repo_file_content.append(local_file_content, ignore_index=True, sort=True)
    repo_file_content.drop_duplicates(inplace=True)
    return repo_file_content.to_csv(index=False)


def update_git_files(file_names, file_list, repo_name, branch, commit_message=''):
    if commit_message == '':
        commit_message = f'Data Updated - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'

    repo = g.get_user().get_repo(repo_name)
    master_ref = repo.get_git_ref(f'heads/{branch}')
    master_sha = master_ref.object.sha
    base_tree = repo.get_git_tree(master_sha)
    element_list = []
    for i in range(0, len(file_list)):
        if file_names[i].endswith('.csv'):
            file_list[i] = merge_csv_files(repo, file_names[i], file_list[i])
        element = InputGitTreeElement(file_names[i], '100644', 'blob', file_list[i])
        element_list.append(element)
    tree = repo.create_git_tree(element_list, base_tree)
    parent = repo.get_git_commit(master_sha)
    commit = repo.create_git_commit(commit_message, tree, [parent])
    master_ref.edit(commit.sha)
    print('Update complete')
