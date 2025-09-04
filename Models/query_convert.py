import os
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

#****************************************************************调用语言LLM模型模块************************************************************#
# 假设 Models.LLM_Models 中已实现 build_model(), invoke(), stream_invoke()
from LLM_Models import build_model, invoke


# 加载语言模型
ll_model = build_model(mode="deepseek_1.5b")

#****************************************************************Step 1: 问题分解链**************************************************************#

# 创建 Prompt 模板
sub_question_prompt = PromptTemplate.from_template("""
    你是一个问题分解器。请将以下复杂问题分解为若干个子问题：

    问题：{question}

    输出格式：
    - 子问题1
    - 子问题2
    - ...
    """)

# 构建 LLM 链式调用器
sub_question_chain = LLMChain(llm=ll_model, prompt=sub_question_prompt)



#****************************************************************Step 2: 子问题回答链**************************************************************#
answer_prompt = PromptTemplate.from_template("请回答以下问题：{question}")
answer_chain = LLMChain(llm=ll_model, prompt=answer_prompt)


#****************************************************************Step 3: 将问题拆解封装为函数*******************************************************#
def decompose_question(question: str) -> list:
    """
    将复杂问题分解为多个子问题。
    
    参数：
        question (str): 用户提出的复杂问题。

    返回：
        List[str]: 分解后的子问题列表。
    """
    print(f"[函数] 正在分解问题：{question}")
    
    # 使用 LLMChain 来执行问题分解
    sub_questions_text = sub_question_chain.invoke({"question": question})["text"]
    
    # 提取子问题列表
    sub_questions = [q.strip() for q in sub_questions_text.strip().split("\n") if q.startswith("-")]
    sub_questions = [q[2:] for q in sub_questions]  # 去掉 "- " 前缀
    
    print("[函数] 分解完成，子问题如下：")
    for i, sq in enumerate(sub_questions):
        print(f"  子问题 {i+1}: {sq}")

    return sub_questions


#****************************************************************Step 4: 主函数模块 - 自动分解 + 查询 + 整合****************************************#

def answer_complex_question(question):
    print(f"原始问题：{question}\n")
    # Step A: 使用函数分解问题
    sub_questions = decompose_question(question)

    # Step B: 并行查询每个子问题的答案（此处为串行，方便调试）
    sub_answers = []
    for i, sq in enumerate(sub_questions):
        print(f"\n子问题{i+1}: {sq}")
        ans = answer_chain.invoke({"question": sq})["text"]
        print(f"回答{i+1}: {ans}")
        sub_answers.append(ans)

    # Step C: 整合答案
    final_answer_prompt = PromptTemplate.from_template("""
以下是各个子问题的回答，请整合成一个完整的、自然流畅的回答：

{"sub_questions": {sub_questions}, "sub_answers": {sub_answers}}
""")
    final_answer_chain = LLMChain(llm=ll_model, prompt=final_answer_prompt)
    final_response = final_answer_chain.invoke({
        "sub_questions": sub_questions,
        "sub_answers": sub_answers
    })["text"]

    return final_response


#****************************************************************示例运行*************************************************************************#

if __name__ == "__main__":
    user_question = "太阳能的发展历史及其在现代社会中的应用有哪些？"
    result = answer_complex_question(user_question)
    print("\n最终整合后的回答：")
    print(result)