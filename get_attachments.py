import requests
import wget
import os
import argparse
import zipfile
import tarfile
import urllib.parse

TICKET_URL_TEMPLATE = 'https://{domain}.freshdesk.com/api/v2/tickets/{ticket}'
CONVERSATIONS_URL_TEMPLATE = 'https://{domain}.freshdesk.com/api/v2/tickets/{ticket}/conversations?page={page}'
HEADERS = { 'Content-Type': 'application/json' }
ATTACHMENTS_DIR = 'attachments'

def make_dir_if_not_exists(path, *paths):
    if paths:
        joined = os.path.join(path, paths)
    else:
        joined = os.path.join(path)
    if not os.path.exists(joined):
        os.mkdir(joined)

def process_post(post):
    created_at = post['created_at'].replace('T', '_').replace(':', '.')
    post_path = os.path.join(ATTACHMENTS_DIR, created_at)
    for attachment in post['attachments']:
        make_dir_if_not_exists(post_path)

        attachment_name = attachment['name']
        attachment_path = os.path.join(post_path, attachment_name)

        if not os.path.isfile(attachment_path):
            attachment_url = attachment['attachment_url']
            # have to unquote because wget will quote again, and this is not reentrable due to handling of the %
            unquoted_url = urllib.parse.unquote(attachment_url)
            wget.download(unquoted_url, out=attachment_path)
        
        if zipfile.is_zipfile(attachment_path):
            attachment_dir_name = attachment_name.split('.')[0]
            attachment_dir_path = os.path.join(post_path, attachment_dir_name)
            with zipfile.ZipFile(attachment_path, 'r') as zip_ref:
                zip_ref.extractall(attachment_dir_path)
        
        if tarfile.is_tarfile(attachment_path):
            attachment_dir_name = attachment_name.split('.')[0]
            attachment_dir_path = os.path.join(post_path, attachment_dir_name)
            with tarfile.open(attachment_path, 'r') as tar_ref:
                def is_within_directory(directory, target):
                    
                    abs_directory = os.path.abspath(directory)
                    abs_target = os.path.abspath(target)
                
                    prefix = os.path.commonprefix([abs_directory, abs_target])
                    
                    return prefix == abs_directory
                
                def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                
                    for member in tar.getmembers():
                        member_path = os.path.join(path, member.name)
                        if not is_within_directory(path, member_path):
                            raise Exception("Attempted Path Traversal in Tar File")
                
                    tar.extractall(path, members, numeric_owner=numeric_owner) 
                    
                
                safe_extract(tar_ref, attachment_dir_path)

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--domain", dest="domain", 
                    help="Freshdesk company domain (domain.freshdesk.com)")
parser.add_argument("-k", "--apikey", dest="api_key", 
                    help="Freshdesk API key (see Profile settings)")
parser.add_argument("-t", "--ticket", dest="ticket", 
                    help="Ticket number")

args = parser.parse_args()

api_key = args.api_key
ticket = args.ticket
domain = args.domain

make_dir_if_not_exists(ATTACHMENTS_DIR)

url = TICKET_URL_TEMPLATE.format(ticket=ticket, domain=domain)
r = requests.get(url, headers=HEADERS, auth=(api_key, 'X'))
r.raise_for_status()

process_post(r.json())

page = 1
while True:
    url = CONVERSATIONS_URL_TEMPLATE.format(ticket=ticket, domain=domain, page=page)
    r = requests.get(url, headers=HEADERS, auth=(api_key, 'X'))
    r.raise_for_status()
    i = 0
    for post in r.json():
        process_post(post)
        i += 1
    if (i == 0):
        break
    page += 1

