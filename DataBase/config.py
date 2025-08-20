


TUPLE_DELIMITER,RECORD_DELIMITER,COMPLETION_DELIMITER = "##;", "###;", "####."

default_graph_config = {
    "entity_types": "组织、人物、日期",  # 实体类型
    "tuple_delimiter": TUPLE_DELIMITER,  # 元组分隔符
    "record_delimiter": RECORD_DELIMITER,  # 记录分隔符
    "completion_delimiter": COMPLETION_DELIMITER,  # 终止分隔符
    "input_text":""  # 输入文本
}


neo4j_config={

'uri':"neo4j://192.168.10.22:18802",
'user':"neo4j",
'password':"neo4jrag",
'database':"neo4j"   # 数据库名称

 }











