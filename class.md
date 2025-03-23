
<!-- markdownlint-disable MD024 -->
# classes

进度：

 bug merge的时候， 
    postings_list 词项元数据 似乎有问题
    只存了 0 1  3  5 后面只有奇数
    解决了， 把 = 写成 += 了
bug 布尔查询结果有误，似乎索引没构建对。
    #TODO 还没解决

todo 索引压缩


待看：
    https://docs.python.org/3/library/contextlib.html
    https://docs.python.org/3/tutorial/controlflow.html#defining-functions


## IdMap 

维护 term(str) 与 termid 之间的映射
通过下标运算将str映射成id或反之。

### attr

str_to_id : dict
id_to_str : list

### core func

__init__:()
__getitem__ ：定义下标运算

## BSBIIndex

完成整个倒排索引构建的过程

### attr

term_id_map(IdMap): 词项与词项id的映射，(一直在内存中)
doc_id_map(IdMap): 文档名和文档id的映射, (一直在内存中)
data_dir(str): 到数据文件夹的路径
output_dir(str): 放索引文件的文件夹
index_name(str): 索引文件的名字
postings_encoding: 存放索引用的编码方式  

### core func 

index: 
    构建索引。先对块构建，然后合并
save : 
    存储词项、文档映射
load : 
    加载词项、文档映射
parse_block: 
    (数据文件夹到sdad块文件夹的相对路径)把块里的所有文件变成 termid-docid 元组;并维护词项、文档映射。
invert_write: 
    (td_pairs，index:InvertedIndexWriter)把 termid-docid 元组排序，做成倒排索引表，将倒排索引通过 InvertedIndexWriter 写入磁盘(用 append 部分地写入)
merge: 
    读取。。。合并

## InvertedIndex : 

    基类， 用来构建倒排索引.
    负责index 文件(.dict .index) 的管理

### attr

postings_dict : 
    key: termid
    value: 词项的元数据
    (在以byte存储的index文件中的起始位置，
    倒排表长度，
    以byte存储的长度)
terms : 
    没什么用，按添加顺序存词项id
index_file : 
    打开的文件(初始化时决定)
postings_encoding：
    编码方式

### core func

__init__ : 
    (索引文件名字， 编码方式， 索引所在文件夹)
__enter__: 
    ‘rb’ 打开索引文件 作为 self.index_file ;
        同时加载postings_dict , terms . 
__exit__ : 
    保存 postings_dict, terms

## InvertedIndexWriter(InvertedIndex): 

    提供将文件写入磁盘的办法。

### attr

postings_dict : 
    key: termid
    value: 词项的元数据
    (在以byte存储的index文件中的起始位置，
    倒排表长度，
    以byte存储的长度)
terms : 
    没什么用，按添加顺序存词项id
index_file : 
    打开的文件(初始化时决定)
postings_encoding：
    编码方式


### core func

__init__ : 
    (索引文件名字， 编码方式， 索引所在文件夹)
__enter__ :
    覆写基类的. 用'wb+'打开，文件若存在会被清空.
__exit__ : 
    保存 postings_dict, terms

append : 
    (term, postings_list) 将该 term 元数据添加进 postings_dict; 将 postings_list 以bytes数据附加到 index_file 末尾.


## InvertedIndexIterator 

    合并索引时, 用这个迭代器从块的索引里一个个地取出(term, postings_list) 元组

### attr

postings_dict : 
    词项的元数据
    (在以byte存储的index文件中的起始位置，
    倒排表长度，
    以byte存储的长度)
terms : 
    没什么用，按添加顺序存词项id
index_file : 
    打开的文件(初始化时决定)
postings_encoding：
    编码方式

### core func

    _initialization_hook: 初始化迭代器()
    __enter__ : 由于在里面调用基类的__enter__, 所以加载了postings_dict 和 terms




<!-- markdownlint-enable MD024 -->