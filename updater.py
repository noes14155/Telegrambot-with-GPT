import hashlib
import os
import shutil
import git
import requests
class SelfUpdating:
    """
    The `SelfUpdating` class is responsible for checking if there is a new version available for a given GitHub repository
    and updating the local files if necessary.
    """

    def __init__(self, repo_url: str, branch: str = "master"):
        """
        Initializes the `SelfUpdating` object with the repository URL and branch.

        Args:
            repo_url (str): The URL of the GitHub repository.
            branch (str, optional): The branch to track for updates. Defaults to "master".
        """
        self.repo_url = f'https://github.com/{repo_url}'
        self.repo_name = repo_url
        self.branch = branch
        self.current_version = self.get_current_version()

    def check_for_update(self):
        """
        Checks if a new version is available and updates the files if necessary.
        """
        latest_tag = self.get_latest_tag_from_github(self.repo_name)

        if latest_tag != self.current_version:
            print(f"New version {latest_tag} available! Updating...")
            self.update()
        else:
            print(f"Already on latest version {self.current_version}")

    def update(self):
        """
        Updates the files by cloning the repository, pulling the latest changes, and copying the updated files.
        """
        temp_dir = "./temp/"
        if not os.path.exists(temp_dir):
            git.Git(".").clone(self.repo_url, temp_dir)
        try:
            repo = git.Repo(temp_dir)
            repo.git.checkout(self.branch)
            repo.git.pull()
        except git.exc.GitCommandError as e:
            print(f"Git pull failed: {e}")
            return

        changed_files = []
        for root, dirs, files in os.walk(temp_dir):
            if '.git' in dirs:
                dirs.remove('.git')
            for file in files:
                file_path = os.path.join(root, file)
                current_hash = hashlib.sha256(open(file_path, "rb").read()).hexdigest()
                destination_path = os.path.join(os.getcwd(), file_path.split(temp_dir, 1)[1])
                if os.path.exists(destination_path):
                    existing_hash = hashlib.sha256(open(destination_path, "rb").read()).hexdigest()
                else:
                    existing_hash = ""
                if current_hash != existing_hash:
                    shutil.copyfile(file_path, destination_path)
                    changed_files.append(file)

        try:
            shutil.rmtree(temp_dir)
        except OSError as e:
            print(f"Error removing temp dir: {e}")

        self.current_version = self.get_current_version()

    def get_current_version(self) -> str:
        """
        Returns the current version of the repository.

        Returns:
            str: The current version of the repository.
        """
        # Return current version somehow
        return "0.7"

    def get_latest_tag_from_github(self, repo_url: str) -> str:
        """
        Retrieves the latest tag from the GitHub API.

        Args:
            repo_url (str): The URL of the GitHub repository.

        Returns:
            str: The latest tag from the GitHub API.
        """
        api_url = f"https://api.github.com/repos/{repo_url}/releases/latest"
        response = requests.get(api_url)
        if response.ok:
            release = response.json()
            return release["name"]
        else:
            print(f"Error fetching latest release: {response}")
            return "None"