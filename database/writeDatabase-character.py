import sqlite3
import re


def check(str):
    my_re = re.compile(r'[A-Za-z]', re.S)
    res = re.findall(my_re, str)
    if len(res):
        return True
    else:
        return False



def readMd(pathurl,list):
    with open(pathurl,encoding = 'utf-8') as f:
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
                   # print(taglist)
                    list.append(taglist)

def getValue(value,i):
    try:
        return value[i]
    except:
        return ""


def createTable(conn,tableName):
    c = conn.cursor()
    createCommit1 = "DROP TABLE IF EXISTS {table}".format(table = tableName)
    c.execute(createCommit1)
    conn.commit()
    createCommit2 = "CREATE TABLE {table} (id integer PRIMARY KEY AUTOINCREMENT,raw CHAR(50) NOT NULL,name CHAR(50) NOT NULL,intro TEXT, links TEXT, UNIQUE (raw ASC));".format(table = tableName)
    c.execute(createCommit2)
    conn.commit()


def addDatabase(conn,list,tableName):
    c = conn.cursor()
    #str_word_keyword = 'hell0, word！{a},{b}'.format(b='张三', a='李四')
    for value in list:
        raw = getValue(value, 0).strip()
        name = getValue(value, 1).strip()
        if " \\" in name:
            print(name)
            name = name.replace(" \\","")
        intro = getValue(value, 2).strip()
        links = getValue(value, 3).strip()
        comment = "INSERT INTO {table}('raw','name','intro','links') VALUES('{raw}', '{name}','{intro}','{links}')".format(table = tableName,raw = raw,name = name,intro = intro,links = links)
        print(comment)
        try:
           c.execute(comment)
           conn.commit()
        except:
            wr = open('databaseLog.txt', mode='a', encoding='utf8')
            wr.write(comment + "\n")  # write 写入
            wr.close()


def addNewDatabase(conn):
    c = conn.cursor()
    with open("NewDataBase",encoding = 'utf-8') as f:
        lines = f.readlines()
    lines = [i.strip() for i in lines]
    for line in lines:
        tags = line.split(":")
        tableArrs = tags[1].split("-")
        tableName = tags[0].strip()
        raw = tableArrs[0].strip()
        name = tableArrs[1].strip()
        comment = "INSERT INTO {table}('raw','name','intro','links') VALUES('{raw}', '{name}','{intro}','{links}')".format(
            table=tableName, raw=raw, name=name, intro="", links="")
        print(comment)
        try:
           c.execute(comment)
           conn.commit()
        except:
            wr = open('databaseLog.txt', mode='a', encoding='utf8')
            wr.write(comment + "\n")  # write 写入
            wr.close()








if __name__ == '__main__':
    mdNames = ["character"]
    sqlitUrl = "F:\RemoteCode\Ehentai_metadata\EhTagTranslation.db"
    DataBaseUrl = "F:\RemoteCode\Database\database\\"
    updataFlag = False
    conn = sqlite3.connect(sqlitUrl)

    if not updataFlag:
        for md in mdNames:
            list = []
            mdName = md+".md"
            if md == "group":
                tableName = "groups"
            else:
                tableName = md
            readMd(DataBaseUrl+mdName,list)
            createTable(conn,tableName)
            addDatabase(conn,list,tableName)
    else:
        addNewDatabase(conn)

    conn.close()
    #updataDatabase(sqlitUrl,list,"artist")

