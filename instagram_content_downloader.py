import json
import logging
import os

import pandas as pd

from instaloader.instaloader import Instaloader, Profile
from instaloader.instaloader.exceptions import TwoFactorAuthRequiredException
from instaloader.instaloader.structures import Post


class InstagramLoader(Instaloader):
    def __init__(self, username: str, password: str, save_custom_metadata: bool = True, **kwargs):
        super().__init__(**kwargs)

        self.username = username
        self.password = password
        self.save_custom_metadata = save_custom_metadata

        self.login()

    def login(self, **kwargs) -> None:
        """
        Login to Instagram. If two-factor authentication is required, the user will be prompted to enter the code.
        """

        logging.info("Logging in to Instagram")
        try:
            super().login(user=self.username, passwd=self.password)
        except TwoFactorAuthRequiredException:
            logging.warning("Two factor authentication required")
            two_factor_code = input("Enter the two factor login code: ")
            super().two_factor_login(two_factor_code=two_factor_code)

    def download_post(self, post: Post, target: str) -> None:
        """
        Download a post from Instagram and save it to the target directory. Also, save custom metadata to a JSON file if
        enable(`save_custom_post_metadata`).

        Parameters
        ----------
        post: Post
            Post object from Instagram.
        target: str
            Target directory to save the post.
        """

        super().download_post(post=post, target=target)
        if self.save_custom_metadata:
            formated_datetime_utc = post.date_utc.strftime("%Y-%m-%d_%H-%M-%S")
            self.save_custom_post_metadata(
                post=post,
                target_dir=self.dirname_pattern.format(target=target, date_utc=formated_datetime_utc),
                file_name=f"custom_metadata_{post.shortcode}",
            )

    def get_profile(self) -> Profile:
        """
        Get the profile of the user.

        Returns
        -------
        Profile
            Profile object from Instagram
        """

        logging.info(f"Getting profile of {self.username}")

        return Profile.from_username(context=self.context, username=self.username)

    def download_posts(self, limit: int | None = 10, target: str | None = None) -> None:
        """
        Download posts of the user.

        Parameters
        ----------
        limit: int
            Number of posts to download. If None, download all posts.
        target: str
            Target directory to save the posts.
        """

        logging.info(f"Downloading posts of {self.username}")
        profile = self.get_profile()

        for idx, post in enumerate(profile.get_posts()):
            self.download_post(post=post, target=target or self.username)
            if limit and idx > limit:
                break

    def download_posts_sorted_by_likes(
        self, limit: int | None = 10, target: str | None = None, reverse: bool = True
    ) -> None:
        """
        Download posts of the user sorted by likes.

        Parameters
        ----------
        limit: int
            Number of posts to download. If None, download all posts.
        target: str
            Target directory to save the posts.
        reverse: bool
            If True, sort posts by likes in descending order. Otherwise, sort posts by likes in ascending
        """

        logging.info(f"Downloading posts of {self.username} sorted by likes")
        profile = self.get_profile()

        posts = sorted(profile.get_posts(), key=lambda post: post.likes, reverse=reverse)[:limit]

        for post in posts:
            self.download_post(post=post, target=target or self.username)

    def save_custom_post_metadata(self, post: Post, target_dir: str, file_name: str) -> None:
        """
        Save custom metadata to a JSON file.
        Format of the metadata:
        {
            "Date UTC": str(post.date_utc),
            "Caption hashtags": post.caption_hashtags,
            "Caption": str(post.caption),
            "Caption mentions": post.caption_mentions,
            "Owner username": post.owner_username,
            "Tagged users": post.tagged_users,
            "Is pinned": post.is_pinned,
            "Likes count": post.likes,
            "Video view count": post.video_view_count,
            "Comments count": post.comments,
            "Video duration": post.video_duration,
        }

        Parameters
        ----------
        post: Post
            Post object from Instagram.
        target_dir: str
            Target directory to save the JSON file.
        file_name: str
            Name of the JSON file.
        """

        metadata = {
            "Date UTC": str(post.date_utc),
            "Caption hashtags": post.caption_hashtags,
            "Caption": str(post.caption),
            "Caption mentions": post.caption_mentions,
            "Owner username": post.owner_username,
            "Tagged users": post.tagged_users,
            "Is pinned": post.is_pinned,
            "Likes count": post.likes,
            "Video view count": post.video_view_count,
            "Comments count": post.comments,
            "Video duration": post.video_duration,
        }

        # Create a directory to save the JSON file
        os.makedirs(name=target_dir, exist_ok=True)

        # Path to the JSON file
        json_file_path = os.path.join(target_dir, f"{file_name}.json")

        # Save metadata to the JSON file
        with open(json_file_path, "w", encoding="utf-8") as json_file:
            json.dump(metadata, json_file, ensure_ascii=False, indent=4)


def convert_all_custom_metadata_to_csv() -> pd.DataFrame:
    """
    Convert all custom metadata to a CSV file.

    Returns
    -------
    pd.DataFrame
        DataFrame with all metadata.
    """

    # List of all directories with metadata
    metadata_dirs = [d for d in os.listdir() if os.path.isdir(d) and d.endswith("_UTC")]

    # List of all JSON files with metadata
    metadata_files = [
        os.path.join(d, f)
        for d in metadata_dirs
        for f in os.listdir(d)
        if f.endswith(".json") and f.startswith("custom_metadata")
    ]

    # List of all metadata
    metadata_list = []

    # Read all metadata from JSON files
    for file in metadata_files:
        with open(file, "r", encoding="utf-8") as json_file:
            metadata = json.load(json_file)
            metadata_list.append(metadata)

    # Create a DataFrame from the list of metadata
    metadata_df = pd.DataFrame(metadata_list)
    metadata_df["Caption"] = metadata_df["Caption"].fillna("")

    # Save metadata to the CSV file
    metadata_df.to_csv("metadata.csv", index=False)

    return metadata_df


if __name__ == "__main__":
    LOGIN = "<login>"  # your username from Instagram
    PASSWORD = "<password>"  # your password from Instagram
    TARGET_USERNAME = "<target_username>"  # target username from Instagram

    loader = InstagramLoader(
        username=LOGIN,
        password=PASSWORD,
        download_comments=True,
        compress_json=False,
        save_metadata=False,
        dirname_pattern="{target}_{date_utc}_UTC",
        filename_pattern="{shortcode}",
    )

    loader.download_posts(limit=10, target=TARGET_USERNAME)

    # loader.download_posts_sorted_by_likes(limit=5, target=TARGET_USERNAME)

    convert_all_custom_metadata_to_csv()
