import pandas as pd

df2 = pd.read_csv("result2.csv")
df3 = pd.DataFrame(
    data=df2[["学号", "姓名", "成绩"]],
    columns=["学号", "姓名", "成绩"],
)


def transform(x):
    if x <= 60:  # 完全没有完成
        return x
    if x <= 70:  # 有重大缺陷
        return 90
    return 100  # 无大问题


df3["成绩"] = df3["成绩"].apply(transform)

df3.to_excel("result3.xlsx", index=False)
df3.to_csv("result3.csv", index=False)
