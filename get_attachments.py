import requests
import wget
import os
import argparse
import zipfile
import tarfile

def make_dir_if_not_exists(path, *paths):
    if paths:
        joined = os.path.join(path, paths)
    else:
        joined = os.path.join(path)
    if not os.path.exists(joined):
        os.mkdir(joined)

URL_TEMPLATE = 'https://gridgain.freshdesk.com/api/v2/tickets/{ticket}/conversations'
HEADERS = { 'Content-Type': 'application/json' }
ATTACHMENTS_DIR='attachments'

parser = argparse.ArgumentParser()
parser.add_argument("-k", "--apikey", dest="api_key", 
                    help="Freshdesk API key (see Profile settings)")
parser.add_argument("-t", "--ticket", dest="ticket", 
                    help="Ticket number")

args = parser.parse_args()

api_key = args.api_key
ticket = args.ticket

url = URL_TEMPLATE.format(ticket=ticket)
r = requests.get(url, headers=HEADERS, auth=(api_key, 'X'))
r.raise_for_status()

make_dir_if_not_exists(ATTACHMENTS_DIR)

for post in r.json():
    created_at = post['created_at'].replace('T', '_').replace(':', '.')
    post_path = os.path.join(ATTACHMENTS_DIR, created_at)
    for attachment in post['attachments']:
        make_dir_if_not_exists(post_path)

        attachment_name = attachment['name']
        attachment_path = os.path.join(post_path, attachment_name)

        if not os.path.isfile(attachment_path):
            attachment_url = attachment['attachment_url']
            wget.download(attachment_url, out=attachment_path)
        
        if zipfile.is_zipfile(attachment_path):
            attachment_dir_name = attachment_name.split('.')[0]
            attachment_dir_path = os.path.join(post_path, attachment_dir_name)
            with zipfile.ZipFile(attachment_path, 'r') as zip_ref:
                zip_ref.extractall(attachment_dir_path)
        
        if tarfile.is_tarfile(attachment_path):
            attachment_dir_name = attachment_name.split('.')[0]
            attachment_dir_path = os.path.join(post_path, attachment_dir_name)
            with tarfile.open(attachment_path, 'r') as tar_ref:
                tar_ref.extractall(attachment_dir_path)
                