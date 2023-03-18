#coding=utf-8
"""
    @Author：nonpricklycactus
    @File： writeUpdataDatabase.py.py
    @Date：2023/3/18 19:50
    @Describe: 
"""
import sqlite3
import re

def check(str):
    my_re = re.compile(r'[A-Za-z]', re.S)
    res = re.findall(my_re, str)
    if len(res):
        return True
    else:
        return False



def readMd(pathUrl,tagList):
    with open(pathUrl,encoding = 'utf-8') as f:
        lines = f.readlines()
    lines = [i.strip() for i in lines]
    flag = False
    for lin in lines:
        if "原始标签" in lin:
            flag = True
        if flag:
            lin = lin.replace('<br>', '')
            lin = lin.replace('\'', '\'\'')
            taglist = lin.split("|")
            taglist = [i for i in taglist if (i != '' and i != '  ')]
            if not len(taglist)<2:
                if check(taglist[0]):
                    tagList.append(taglist)

def insertTags(conn,tableName,tags):
    c = conn.cursor()
    tagsMap=fillChara(tags)
    comment = "INSERT INTO {table}('raw','name','intro','links') VALUES('{raw}', '{name}','{intro}','{links}')".format(
        table=tableName, raw=tags[0].strip(), name=tagsMap["name"], intro=tagsMap["intro"], links=tagsMap["links"])
    print(comment)
    try:
        c.execute(comment)
        conn.commit()
    except:
        wr = open('databaseLog.txt', mode='a', encoding='utf8')
        wr.write(comment + "\n")  # write 写入
        wr.close()

def fillChara(tags):
    tagMap = {
        "raw": "",
        "name": "",
        "intro": "",
        "links": ""
    }
    tagMap["raw"] = tags[0]
    if len(tags) == 2:
        tagMap["name"] = tags[1].strip()
        tagMap["intro"] = ""
        tagMap["links"] = ""
    elif len(tags) == 3:
        tagMap["name"] = tags[1].strip()
        tagMap["intro"] = tags[2].strip()
        tagMap["links"] = ""
    else:
        tagMap["name"] = tags[1].strip()
        tagMap["intro"] = tags[2].strip()
        tagMap["links"] = tags[3].strip()
    return tagMap

def updataTags(conn,tableName,tags):
    c = conn.cursor()
    tagsMap=fillChara(tags)
    comment = "UPDATE {table} SET name='{name}',intro='{intro}',links='{links}' WHERE raw='{raw}';".format(
        table=tableName, raw=tags[0].strip(), name=tagsMap["name"], intro=tagsMap["intro"], links=tagsMap["links"])
    print(comment)
    try:
        c.execute(comment)
        conn.commit()
    except:
        wr = open('databaseLog.txt', mode='a', encoding='utf8')
        wr.write(comment + "\n")  # write 写入
        wr.close()

def updataDB(conn,tableName,tagList):
    for tags in tagList:
        mycursor = conn.cursor()
        sqlExe = "select raw,name,intro,links from " + tableName + " where raw = '" + tags[0].strip() + "'"
        mycursor.execute(sqlExe)
        myresult = mycursor.fetchall()  # fetchall() 获取所有记录
        if len(myresult)<=0:
            insertTags(conn,tableName,tags)
            continue
        oldTags = []
        for i in myresult[0]:
            if i != "":
                oldTags.append(i)
        if len(oldTags)==len(tags):
            for i in range(0,len(tags)):
                if(oldTags[i]!=tags[i].strip()):
                    updataTags(conn,tableName,tags)
                    break
        else:
            updataTags(conn,tableName,tags)

if __name__ == '__main__':
    mdNames = ["artist","character","cosplayer","female","group","male","mixed","parody"]
    sqlitUrl = "F:\RemoteCode\Ehentai_metadata\EhTagTranslation.db"
    DataBaseUrl = "F:\RemoteCode\Database\database\\"
    conn = sqlite3.connect(sqlitUrl)

    for md in mdNames:
        tags = []
        mdName = md + ".md"
        if md == "group":
            tableName = "groups"
        else:
            tableName = md
        readMd(DataBaseUrl + mdName, tags)
        updataDB(conn,tableName,tags)

    conn.close()