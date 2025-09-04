

"""
文件名：graph_prompt.py
作者：汤军
邮箱：511026664@qq.com
日期：2025-07-25
描述：根据前沿论文和代码总结构建知识图谱的提示词。

"""

""" 实体和关系提取默认参数模板+调用示例
graph_extraction_parameter = {
    "entity_types": "组织、人物、日期",  # 实体类型
    "tuple_delimiter": "#zhhn#",  # 元组分隔符
    "record_delimiter": "\n---\n",  # 记录分隔符
    "completion_delimiter": "###END###",  # 终止分隔符
    "input_text":""  # 输入文本
}

graph_extraction_content=graph_extraction.format(**graph_extraction_parameter)
print(graph_extraction_content)

"""


from DataBase.config import TUPLE_DELIMITER,RECORD_DELIMITER,COMPLETION_DELIMITER

# TUPLE_DELIMITER,RECORD_DELIMITER,COMPLETION_DELIMITER = "##;", "###;", "####."

graph_extraction_parameter_default = {
    "entity_types": "组织、人物、日期",  # 实体类型
    "tuple_delimiter": TUPLE_DELIMITER,  # 元组分隔符
    "record_delimiter": RECORD_DELIMITER,  # 记录分隔符
    "completion_delimiter": COMPLETION_DELIMITER,  # 终止分隔符
    "input_text":""  # 输入文本
}


system_prompt = """
    你是一个专业的知识图谱构建助手，擅长从自然语言文本中精确提取结构化三元组。请严格遵循用户要求，不要添加任何解释或额外内容,严格遵循用户格式要求。/no_think。
    """
graph_extraction = """
-目标-
给定一个可能与本活动相关的文本文件和一个实体类型列表，识别文本中的所有实体类型以及这些实体之间的所有关系。

-步骤-
1. 识别所有实体。对于每个已识别的实体，提取以下信息：
- entity_name：实体的名称
- entity_type：以下类型之一：[{entity_types}]
- entity_description：对实体的属性和活动的全面描述
将每个实体格式化为 (entity{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_description>)

2. 从步骤1中识别的实体中，找出所有明显相互关联的（source_entity, target_entity）对。
对于每对相关实体，提取以下信息：
- source_entity：源实体的名称，如步骤1中所标识的
- target_entity：目标实体的名称，如步骤1中所标识的
- relationship_description：解释为什么认为源实体和目标实体之间有关联
- relationship_strength：表示源实体和目标实体之间关系强度的数值分数,取值范围[0,1],数值分数越大关联越强
将每种关系格式化为 (relationship{tuple_delimiter}<source_entity>{tuple_delimiter}<target_entity>{tuple_delimiter}<relationship_description>{tuple_delimiter}<relationship_strength>)

3. 返回步骤1和2中识别的所有实体和关系的列表。使用**{record_delimiter}**作为列表分隔符。

4. 完成后，输出 {completion_delimiter}

######################
-示例-
######################

示例1：
Entity_types: 组织、人物、日期
Text:
Verdantis的中央机构计划于周一和周四举行会议，并计划于周四下午1:30（太平洋夏令时）发布其最新政策决定，随后将举行新闻发布会，届时中央机构主席Martin Smith将回答记者提问。投资者预计市场战略委员会将把基准利率维持在3.5%-3.75%的区间内。
Output:
(entity{tuple_delimiter}中央机构{tuple_delimiter}组织{tuple_delimiter}中央机构是Verdantis的联邦储备银行，它将在周一和周四制定利率)
{record_delimiter}
(entity{tuple_delimiter}马丁·史密斯{tuple_delimiter}人物{tuple_delimiter}马丁·史密斯是中央机构的主席)
{record_delimiter}
(entity{tuple_delimiter}市场战略委员会{tuple_delimiter}组织{tuple_delimiter}市场战略委员会是中央机构的一个委员会，负责就利率及Verdantis货币供应量的增长作出关键决策)
{record_delimiter}
(relationship{tuple_delimiter}马丁·史密斯{tuple_delimiter}中央机构{tuple_delimiter}马丁·史密斯是中央机构的主席，并将在新闻发布会上回答问题{tuple_delimiter}9)
{completion_delimiter}

######################
示例2:
Entity_types: 组织、人物、日期
Text:
7月12日，印发《关于刘继美退休的通知》，刘继美到龄退休。
######################
Output:
(entity{tuple_delimiter}"7月12日"{tuple_delimiter}"时间"{tuple_delimiter}"《关于刘继美退休的通知》印发的日期。")  
{record_delimiter}  
(entity{tuple_delimiter}"刘继美"{tuple_delimiter}"人物"{tuple_delimiter}"被通知退休的人员，因达到法定退休年龄而正式退休。")  
{record_delimiter}  
(entity{tuple_delimiter}"《关于刘继美退休的通知》"{tuple_delimiter}"文件"{tuple_delimiter}"由相关单位印发，正式宣布刘继美退休的公文。")  
{record_delimiter}  
(relationship{tuple_delimiter}"7月12日"{tuple_delimiter}"《关于刘继美退休的通知》"{tuple_delimiter}"《关于刘继美退休的通知》于7月12日印发。"{tuple_delimiter}"1.0")  
{record_delimiter}  
(relationship{tuple_delimiter}"《关于刘继美退休的通知》"{tuple_delimiter}"刘继美"{tuple_delimiter}"该通知是关于刘继美退休事项发布的正式文件。"{tuple_delimiter}"1.0")  
{record_delimiter}  
(relationship{tuple_delimiter}"7月12日"{tuple_delimiter}"刘继美"{tuple_delimiter}"刘继美于7月12日被正式通知到龄退休。"{tuple_delimiter}"1.0")  
{completion_delimiter}

######################
示例 3：
Entity_types: 组织
Text:
周四，TechGlobal（TG）在环球交易所（Global Exchange）上市首日股价飙升。但首次公开募股（IPO）专家警告称，这家半导体公司的公开市场首秀并不能代表其他新上市公司的表现。

TechGlobal 之前是一家上市公司，2014年被 Vision Holdings 私有化。这家知名的芯片设计公司表示，其产品为85%的高端智能手机提供动力。
######################
Output:
(entity{tuple_delimiter}TECHGLOBAL{tuple_delimiter}组织{tuple_delimiter}TechGlobal 是目前在环球交易所上市的一只股票，它为85%的高端智能手机提供动力)
{record_delimiter}
(entity{tuple_delimiter}VISION HOLDINGS{tuple_delimiter}组织{tuple_delimiter}Vision Holdings 是一家之前拥有 TechGlobal 的公司)
{record_delimiter}
(relationship{tuple_delimiter}TECHGLOBAL{tuple_delimiter}VISION HOLDINGS{tuple_delimiter}Vision Holdings 从2014年至今曾拥有 TechGlobal{tuple_delimiter}0.5)
{completion_delimiter}

######################
示例4：  
Entity_types: 组织、地理、人物  
Text:  
五名奥雷利亚人在费鲁扎巴德被监禁了8年，被广泛视为人质，现在正返回奥雷利亚的途中。  

这次交换是由昆塔拉精心安排的，在80亿美元的费鲁齐资金被转移到昆塔拉首都克罗哈拉的金融机构时完成。  

这次交换始于费鲁扎巴德的首都蒂鲁齐亚，导致四名男子和一名女子（他们也是费鲁齐公民）登上一架包机飞往克罗哈拉。  

他们在克罗哈拉受到奥雷利亚高级官员的欢迎，现在正前往奥雷利亚的首都卡申。  

这些奥雷利亚人包括39岁的商人萨缪尔·纳马拉，他曾被关押在蒂鲁齐亚的阿尔哈米亚监狱，以及59岁的记者杜尔克·巴塔格拉尼和53岁的环保主义者梅吉·塔兹巴，塔兹巴还拥有布拉蒂纳斯国籍。  
######################
Output: 
(entity{tuple_delimiter}费鲁扎巴德{tuple_delimiter}地理{tuple_delimiter}费鲁扎巴德将奥雷利亚人作为人质扣押)  
{record_delimiter}  
(entity{tuple_delimiter}奥雷利亚{tuple_delimiter}地理{tuple_delimiter}寻求释放人质的国家)  
{record_delimiter}  
(entity{tuple_delimiter}昆塔拉{tuple_delimiter}地理{tuple_delimiter}协商用资金交换人质的国家)  
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
######################
-Real Data-
######################
Entity_types: {entity_types}
Text: {input_text}
######################
Output:

"""










