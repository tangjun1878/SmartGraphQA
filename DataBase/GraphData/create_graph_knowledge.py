from neo4j import GraphDatabase
from DataBase.config import  neo4j_config, TUPLE_DELIMITER,RECORD_DELIMITER,COMPLETION_DELIMITER
import json
# # Neo4j 连接配置
# uri = "neo4j://182.140.215.17:18802"
# user = "neo4j"
# password = "lightrag"
# database = "neo4j"
# 自定义分隔符
# TUPLE_DELIMITER,RECORD_DELIMITER,COMPLETION_DELIMITER = "##;", "###;", "####."

                              







# 原始数据（注意：这里保留原始格式）
raw_data = ['''
(entity{tuple_delimiter}费鲁扎巴德{tuple_delimiter}地理{tuple_delimiter}费鲁扎巴德将奥雷利亚人作为人质扣押)  
{record_delimiter}  
(entity{tuple_delimiter}奥雷利亚{tuple_delimiter}地理{tuple_delimiter}寻求释放人质的国家)  
{record_delimiter}  
(entity{tuple_delimiter}昆塔拉{tuple_delimiter}地理{tuple_delimiter}这里是我修改的内容，第二次修改)  
{record_delimiter}  
{record_delimiter}  
(entity{tuple_delimiter}蒂鲁齐亚{tuple_delimiter}地理{tuple_delimiter}费鲁扎巴德的首都，奥雷利亚人被关押的地方)  
{record_delimiter}  
(entity{tuple_delimiter}克罗哈拉{tuple_delimiter}地理{tuple_delimiter}昆塔拉的首都城市)  
{record_delimiter}  
(entity{tuple_delimiter}卡申{tuple_delimiter}地理{tuple_delimiter}奥雷利亚的首都城市)  
{record_delimiter}  
(entity{tuple_delimiter}萨缪尔·纳马拉{tuple_delimiter}人物{tuple_delimiter}曾在蒂鲁齐亚的阿尔哈米亚监狱服刑的奥雷利亚人)  
{record_delimiter}  
(entity{tuple_delimiter}阿尔哈米亚监狱{tuple_delimiter}地理{tuple_delimiter}位于蒂鲁齐亚的监狱)  
{record_delimiter}  
(entity{tuple_delimiter}杜尔克·巴塔格拉尼{tuple_delimiter}人物{tuple_delimiter}曾被扣为人质的奥雷利亚记者)  
{record_delimiter}  
(entity{tuple_delimiter}梅吉·塔兹巴{tuple_delimiter}人物{tuple_delimiter}布拉蒂纳斯国民和曾被扣为人质的环保主义者)  
{record_delimiter}  
(relationship{tuple_delimiter}费鲁扎巴德{tuple_delimiter}奥雷利亚{tuple_delimiter}费鲁扎巴德与奥雷利亚进行了人质交换谈判{tuple_delimiter}0.2)  
{record_delimiter}  
(relationship{tuple_delimiter}昆塔拉{tuple_delimiter}奥雷利亚{tuple_delimiter}昆塔拉促成了费鲁扎巴德和奥雷利亚之间的人质交换{tuple_delimiter}0.2)  
{record_delimiter}  
(relationship{tuple_delimiter}昆塔拉{tuple_delimiter}费鲁扎巴德{tuple_delimiter}昆塔拉促成了费鲁扎巴德和奥雷利亚之间的人质交换{tuple_delimiter}0.2)  
{record_delimiter}  
(relationship{tuple_delimiter}萨缪尔·纳马拉{tuple_delimiter}阿尔哈米亚监狱{tuple_delimiter}萨缪尔·纳马拉是阿尔哈米亚监狱的囚犯{tuple_delimiter}0.8)  
{record_delimiter}  
(relationship{tuple_delimiter}萨缪尔·纳马拉{tuple_delimiter}梅吉·塔兹巴{tuple_delimiter}萨缪尔·纳马拉和梅吉·塔兹巴在同一次人质释放中被交换{tuple_delimiter}0.2)  
{record_delimiter}  
(relationship{tuple_delimiter}萨缪尔·纳马拉{tuple_delimiter}杜尔克·巴塔格拉尼{tuple_delimiter}萨缪尔·纳马拉和杜尔克·巴塔格拉尼在同一次人质释放中被交换{tuple_delimiter}0.2)  
{record_delimiter}  
(relationship{tuple_delimiter}梅吉·塔兹巴{tuple_delimiter}杜尔克·巴塔格拉尼{tuple_delimiter}梅吉·塔兹巴和杜尔克·巴塔格拉尼在同一次人质释放中被交换{tuple_delimiter}0.2)  
{record_delimiter}  
(relationship{tuple_delimiter}萨缪尔·纳马拉{tuple_delimiter}费鲁扎巴德{tuple_delimiter}萨缪尔·纳马拉是费鲁扎巴德的人质{tuple_delimiter}0.2)  
{record_delimiter}  
(relationship{tuple_delimiter}梅吉·塔兹巴{tuple_delimiter}费鲁扎巴德{tuple_delimiter}梅吉·塔兹巴是费鲁扎巴德的人质{tuple_delimiter}0.2)  
{record_delimiter}  
(relationship{tuple_delimiter}杜尔克·巴塔格拉尼{tuple_delimiter}费鲁扎巴德{tuple_delimiter}杜尔克·巴塔格拉尼是费鲁扎巴德的人质{tuple_delimiter}0.2)  
{completion_delimiter}

'''.format(
    tuple_delimiter=TUPLE_DELIMITER,
    record_delimiter=RECORD_DELIMITER,
    completion_delimiter=COMPLETION_DELIMITER
),
'''
(entity{tuple_delimiter}TECHGLOBAL{tuple_delimiter}组织{tuple_delimiter}TechGlobal 是目前在环球交易所上市的一只股票，它为85%的高端智能手机提供动力)
{record_delimiter}
(entity{tuple_delimiter}VISION HOLDINGS{tuple_delimiter}组织{tuple_delimiter}Vision Holdings 是一家之前拥有 TechGlobal 的公司)
{record_delimiter}
(relationship{tuple_delimiter}TECHGLOBAL{tuple_delimiter}VISION HOLDINGS{tuple_delimiter}Vision Holdings 从2014年至今曾拥有 TechGlobal{tuple_delimiter}0.5)
{completion_delimiter}
'''.format(
    tuple_delimiter=TUPLE_DELIMITER,
    record_delimiter=RECORD_DELIMITER,
    completion_delimiter=COMPLETION_DELIMITER
    )

]












class TripleDataParser:
    """
    三元组数据解析器：从大模型输出中提取实体和关系，并附加上下文元数据。
    支持批量累积解析。
    """
    def __init__(self, tuple_delimiter, record_delimiter,completion_delimiter ):
        self.completion_delimiter = completion_delimiter
        self.record_delimiter = record_delimiter
        self.tuple_delimiter = tuple_delimiter
        self.batch_count = 0  # 记录已处理的 batch 数量
        self._buffer = []     # 缓存待处理的数据
        self.fail_records=[]

    def parse_data(self, data_lst):
        """
        解析三元组提取的内容，加工成 graph 需要的格式。
        """
        entities = []
        relationships = []

        for item in data_lst:
            # 提取附加字段，统一添加 entity_ 前缀
            metadata = {f"entity_{k}": v for k, v in item.items() if k != "graph_text"}
            raw_text = item["graph_text"].replace(self.completion_delimiter, "")
            
            # 分割为有效记录
            records = filter(None, (r.strip() for r in raw_text.split(self.record_delimiter)))
            
            for record in records:
                # 去除最外层括号
                content = record.strip()[1:-1] if record.strip().startswith('(') else record.strip()
                parts = [p.strip() for p in content.split(self.tuple_delimiter)]
                
                if not parts:
                    continue

                prefix = parts[0]
                if prefix == "entity":
                    try:
                        entity = {
                            "entity_name": parts[1],
                            "entity_type": parts[2],
                            "entity_description": parts[3],
                            **metadata  # 合并附加字段
                        }
                        entities.append(entity)
                    except:
                        self.fail_records.append(parts)
                        print("{}-->写入实体失败！".format(parts))

                elif prefix == "relationship":
                    try:
                        relationshape = {
                            "source_entity": parts[1],
                            "target_entity": parts[2],
                            "relationship_description": parts[3],
                            "relationship_strength": float(json.loads(parts[4]))
                        }
                        
                        relationships.append( relationshape )
                    except:
                        self.fail_records.append(parts)
                        print("{}-->写入关系失败！".format(parts))


        return entities, relationships

    def batch_parse_data(self, item, batch=4):
        """
        累积数据直到达到 batch 大小，然后调用 parse_data 进行处理。
        
        参数:
            item (dict): 单条数据，包含 graph_text 和其他元数据
            batch (int): 批处理大小，默认为 4
        
        返回:
            tuple: 如果达到 batch 大小，返回 (entities, relationships)；
                   否则返回 (None, None)
        """
        # 将当前 item 添加到缓冲区
        self._buffer.append(item)
        
        # 检查是否达到 batch 大小
        if len(self._buffer) >= batch:
            # 调用 parse_data 处理当前 batch
            entities, relationships = self.parse_data(self._buffer)
            # 重置缓冲区
            self._buffer = []
            # 增加 batch 计数
            self.batch_count += 1
            return entities, relationships
        else:
            # 还未达到 batch，不处理，返回空
            return None, None

    def flush(self):
        """
        强制处理剩余缓冲区中的数据（例如循环结束后调用）
        """
        if self._buffer:
            entities, relationships = self.parse_data(self._buffer)
            self._buffer = []
            self.batch_count += 1
            return entities, relationships
        return None, None

    def check_failed_extract(self):
        if self.fail_records:
            print("部分为写入，其记录如下：\n")
            print(self.fail_records)
        else:
            print('全部写入，提取成功！')




# ✅ 使用 Class 实现写入 Neo4j
class Neo4jGraphData:
    """
    初始化连接neo4j数据库,给到默认数据库名self.database,伴随数据库写入、查询、删除功能，如果不指定就是操作默认数据库。
    ①实体写入根据字典统一嵌入属性(命名必须是entity_属性名);
    ②删除必须是实体名称；
    ③写入实体或关系最好给更多批量，提高写入效率；
    ④关系暂时是固定内容，包含"source_entity","target_entity","relationship_description","relationship_strength";
    """
    def __init__(self, uri, user, password, database="neo4j"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database

    def close(self):
        """关闭数据库连接"""
        self.driver.close()


    def _create_entities1(self, tx, entities):
        """
        创建实体节点，自动提取 entity_xxx 字段作为属性,将原来（下面所示）内容替换，这样具有所有属性都可以给到实体，使其更灵活了。
        #tx.run(
        #        MERGE (e:Entity {name: $name})
        #        SET e.type = $type, e.description = $description
        #   ,
        #        name=entity["entity_name"],
        #        type=entity["entity_type"],
        #        description=entity["entity_description"]
        #        )
        """
        for entity in entities:
            # 提取 entity_ 开头的字段，转为节点属性（去掉前缀）
            props = {k[7:]: v for k, v in entity.items() if k.startswith("entity_")}
            
            if "name" not in props:
                raise ValueError(f"实体缺少 name 属性: {entity}")

            set_clause = ", ".join(f"e.{k} = ${k}" for k in props if k != "name")
            cypher = f"MERGE (e:Entity {{name: $name}}) {'SET ' + set_clause if set_clause else ''}"

            tx.run(cypher, **props)


    def _create_entities1(self, tx, entities):
        """
        创建或合并实体节点。
        - 若实体不存在：创建并设置所有属性。
        - 若实体存在：
            - 与旧值拼接（用 '; ' 分隔，自动去重空值）
 
        """
        cypher = """

        MERGE (e:Entity {name: $name})
        WITH e, $props AS props
        UNWIND keys(props) AS key
        WITH e, key, props[key] AS new_val, properties(e)[key] AS old_val
        WHERE key <> 'name'  // name 不参与合并

        WITH e, key, old_val, trim(new_val) AS trimmed_new_val, trim(old_val) AS trimmed_old_val
        WITH e, key, old_val, trimmed_new_val, trimmed_old_val,
            split(trimmed_old_val, '#; ') AS old_vals_array
        WITH e, key,
            CASE 
                // 旧值不存在或为空时，直接使用新值
                WHEN old_val IS NULL OR trimmed_old_val = '' THEN trimmed_new_val
                // 旧值存在且新值已在旧值中，保持旧值
                WHEN trimmed_new_val IN old_vals_array THEN trimmed_old_val
                // 旧值存在且新值不在旧值中，进行合并
                ELSE trimmed_old_val + '#; ' + trimmed_new_val
            END AS final_val

        // 设置最终值
        SET e[key] = final_val

        """

        for entity in entities:
            # 提取 entity_ 前缀属性（去掉前缀）
            props = {k[7:]: v for k, v in entity.items() if k.startswith("entity_")}
            
            if "name" not in props:
                raise ValueError(f"实体缺少必填主键 'name'：{entity}")
            
            # 执行合并逻辑
            tx.run(cypher, name=props["name"], props=props)

    def _create_entities(self, tx, entities):
        """
        创建或合并实体节点。
        - 若实体不存在：创建并设置所有属性。
        - 若实体存在：
            - 与旧值拼接（用 '; ' 分隔，自动去重空值）
        使用APOC库的apoc.create.setProperty处理动态属性设置
        """
        cypher = """
        MERGE (e:Entity {name: $name})
        WITH e, $props AS props
        UNWIND keys(props) AS key
        WITH e, key, props[key] AS new_val, properties(e)[key] AS old_val
        WHERE key <> 'name'  // name 不参与合并

        // 处理空值和修剪空格
        WITH e, key, 
             old_val, 
             trim(new_val) AS trimmed_new_val, 
             trim(COALESCE(old_val, '')) AS trimmed_old_val
             
        // 拆分旧值为数组用于去重检查
        WITH e, key, 
             trimmed_new_val, 
             trimmed_old_val,
             split(trimmed_old_val, '#; ') AS old_vals_array
             
        // 计算最终值
        WITH e, key,
             CASE 
                 // 旧值不存在或为空时，直接使用新值
                 WHEN trimmed_old_val = '' THEN trimmed_new_val
                 // 旧值存在且新值已在旧值中，保持旧值
                 WHEN trimmed_new_val IN old_vals_array THEN trimmed_old_val
                 // 旧值存在且新值不在旧值中，进行合并
                 ELSE apoc.text.join([trimmed_old_val, trimmed_new_val], '#; ')
             END AS final_val
             
        // 使用APOC设置属性，处理动态属性名更可靠
        CALL apoc.create.setProperty(e, key, final_val) YIELD node
        SET e = node  // 将更新后的节点属性写回原节点
        """

        for entity in entities:
            # 提取 entity_ 前缀属性（去掉前缀）
            props = {k[7:]: v for k, v in entity.items() if k.startswith("entity_")}
            
            if "name" not in props:
                raise ValueError(f"实体缺少必填主键 'name'：{entity}")
            
            # 处理可能的None值，转换为空字符串
            for key, value in props.items():
                if value is None:
                    props[key] = ""
            
            # 执行合并逻辑
            tx.run(cypher, name=props["name"], props=props)
    



    def _create_relationships(self, tx, relationships):
        """创建实体之间的关系，如果需要添加其它属性，通过SET r.description = $description, r.strength = $strength设置"""
        for rel in relationships:
            tx.run("""
                MATCH (a:Entity {name: $source})
                MATCH (b:Entity {name: $target})
                MERGE (a)-[r:relationships]->(b)
                SET r.description = $description, r.strength = $strength
            """,
                source=rel["source_entity"],
                target=rel["target_entity"],
                description=rel["relationship_description"],
                strength=rel["relationship_strength"]
            )

    
    def write_entities_and_relationships(self, entities=None, relationships=None,database=None):
        """写入实体和关系,利用if使代码更稳健"""
        if entities is None and relationships is None:
            print('没有实体和关系')
            return 
        graph_database = self.database if database is None else database  # 选择性执行不同数据库操作
        with self.driver.session(database = graph_database) as session:
            if entities is not None:
                session.write_transaction(self._create_entities, entities)
            if relationships is not None:
                session.write_transaction(self._create_relationships, relationships)
        print("✅ 实体和关系已成功写入 Neo4j")
    
    
    def delete_entity_by_name(self, entity_name: str,database=None):
        """
        根据实体名称删除该实体及其所有相关的关系
        使用 DETACH DELETE：自动删除节点和其所有关系
        :param entity_name: 要删除的实体名称
        """
        cypher = """
        MATCH (e:Entity {name: $name})
        DETACH DELETE e
        """
        graph_database = self.database if database is None else database  # 选择性执行不同数据库操作
        try:
            with self.driver.session(database=graph_database) as session:
                result = session.run(cypher, name=entity_name)
                summary = result.consume()  # 获取执行摘要

            # 检查是否真的删除了
            with self.driver.session(database=self.database) as session:
                check = session.run(
                    "MATCH (e:Entity {name: $name}) RETURN 1 AS found LIMIT 1",
                    name=entity_name
                ).single()

            if check:
                print(f"⚠️  删除操作未生效：实体 '{entity_name}' 仍存在（可能权限不足或已被手动删除）。")
            else:
                print(f"✅ 实体 '{entity_name}' 及其所有相关关系已成功删除。")

        except Exception as e:
            print(f"❌ 删除实体 '{entity_name}' 时发生错误：{str(e)}")


def write_graph(batch=4):

    dataparse = TripleDataParser(TUPLE_DELIMITER,RECORD_DELIMITER,COMPLETION_DELIMITER)
    graph = Neo4jGraphData(neo4j_config['uri'], neo4j_config['user'], neo4j_config['password'], neo4j_config['database'])


    data_demo = [{"graph_text":raw_data[0],"page":"20","import":"增加" },
        {"graph_text":raw_data[1],"page":"20", },

    ]



    for extract_graph_text in data_demo:
        entities, relationships = dataparse.batch_parse_data(extract_graph_text, batch=batch)
        graph.write_entities_and_relationships(entities, relationships)

    if dataparse._buffer:
        entities, relationships = dataparse.flush()
        graph.write_entities_and_relationships(entities, relationships)
    
    graph.close() # 关闭数据库连接
    


if __name__ == "__main__":
    


    write_graph(batch=4)

