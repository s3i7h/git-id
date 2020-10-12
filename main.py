import os
import sys
from dataclasses import dataclass, field
from typing import List, Optional

import yaml
from click import option, group, pass_context, argument
from git import Repo, InvalidGitRepositoryError


@dataclass
class Profile:
    id: str
    raw_config: dict = field(default_factory=dict)

    @property
    def name(self):
        return self.raw_config.get("user.name", "")

    @name.setter
    def name(self, name):
        self.raw_config["user.name"] = name

    @property
    def email(self):
        return self.raw_config.get("user.email", "")

    @email.setter
    def email(self, email):
        self.raw_config["user.email"] = email

    @property
    def gpg_key(self):
        return self.raw_config.get("user.signingkey", "")

    @gpg_key.setter
    def gpg_key(self, gpg_key):
        self.raw_config["user.signingkey"] = gpg_key

    def __repr__(self):
        return f"Profile({self.id}, {self.raw_config})"

    def __str__(self):
        return f"{self.name} <{self.email}>" + ("" if not self.gpg_key else f": {self.gpg_key}")

    def __eq__(self, other):
        if not isinstance(other, Profile):
            return False
        return all([
            self.name == other.name,
            self.email == other.email,
            self.gpg_key == other.gpg_key,
        ])


class ProfileManager:
    def __init__(self, config_path=None):
        self.config_path = os.path.abspath(config_path or os.path.join(os.environ["HOME"], ".git-id.yml"))
        if not os.path.exists(self.config_path):
            with open(self.config_path, "w"):
                ...
        with open(self.config_path) as config_yml:
            config = yaml.safe_load(config_yml)
        if not config or isinstance(config, dict):
            if not config or not all([isinstance(profile, dict) for profile in config.values()]):
                config = {}
        self.config = config

    def list_profiles(self) -> List[Profile]:
        return [
            Profile(id=profile_id, raw_config=raw_config)
            for profile_id, raw_config in self.config.items()
        ]

    def get_profile(self, profile_id: str) -> Optional[Profile]:
        return Profile(id=profile_id, raw_config=self.config[profile_id]) if profile_id in self.config else None

    def save_profile(self, profile: Profile) -> None:
        self.config[profile.id] = profile.raw_config

    def save(self):
        with open(self.config_path, mode="w") as config_yml:
            yaml.safe_dump(self.config, config_yml)

    @classmethod
    def create(cls, name="", email="", gpg_key="", profile_id=""):
        print("Enter a new Identity")
        profile = Profile(profile_id)
        profile.name = name or input("name: ")
        if not profile.name:
            return None
        profile.email = email or input("email: ")
        if not profile.email:
            return None
        profile.gpg_key = gpg_key or input("signingkey: ")
        if not profile.id:
            print("Give a name for this profile: ", profile)
            profile.id = input(">")
        if not profile.id:
            return None
        return profile


class GitManager:
    repo: Optional[Repo]

    def __init__(self):
        self.cwd = os.getcwd()
        self.basename = os.path.basename(self.cwd)
        try:
            self.repo = Repo(self.cwd, search_parent_directories=True)
        except InvalidGitRepositoryError:
            self.repo = None

    def get_profile(self) -> Optional[Profile]:
        if not self.repo:
            return None
        profile = Profile(self.basename)
        config_parser = self.repo.config_reader()
        profile.name = config_parser.get_value("user", "name", "")
        profile.email = config_parser.get_value("user", "email", "")
        profile.gpg_key = config_parser.get_value("user", "signingkey", "")
        return profile

    def save_profile(self, profile: Profile):
        if not self.repo:
            return None
        config_writer = self.repo.config_writer()
        for config_key, value in profile.raw_config.items():
            section_option = config_key.split(".")
            if len(section_option) != 2:
                continue
            config_writer.set_value(section_option[0], section_option[1], value)
        config_writer.write()


@group(invoke_without_command=True)
@pass_context
def git_id(ctx):
    if ctx.invoked_subcommand is None:
        git = GitManager()
        local_profile = git.get_profile()
        if not local_profile:
            print("Couldn't retrieve profile information")
            return sys.exit(1)
        manager = ProfileManager()
        matching_profile = [profile for profile in manager.list_profiles() if profile == local_profile][:1]
        if matching_profile:
            profile = matching_profile[0]
            print(f"{profile.id} - {profile}")
            return sys.exit(0)
        else:
            profile = local_profile
            print(f"{profile}")
            print("\nThis profile is not registered yet.")
            register_choice = input("register? (y/N):") in "yY"
            if not register_choice:
                return sys.exit(0)
            profile.id = input(f"Set an id to the profile ({profile.id}):") or profile.id
            manager.save_profile(profile)
            manager.save()
            return sys.exit(0)


@git_id.command()
def ls():
    manager = ProfileManager()
    profiles = manager.list_profiles()
    if not profiles:
        print("No profiles available")
    local_profile = GitManager().get_profile()
    for profile in profiles:
        print(
            f"{'*' if profile == local_profile else ''}\t"
            f"{profile.id} - {profile}"
        )


@git_id.command()
@argument("profile_id")
def use(profile_id: str):
    manager = ProfileManager()
    profile = manager.get_profile(profile_id)
    if not profile:
        print(f"Profile '{profile_id}' not found.")
        return sys.exit(2)
    git = GitManager()
    if not git.repo:
        print(f"Couldn't retrieve information about current repo")
    git.save_profile(profile)
    print(f"Current Identity: {profile}")


@git_id.command()
@option("--profile_id", default=None)
@option("--name", default=None)
@option("--email", default=None)
@option("--gpg_key", default=None)
def create(
        profile_id: str = None,
        name: str = None,
        email: str = None,
        gpg_key: str = None
):
    manager = ProfileManager()
    profile = manager.create(name, email, gpg_key, profile_id)
    if not profile:
        print("Cancelled.")
        return sys.exit(0)
    manager.save_profile(profile)
    manager.save()
    print(f"Saved Identity: {profile.id} - {profile}")


if __name__ == "__main__":
    git_id()
