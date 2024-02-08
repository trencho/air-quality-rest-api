from datetime import datetime
from io import BytesIO, StringIO
from logging import getLogger
from os import environ, path, sep
from shutil import make_archive, move

from github import Github, GithubException, GitRef, GitTree, InputGitTreeElement, Repository
from github.Auth import Token
from pandas import concat
from requests import ReadTimeout
from urllib3.exceptions import ReadTimeoutError

from definitions import column_dtypes, GITHUB_TOKEN, ROOT_PATH
from processing import read_csv_in_chunks, trim_dataframe

logger = getLogger(__name__)


class GithubSingleton:
    _instance = None

    @staticmethod
    def get_instance():
        if not GithubSingleton._instance:
            GithubSingleton._instance = GithubSingleton()
        return GithubSingleton._instance

    def __init__(self):
        if (token := environ.get(GITHUB_TOKEN)) is not None:
            self.github_instance = Github(auth=Token(token))
        else:
            self.github_instance = None

    def get_repository(self, repo_name: str) -> Repository:
        return self.github_instance.get_user().get_repo(repo_name)


def append_commit_files(file_list: list, data: [bytes, str], root: str, file: str, file_names: list) -> None:
    file_list.append(data)
    rel_dir = path.relpath(root, ROOT_PATH)
    rel_file = path.join(rel_dir, file).replace("\\", "/").strip("./")
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
        logger.error("Error occurred while committing files to GitHub", exc_info=True)


def create_archive(source, destination) -> None:
    base = path.basename(destination)
    name = base.split(".")[0]
    fmt = base.split(".")[1]
    archive_from = path.dirname(source)
    archive_to = path.basename(source.strip(sep))
    make_archive(base_name=name, format=fmt, root_dir=archive_from, base_dir=archive_to)
    move(f"{name}.{fmt}", destination)


def merge_csv_files(repo: Repository, file_name: str, data: str) -> str:
    try:
        string_io_data = StringIO(data)
        string_io_data.seek(0)
        local_file_content = read_csv_in_chunks(string_io_data.getvalue())
        repo_file = repo.get_contents(file_name)
        bytes_io_data = BytesIO(repo_file.decoded_content)
        bytes_io_data.seek(0)
        repo_file_content = read_csv_in_chunks(bytes_io_data.getvalue().decode("utf-8"))
        local_file_content = concat([local_file_content, repo_file_content], ignore_index=True)
        trim_dataframe(local_file_content, "time")
        local_file_content = local_file_content.astype(column_dtypes, errors="ignore")
        return local_file_content.to_csv(index=False)
    except Exception:
        logger.error("Error occurred while merging local files with files from GitHub repository", exc_info=True)


def update_git_files(file_list: list, file_names: list, repo_name: str, branch: str,
                     commit_message: str = f"Data Updated - {datetime.now().strftime('%H:%M:%S %d-%m-%Y')}") -> None:
    repo = GithubSingleton.get_instance().get_repository(repo_name)
    master_ref = repo.get_git_ref(f"heads/{branch}")
    master_sha = master_ref.object.sha
    base_tree = repo.get_git_tree(master_sha)
    element_list = []
    for i in range(0, len(file_list)):
        if (file_name := file_names[i]).endswith(".csv"):
            file = merge_csv_files(repo, file_name, file_list[i])
            element = InputGitTreeElement(file_name, "100644", "blob", file)
            element_list.append(element)
        elif file_name.endswith((".png", ".zip")):
            file = repo.create_git_blob(file_list[i].decode(), "base64")
            element = InputGitTreeElement(file_name, "100644", "blob", sha=file.sha)
            element_list.append(element)

    commit_git_files(repo, master_ref, master_sha, base_tree, commit_message, element_list)
