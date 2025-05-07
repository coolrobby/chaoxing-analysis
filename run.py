import pandas as pd
import streamlit as st
import altair as alt

# 设置页面标题
st.title("错题分析-英语")
st.markdown(
    "<p style='text-align: left; color: red;'>读取数据会很慢，请耐心等待。右上角有个小人在动，就表示正在运行。如果担心上课时候打不开，按键盘的“ctrl+p”,可以将当前页面保存为PDF。此外，点击右上角的三点图标，还可以进行一些设置，比如设置为宽屏。</p>",
    unsafe_allow_html=True)

# 上传Excel文件
uploaded_file = st.file_uploader("请上传错题分析的Excel文件:", type=['xlsx'])

if uploaded_file is not None:
    # 读取上传的文件
    df = pd.read_excel(uploaded_file)

    # 替换列名
    df.columns = df.columns.str.replace('试题 ', '试题', regex=False)

    results = []
    i = 1

    while True:
        answer_col = f'回答{i}'  # 动态生成回答列名
        if answer_col not in df.columns:
            break

        answers = df[answer_col].dropna()  # 获取回答
        valid_answers = answers[~answers.isin(["-", "- -"])]
        result = valid_answers.value_counts().reset_index()  # 统计答案出现次数
        result.columns = ['答案', '出现次数']

        # 添加学生列
        result['学生'] = result['答案'].apply(lambda x: ', '.join(
            df[df[answer_col] == x]['姓氏'].astype(str) + df[df[answer_col] == x]['名'].astype(str)))

        standard_answer_col = f'标准答案{i}'  # 动态生成标准答案列名
        standard_answer = df[standard_answer_col].iloc[0]  # 获取标准答案，取第一行

        correct_count = (df[answer_col] == standard_answer).sum()  # 统计正确答案数量
        total_count = df[answer_col].notna().sum() - df[answer_col].isin(["-", "- -"]).sum()  # 计算有效答题人数
        accuracy = (correct_count / total_count * 100) if total_count > 0 else 0

        # 计算答题人数（所有答案不为“–”的人数）
        answering_count = df[answer_col].notna().sum() - df[answer_col].isin(["-", "- -"]).sum()

        question_content = df[f'试题{i}'].iloc[0]  # 获取题目内容，取第一行

        results.append({
            '题号': i,
            '试题': question_content,
            '标准答案': standard_answer,
            '答题人数': answering_count,
            '正确率': accuracy,
            '答案统计': result[['答案', '出现次数', '学生']],
            '错误答案统计': result[result['答案'] != standard_answer].sort_values(by='出现次数', ascending=False)
        })

        i += 1  # 处理下一道题

    # 添加排序选项
    sort_option = st.selectbox("选择排序方式:", ["按照题目原本顺序", "按照正确率升序", "按照正确率降序"])

    # 根据选择的排序方式进行排序
    if sort_option == "按照正确率升序":
        sorted_results = sorted(results, key=lambda x: x['正确率'])
    elif sort_option == "按照正确率降序":
        sorted_results = sorted(results, key=lambda x: x['正确率'], reverse=True)
    else:
        sorted_results = results  # 保持原本顺序

    # 创建导航栏
    st.sidebar.title("题目导航")
    for res in sorted_results:
        question_link = f"[第{res['题号']}题 (正确率: {res['正确率']:.2f}%)](#{res['题号']})"
        st.sidebar.markdown(question_link)

    # 显示选择的题目统计
    for res in sorted_results:
        st.markdown(f"<a id='{res['题号']}'></a>", unsafe_allow_html=True)  # 创建锚点
        st.subheader(f"第{res['题号']}题")
        st.write(f"题目: {res['试题']}")
        st.write(f"标准答案: {res['标准答案']}")
        st.write(f"答题人数: {res['答题人数']}")
        st.write(f"正确率: {res['正确率']:.2f}%")

        if not res['错误答案统计'].empty:
            st.write("#### 错误答案统计")

            # 从上往下的柱形图
            error_stats = res['错误答案统计']
            bar_chart = alt.Chart(error_stats).mark_bar(color='red').encode(
                y=alt.Y('答案', sort='-x'),
                x='出现次数',
                tooltip=['答案', '出现次数', '学生']
            ).properties(
                title=''
            )

            st.altair_chart(bar_chart, use_container_width=True)

            # 列出所有错误答案
            for _, row in error_stats.iterrows():
                color = 'green' if row['答案'] == res['标准答案'] else 'red'
                st.markdown(f"<div style='color:black;'>答案: <span style='color:{color};'>{row['答案']}</span></div>",
                            unsafe_allow_html=True)
                st.write(f"出现次数: {row['出现次数']}")
                st.write(f"学生: {row['学生']}")
                st.write("")  # 添加空行

    st.success("统计完成！")

else:
    st.info("请上传一个Excel文件以进行错题分析。")