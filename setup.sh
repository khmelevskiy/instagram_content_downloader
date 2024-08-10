pip install -r requirements.txt

git clone https://github.com/instaloader/instaloader.git
cd instaloader
git fetch origin pull/2330/head:docid-query-posts
git checkout docid-query-posts
pip install -e .
