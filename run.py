import streamlit as st
import altair as alt
import numpy as np
import pandas as pd

# 设置页面标题
st.title("超星题目分析小工具")
st.markdown(
    "<p style='text-align: left; color: red;'>川哥做的小工具。只能分析普通的选择题和填空题，不能分析大题。因为我用不上。</p>",
    unsafe_allow_html=True)

# 上传Excel文件
uploaded_file = st.file_uploader("请上传错题分析的Excel文件:", type=['xlsx'])

if uploaded_file is not None:
    # 读取上传的文件，强制所有列为字符串
    df = pd.read_excel(uploaded_file, dtype=str, keep_default_na=False)

    results = []

    # 从第三列开始处理题目（索引从0开始，所以第3列是索引2）
    for col_idx in range(2, len(df.columns)):
        question_col = df.columns[col_idx]

        # 使用列名作为题目标识（因第一行无题干）
        question_content = question_col

        # 获取标准答案（第一行）
        standard_answer = df.iloc[0][question_col]
        # 处理全角和半角冒号
        import re
        pattern = re.compile(r'[:：]')
        parts = pattern.split(str(standard_answer))
        if len(parts) > 1:
            standard_answer_str = parts[-1].strip()
        else:
            standard_answer_str = parts[0].strip()

        # 获取学生答案（从第十六行开始），过滤掉空答案
        student_answers = df.iloc[15:][question_col]
        valid_answers = student_answers[student_answers.str.strip() != ""].copy()

        # 如果没有有效答案，跳过该题目
        if valid_answers.empty:
            continue

        # 统计答案分布
        result = valid_answers.value_counts().reset_index()
        result.columns = ['答案', '出现次数']

        # 添加学生姓名列
        result['学生'] = result['答案'].apply(lambda x: ', '.join(
            df[(df[question_col] == x) & (df.index >= 15)]['学生姓名'].astype(str)))

        # 统计正确答案数量
        correct_count = (valid_answers.astype(str) == standard_answer_str).sum()

        # 计算有效答题人数
        total_count = len(valid_answers)

        accuracy = (correct_count / total_count * 100) if total_count > 0 else 0

        results.append({
            '题号': col_idx - 1,  # 题号从1开始
            '试题': question_content,
            '标准答案': standard_answer_str,
            '答题人数': total_count,
            '正确率': accuracy,
            '答案统计': result[['答案', '出现次数', '学生']],
            '错误答案统计': result[result['答案'] != standard_answer_str].sort_values(by='出现次数', ascending=False)
        })

    # 检查是否有有效题目
    if not results:
        st.error("没有找到任何题目或所有题目均无有效答案。请检查Excel文件是否包含题目列（从第三列开始）且有非空答案。")
    else:
        # 添加排序选项
        sort_option = st.selectbox("选择排序方式:", ["按照题目原本顺序", "按照正确率升序", "按照正确率降序"])

        # 根据选择的排序方式进行排序
        if sort_option == "按照正确率升序":
            sorted_results = sorted(results, key=lambda x: x['正确率'])
        elif sort_option == "按照正确率降序":
            sorted_results = sorted(results, key=lambda x: x['正确率'], reverse=True)
        else:
            sorted_results = results

        # 创建导航栏
        st.sidebar.title("题目导航")
        for res in sorted_results:
            question_link = f"[第{res['题号']}题 (正确率: {res['正确率']:.2f}%)](#{res['题号']})"
            st.sidebar.markdown(question_link)

        # 显示选择的题目统计
        for res in sorted_results:
            st.markdown(f"<a id='{res['题号']}'></a>", unsafe_allow_html=True)
            st.subheader(f"第{res['题号']}题")
            st.write(f"题目: {res['试题']}")
            st.write(f"标准答案: {res['标准答案']}")
            st.write(f"答题人数: {res['答题人数']}")
            st.write(f"正确率: {res['正确率']:.2f}%")

            st.write("#### 所有答案统计")
            all_stats = res['答案统计']
            bar_chart = alt.Chart(all_stats).mark_bar().encode(
                y=alt.Y('答案', sort='-x'),
                x='出现次数',
                tooltip=['答案', '出现次数', '学生']
            ).properties(
                title=''
            )

            st.altair_chart(bar_chart, use_container_width=True)

            for _, row in all_stats.iterrows():
                color = 'green' if row['答案'] == res['标准答案'] else 'red'
                st.markdown(f"<div style='color:black;'>答案: <span style='color:{color};'>{row['答案']}</span></div>",
                            unsafe_allow_html=True)
                st.write(f"出现次数: {row['出现次数']}")
                st.write(f"学生: {row['学生']}")
                st.write("")


        st.success("统计完成！")
else:
    st.info("请上传一个Excel文件以进行错题分析。")