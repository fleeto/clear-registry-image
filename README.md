# Clear registry images

*v2 API only*

- Select images from Docker registry with sql conditions and remove them.
- Find orphan manifests from Docker reistry and remove them.
- Release disk space.

From [@mortensteenrasmussen](https://github.com/mortensteenrasmussen/docker-registry-manifest-cleanup):

> Docker images can be pulled both via image:tag and via image@digest. Because of this, if you overwrite an image:tag with a different one (e.g., pushing nightly to whateverimage:latest) you will still be able to pull the OLD versions of that tag by using image@digest. This functionality means the registry garbage collect cannot remove an image because a reference still exists.


---

Usage: `clear.py sql_id action`


- **sql_id**: It's conditions will be used to filter the images.
- **action**:
	- del: remove the tags , and run gc.
	- none: list view.

## Configuration

All configuration items stored into conf.json.

### registry

- url: URL of the registry endpoint.
- base_path: registry file root, MUST CAN BE WRITE by the script.

## Data Structure

The script will store image info into a in-memory sqlite database.

~~~sql

CREATE TABLE images (id INTEGER PRIMARY KEY,image_name TEXT, tag_name TEXT, tag_timestamp INTEGER, tag_hash TEXT,tag_size INTEGER);

CREATE TABLE relations (id INTEGER PRIMARY KEY,image_name TEXT, tag_name TEXT, blob_hash TEXT);

CREATE TABLE blobs (id INTEGER PRIMARY KEY, blob_hash TEXT, blob_size INTEGER, blob_date INTEGER)

~~~

We can store conditons in `conf.json`, to get get image list that match the filter.

for example:

~~~json
  "sql": {
    "none": "image_name = '<none>'"
  }

~~~

## Examples

**in 'conf.json'**:

~~~json
  "sql": {
    "dummy": " tag_name = 'dummy'"
  }
~~~

**command line**

`clear.py dummy del`

### Delete all images named like '%prod%', except for tag 'latest'

**in 'conf.json'**:

~~~json
  "sql": {
    "autobuild": "image_name like '%prod%' and image_tag != 'latest'"
  }
~~~

**command line**

`clear.py autobuild del`

# 清理 Docker 私库镜像

*仅支持 v2 API*

- 利用 SQL 条件语句对 Docker 私库进行查询并删除。
- 删除孤立的 manifest。
- 回收磁盘空间

> Docker 私库的 Hash 和 Tag 都是找到一个 Manifest 的有效方法，但是，从 Image 是只能找到 Tag 的；另外对同一个 Tag 的重复 Push，并不会删除原有的 Manifest，这就造出一个只有 Hash 没有 Tag 的 Manifest。

---

用法: `clear.py sql_id action`

- **sql_id**: SQL 语句的条件部分，保存在 conf.json 中
- **action**:
	- del: 删除标签，并运行垃圾收集
	- none: 列表展示


## 配置

所有配置文件都保存在 conf.json 中

### registry

- url: 私库地址。
- base_path: 私库的目录，必须能被本脚本写入。

## 数据结构

The script will store image info into a in-memory sqlite database.

脚本用 SQLite 的内存数据库进行缓存

~~~sql
CREATE TABLE images
(id INTEGER PRIMARY KEY,image_name TEXT,
	tag_name TEXT, tag_timestamp INTEGER,
	tag_hash TEXT,tag_size INTEGER);

CREATE TABLE relations
(id INTEGER PRIMARY KEY,image_name TEXT,
	tag_name TEXT, blob_hash TEXT);

CREATE TABLE blobs
(id INTEGER PRIMARY KEY, blob_hash TEXT,
	blob_size INTEGER, blob_date INTEGER)

~~~



SQL 语句的条件会保存在 conf.json 文件中，

## 实例

### 删除 tag 叫 `dummy` 的镜像

**'conf.json'**:

~~~json
  "sql": {
    "dummy": " tag_name = 'dummy'"
  }
~~~

**命令行**

`clear.py dummy del`

###删除所有镜像名称类似 '%prod%'，但是 tag 不是'latest' 的镜像

**'conf.json'**:

~~~json
  "sql": {
    "autobuild": "image_name like '%prod%' and image_tag != 'latest'"
  }
~~~

**命令**

`clear.py autobuild del`
