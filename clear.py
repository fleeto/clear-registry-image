#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlite3
import os
import sys
import subprocess
import json
import time
import shutil
import os.path
from datetime import datetime

fp = open("conf.json")
conf = json.load(fp)
con = sqlite3.connect(':memory:')
cursor = con.cursor()

registry_root = conf["registry"]["base_path"]

def list_orphan(root_dir):
    repo_root = os.path.join(root_dir,"docker/registry/v2/repositories")
    repositories = os.listdir(repo_root)
    result = {}
    for repo_name in repositories:
        repo_path = os.path.join(repo_root, repo_name)
        tag_root = os.path.join(repo_path, "_manifests/tags")
        rev_root = os.path.join(repo_path, "_manifests/revisions")
        tag_list = os.listdir(tag_root)
        if len(tag_list) == 0:
            shutil.rmtree(repo_path)
            continue
        tag_sha_list = get_tag_sha_list(tag_root)
        revision_sha_list = get_revision_sha_list(rev_root)
        orphan_list = filter(lambda x: x not in tag_sha_list, revision_sha_list)
        result[repo_name] = orphan_list
    return result

def get_tag_sha_list(tag_root):
    tag_list = os.listdir(tag_root)
    result = []
    for tag in tag_list:
        text_file = os.path.join(tag_root, tag, "current/link")
        with open(text_file, 'r') as f:
            first_line = f.readline()
            sha = first_line[7:]
            result.append(sha)
    return result

def get_revision_sha_list(revision_root):
    rev_list = os.listdir(os.path.join(revision_root, "sha256"))
    return rev_list


def del_manifest(image_name, tag_hash):
    command = conf["curl"] + ["-X", "DELETE"]
    url = conf["registry"]["url"] + "/v2/{}/manifests/{}"
    url = url.format(image_name, tag_hash)
    subprocess.check_call(command + [url])


def get_image_list():
    command = conf["curl"]
    url = conf["registry"]["url"] + "/v2/_catalog"
    image_str = subprocess.check_output(command + [url])
    image_list = json.loads(image_str)
    return image_list["repositories"]


def get_tag_list(image):
    command = conf["curl"]
    url = "{}/v2/{}/tags/list".format(conf["registry"]["url"], image)
    tag_str = subprocess.check_output(command + [url])
    tag_obj = json.loads(tag_str)
    return tag_obj["tags"]


def get_blob_list(image, tag):
    command = conf["curl"] + ["-i"]
    url = "{}/v2/{}/manifests/{}".format(conf["registry"]["url"], image, tag)
    blob_str = subprocess.check_output(command + [url])
    json_str = ""
    json_start = 0
    for line in blob_str.split("\n"):
        line = line.strip()
        if line == "{":
            json_start = 1
        if json_start == 1:
            json_str += line
        if line[:21] == "Docker-Content-Digest":
            tag_hash = line[23:]

    blob_obj = json.loads(json_str)
    hash_list = []
    for blob_rec in blob_obj["layers"]:
        hash_list += [blob_rec["digest"]]
    return (tag_hash, hash_list)


def get_blob_info(image_name, blob_hash):
    command = conf["curl"] + ["-I"]
    url = "{}/v2/{}/blobs/{}".format(conf["registry"]
                                     ["url"], image_name, blob_hash)
    header = subprocess.check_output(command + [url])
    rec = {"image_name": image_name, "blob_hash": blob_hash}
    for line in header.split('\n'):
        line = line.strip()
        if line[:14] == "Content-Length":
            rec["blob_size"] = int(line[16:])
        if line[:4] == "Date":
            time_str = line[6:]
            dt = datetime.strptime(time_str, "%a, %d %b %Y %H:%M:%S %Z")
            rec["blob_timestamp"] = int(time.mktime(dt.timetuple()))
    return rec


def write_blob(record):
    blob_query = "SELECT COUNT(id) FROM blobs WHERE blob_hash='{}'"
    blob_query = blob_query.format(record["blob_hash"])
    cursor.execute(blob_query)
    blob_count = cursor.fetchone()[0]
    if (blob_count == 0):
        blob_insert = "INSERT INTO blobs (blob_hash, blob_size, blob_date)"
        blob_insert += "  VALUES ('{}', {}, {})"
        blob_insert = blob_insert.format(record["blob_hash"],
                                         record["blob_size"],
                                         record["blob_timestamp"])
        cursor.execute(blob_insert)
    # Write relations into db
    relation_query = "SELECT COUNT(id) FROM relations WHERE image_name = '{}' "
    relation_query += "AND tag_name= '{}' AND blob_hash='{}' "
    relation_query = relation_query.format(
        record["image_name"], record["tag_name"], record["blob_hash"])
    cursor.execute(relation_query)
    relation_count = cursor.fetchone()[0]

    if (relation_count == 0):
        relation_insert = "INSERT INTO relations (image_name, tag_name, blob_hash)"
        relation_insert += " VALUES ('{}', '{}', '{}')"
        cursor.execute(
            relation_insert.format(
                record["image_name"],
                record["tag_name"],
                record["blob_hash"]
            )
        )


def write_tag(record):
    tag_sql = "INSERT INTO images (image_name, tag_name, tag_timestamp, tag_size, tag_hash) "
    tag_sql += "VALUES ('{}', '{}', {}, {}, '{}')"
    tag_sql = tag_sql.format(
        record["image_name"],
        record["tag_name"],
        record["tag_timestamp"],
        record["tag_size"],
        record["tag_hash"]
    )
    cursor.execute(tag_sql)


def db_init():
    cursor.execute(
        "CREATE TABLE images (id INTEGER PRIMARY KEY,image_name TEXT, tag_name TEXT, tag_timestamp INTEGER, tag_hash TEXT,tag_size INTEGER);")
    cursor.execute(
        "CREATE TABLE relations (id INTEGER PRIMARY KEY,image_name TEXT, tag_name TEXT, blob_hash TEXT);")
    cursor.execute(
        "CREATE TABLE blobs (id INTEGER PRIMARY KEY, blob_hash TEXT, blob_size INTEGER, blob_date INTEGER)")


def main(sql_id, action):
    orphan = list_orphan(registry_root)
    for image in orphan.keys():
        sha_list = orphan[image]
        for sha in sha_list:
            del_manifest(image, "sha256:"+sha)
            os.rmdir(
                os.path.join(registry_root, "docker/registry/v2/repositories",
                image, "_manifests/revisions/sha256/", sha)
            )


    condition = conf["sql"][sql_id]
    db_init()
    image_list = get_image_list()
    for image_name in image_list:
        tag_list = get_tag_list(image_name)
        if tag_list == None:
            print "Tag list of Image {} is null" % image_name
            continue
        for tag_name in tag_list:
            (tag_hash,blob_list) = get_blob_list(image_name, tag_name)
            tag_record = {"image_name": image_name, "tag_name": tag_name,
                          "tag_size": 0, "tag_timestamp": 0,
                          "tag_hash": tag_hash}
            for blob_hash in blob_list:
                blob_info = get_blob_info(image_name, blob_hash)
                blob_info['tag_name'] = tag_name
                write_blob(blob_info)
                tag_record["tag_size"] += blob_info["blob_size"]
                if (blob_info['blob_timestamp'] > tag_record["tag_timestamp"]):
                    tag_record["tag_timestamp"] = blob_info['blob_timestamp']
            write_tag(tag_record)

    sql = "select image_name, tag_name, tag_hash, tag_timestamp, tag_size \
        from images where {} order by image_name, tag_name".format(condition)
    tag_list = cursor.execute(sql)
    if action == "none":
        for record in tag_list:
            print("{}:{}\t{}\t{}\t{}".format(
                record[0],
                record[1],
                record[2],
                record[3],
                record[4],
                )
            )

    if action == "del":
        for record in tag_list:
            image_name = record[0]
            hash_value = record[2]
            del_manifest(image_name, hash_value)
        subprocess.check_call(conf["gc-command"])


if __name__ == "__main__":
    if (len(sys.argv) == 3):
        main(sys.argv[1], sys.argv[2])
    else:
        print "Usage %s sql_id  action " % sys.argv[0]
