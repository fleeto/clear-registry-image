# Clear registry images

*v2 API only*

## known issues

When there is only one tag of an image, del operation will remove the tag, but the image remains here, and its tag list will be null.

---

Usage: `clear.py sql_id action`

- **sql_id**: It's conditions will be used to filter the images.
- **action**:
	- del: remove the tags , and run gc.
	- none: list view.

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

# Docker 私库镜像

*仅支持 v2 API*

## 已知问题


如果私库中的某个镜像仅有一个 Tag，对其进行删除操作的后果是，镜像还在，缺没有 Tag。

---

用法: `clear.py sql_id action`

- **sql_id**: SQL 语句的条件部分，保存在 conf.json 中
- **action**:
	- del: 删除标签，并运行垃圾收集
	- none: 列表展示


## 数据结构

脚本用 SQLite 的内存数据库进行缓存

~~~sql

CREATE TABLE images (id INTEGER PRIMARY KEY,image_name TEXT, tag_name TEXT, tag_timestamp INTEGER, tag_hash TEXT,tag_size INTEGER);

CREATE TABLE relations (id INTEGER PRIMARY KEY,image_name TEXT, tag_name TEXT, blob_hash TEXT);

CREATE TABLE blobs (id INTEGER PRIMARY KEY, blob_hash TEXT, blob_size INTEGER, blob_date INTEGER)

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
