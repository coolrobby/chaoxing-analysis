import pandas as pd
import streamlit as st
import altair as alt
import numpy as np

# 设置页面标题
st.title("错题分析-英语")
st.markdown(
    "<p style='text-align: left; color: red;'>读取数据会很慢，请耐心等待。右上角有个小人在动，就表示正在运行。如果担心上课时候打不开，按键盘的“ctrl+p”,可以将当前页面保存为PDF。此外，点击右上角的三点图标，还可以进行一些设置，比如设置为宽屏。</p>",
    unsafe_html=True
)

# 上传Excel文件
uploaded_file = st.file_uploader("请上传错题分析的Excel文件:", type=['xlsx'])

if uploaded_file is not None:
    # 读取上传的文件，强制所有列为字符串
    df = pd.read_excel(uploaded_file, dtype=str, keep_default_na=False)

    # 显示前几行数据以便调试
    st.markdown("### Excel文件前几行预览")
    st.write("以下是Excel文件的前5行（若行数不足则显示全部）：")
    st.dataframe(df.head())

    # 自动检测包含“正确答案”的行
    standard_answer_idx = None
    max_rows_to_check = min(10, len(df))  # 检查前10行或文件总行数
    for idx in range(max_rows_to_check):
        if df.iloc[idx].str.contains("正确答案", na=False).any():
            standard_answer_idx = idx
            break

    # 检查是否找到标准答案行
    if standard_answer_idx is None:
        st.error("未找到包含‘正确答案’的行。请检查Excel文件，确保某一行包含‘正确答案’（如‘正确答案 :D’）。")
    else:
        st.write(f"检测到标准答案行：Excel行号 {standard_answer_idx + 1}（索引 {standard_answer_idx}）")

        results = []
        debug_info = []

        # 从第三列开始处理题目（索引从0开始，所以第3列是索引2）
        for col_idx in range(2, len(df.columns)):
            question_col = df.columns[col_idx]

            # 使用列名作为题目标识（因第一行无题干）
            question_content = question_col

            # 获取标准答案（检测到的行）
            try:
                standard_answer = df.iloc[standard_answer_idx][question_col]
            except IndexError:
                debug_info.append(f"列 {question_col}: 错误 - 行索引 {standard_answer_idx} 超出数据范围")
                continue
            standard_answer_str = str(standard_answer)  # 确保为字符串

            # 调试信息：记录标准答案及其类型
            debug_info.append(
                f"列 {question_col}: 标准答案 = {standard_answer_str}, 类型 = {type(standard_answer).__name__}")

            # 获取学生答案（从标准答案行后的下一行开始）
            answers = df.iloc[standard_answer_idx + 1:][question_col].dropna()
            valid_answers = answers[~answers.isin(["-", "- -", ""])]
            result = valid_answers.value_counts().reset_index()
            result.columns = ['答案', '出现次数']

            # 添加学生姓名列
            result['学生'] = result['答案'].apply(lambda x: ', '.join(
                df[df[question_col] == x].iloc[standard_answer_idx + 1:]['学生姓名'].astype(str)))

            # 统计正确答案数量和有效答题人数
            correct_count = (df.iloc[standard_answer_idx + 1:][question_col].astype(str) == standard_answer_str).sum()

            total_count = df.iloc[standard_answer_idx + 1:][question_col].notna().sum() - \
                          df.iloc[standard_answer_idx + 1:][question_col].isin(["-", "- -", ""]).sum()
            accuracy = (correct_count / total_count * 100) if total_count > 0 else 0

            # 计算答题人数
            answering_count = df.iloc[standard_answer_idx + 1:][question_col].notna().sum() - \
                              df.iloc[standard_answer_idx + 1:][question_col].isin(["-", "- -", ""]).sum()

            results.append({
                '题号': col_idx - 1,  # 题号从1开始
                '试题': question_content,
                '标准答案': standard_answer_str,  # 显示原始标准答案
                '答题人数': answering_count,
                '正确率': accuracy,
                '答案统计': result[['答案', '出现次数', '学生']],
                '错误答案统计': result[result['答案'] != standard_answer_str].sort_values(by='出现次数',
                                                                                          ascending=False)
            })

        # 显示调试信息
        st.markdown("### 调试信息", unsafe_html=True)
        for info in debug_info:
            st.write(info)

        # 检查是否有有效题目
        if not results:
            st.error("没有找到任何题目。请检查Excel文件是否包含题目列（从第三列开始）或标准答案行是否有效。")
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
                st.sidebar.markdown(question_link, unsafe_html=True)

            # 显示选择的题目统计
            for res in sorted_results:
                st.markdown(f"<a id='{res['题号']}'></a>", unsafe_html=True)
                st.subheader(f"第{res['题号']}题")
                st.write(f"题目: {res['试题']}")
                st.write(f"标准答案: {res['标准答案']}")
                st.write(f"答题人数: {res['答题人数']}")
                st.write(f"正确率: {res['正确率']:.2f}%")

                if not res['错误答案统计'].empty:
                    st.write("#### 错误答案统计")

                    error_stats = res['错误答案统计']
                    bar_chart = alt.Chart(error_stats).mark_bar(color='red').encode(
                        y=alt.Y('答案', sort='-x'),
                        x='出现次数',
                        tooltip=['答案', '出现次数', '学生']
                    ).properties(
                        title=''
                    )

                    st.altair_chart(bar_chart, use_container_width=True)

                    for _, row in error_stats.iterrows():
                        color = 'green' if row['答案'] == res['标准答案'] else 'red'
                        st.markdown(
                            f"<div style='color:black;'>答案: <span style='color:{color};'>{row['答案']}</span></div>",
                            unsafe_html=True)
                        st.write(f"出现次数: {row['出现次数']}")
                        st.write(f"学生: {row['学生']}")
                        st.write("")

            st.success("统计完成！")
else:
    st.info("请上传一个Excel文件以进行错题分析。")