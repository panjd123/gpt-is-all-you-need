"""
你可以输入：
- 分数 评语
- 分数
- 直接回车
"""

import pandas as pd

df = pd.read_csv("result.csv")
df2 = df.copy()

THRESHOLD = 70


def transform(x):
    if x <= 60:  # 完全没有完成
        return x
    if x <= 70:  # 有重大缺陷
        return 90
    return 100  # 无大问题


for i, row in df.iterrows():
    t_score = transform(row["成绩"])
    if row["成绩"] <= THRESHOLD or row["成绩"] is None:
        print(row["学号"], row["姓名"], row["评语"])
        manual_score = input(
            f"Please input the score for {row['学号']} {row['姓名']} (current score: {row['成绩']} -> {t_score}): "
        )
        if " " in manual_score:
            manual_score, comment = manual_score.split(" ", 1)
            df2.loc[i, "评语"] = "手动校对：" + comment
        elif manual_score:
            df2.loc[i, "评语"] = "手动校对："
        df2.loc[i, "成绩"] = int(manual_score) if manual_score else t_score
    else:
        df2.loc[i, "成绩"] = t_score

df2.to_excel("result2.xlsx", index=False)
df2.to_csv("result2.csv", index=False)

df2 = pd.read_csv("result2.csv")
df3 = pd.DataFrame(
    data=df2[["学号", "姓名", "成绩"]],
    columns=["学号", "姓名", "成绩"],
)

df3.to_excel("result3.xlsx", index=False)
df3.to_csv("result3.csv", index=False)
