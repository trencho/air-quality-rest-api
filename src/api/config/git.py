from datetime import datetime
from io import BytesIO, StringIO
from os import environ, path, sep
from shutil import make_archive, move
from traceback import print_exc

from github import Github, GithubException, GitRef, GitTree, InputGitTreeElement, Repository
from pandas import concat, read_csv
from requests import ReadTimeout
from urllib3.exceptions import ReadTimeoutError

from definitions import github_token, ROOT_PATH

g = Github(environ.get(github_token))


def append_commit_files(file_list: list, data: [bytes, str], root: str, file: str, file_names: list) -> None:
    file_list.append(data)
    rel_dir = path.relpath(root, ROOT_PATH)
    rel_file = path.join(rel_dir, file).replace('\\', '/').strip('./')
    file_names.append(rel_file)


def commit_git_files(repo: Repository, master_ref: GitRef, master_sha: str, base_tree: GitTree, commit_message: str,
                     element_list: list) -> None:
    try:
        tree = repo.create_git_tree(element_list, base_tree)
        parent = repo.get_git_commit(master_sha)
        commit = repo.create_git_commit(commit_message, tree, [parent])
        master_ref.edit(commit.sha)
    except (GithubException, ReadTimeout, ReadTimeoutError):
        if len(element_list) // 2 > 0:
            commit_git_files(repo, master_ref, master_sha, base_tree, commit_message,
                             element_list[:len(element_list) // 2])
            commit_git_files(repo, master_ref, master_sha, base_tree, commit_message,
                             element_list[len(element_list) // 2:])
        print_exc()


def create_archive(source, destination):
    base = path.basename(destination)
    name = base.split('.')[0]
    fmt = base.split('.')[1]
    archive_from = path.dirname(source)
    archive_to = path.basename(source.strip(sep))
    make_archive(base_name=name, format=fmt, root_dir=archive_from, base_dir=archive_to)
    move(f'{name}.{fmt}', destination)


def merge_csv_files(repo: Repository, file_name: str, data: str) -> str:
    local_file_content = read_csv(StringIO(data))
    try:
        repo_file = repo.get_contents(file_name)
        repo_file_content = read_csv(BytesIO(repo_file.decoded_content))
        local_file_content = concat([local_file_content, repo_file_content], ignore_index=True)
    except GithubException:
        print_exc()
    local_file_content.drop_duplicates(inplace=True)
    return local_file_content.to_csv(index=False)


def update_git_files(file_list: list, file_names: list, repo_name: str, branch: str,
                     commit_message: str = f'Data Updated - {datetime.now().strftime("%H:%M:%S %d-%m-%Y")}') -> None:
    repo = g.get_user().get_repo(repo_name)
    master_ref = repo.get_git_ref(f'heads/{branch}')
    master_sha = master_ref.object.sha
    base_tree = repo.get_git_tree(master_sha)
    element_list = []
    for i in range(0, len(file_list)):
        if (file_name := file_names[i]).endswith('.csv'):
            file = merge_csv_files(repo, file_name, file_list[i])
            element = InputGitTreeElement(file_name, '100644', 'blob', file)
            element_list.append(element)
        elif file_name.endswith(('.png', '.zip')):
            file = repo.create_git_blob(file_list[i].decode(), 'base64')
            element = InputGitTreeElement(file_name, '100644', 'blob', sha=file.sha)
            element_list.append(element)

    commit_git_files(repo, master_ref, master_sha, base_tree, commit_message, element_list)
