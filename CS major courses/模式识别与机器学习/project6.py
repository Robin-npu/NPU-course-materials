import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score


# 1. 读取数据
data_path = "mycode\ML\insurance.csv"

data = pd.read_csv(data_path)

print("数据前5行：")
print(data.head())

print("\n数据基本信息：")
print(data.info())

print("\n缺失值统计：")
print(data.isnull().sum())

print("\n数据描述统计：")
print(data.describe())


# 2. 划分特征和标签
X = data.drop(columns=["charges"])
y = data["charges"]


# 3. 区分数值特征和类别特征
num_features = ["age", "bmi", "children"]
cat_features = ["sex", "smoker", "region"]


# 4. 划分训练集和测试集
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)


# 5. 数据预处理：类别特征独热编码
preprocess = ColumnTransformer(
    transformers=[
        ("num", "passthrough", num_features),
        ("cat", OneHotEncoder(drop="first", handle_unknown="ignore"), cat_features)
    ]
)


# 6. 建立线性回归模型
model = Pipeline(
    steps=[
        ("preprocess", preprocess),
        ("regressor", LinearRegression())
    ]
)


# 7. 训练模型
model.fit(X_train, y_train)


# 8. 模型预测
y_pred = model.predict(X_test)


# 9. 模型评价
mse = mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse)
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print("\n模型评价结果：")
print(f"MSE  = {mse:.2f}")
print(f"RMSE = {rmse:.2f}")
print(f"MAE  = {mae:.2f}")
print(f"R²   = {r2:.4f}")


# 10. 输出特征系数
onehot = model.named_steps["preprocess"].named_transformers_["cat"]
cat_names = onehot.get_feature_names_out(cat_features)

feature_names = num_features + list(cat_names)
coef = model.named_steps["regressor"].coef_

coef_df = pd.DataFrame({
    "Feature": feature_names,
    "Coefficient": coef
})

coef_df["AbsCoefficient"] = coef_df["Coefficient"].abs()
coef_df = coef_df.sort_values("AbsCoefficient", ascending=False)

print("\n线性回归特征系数：")
print(coef_df[["Feature", "Coefficient"]])


# 11. 保存实验结果
result_df = pd.DataFrame({
    "Metric": ["MSE", "RMSE", "MAE", "R2"],
    "Value": [mse, rmse, mae, r2]
})

result_df.to_csv("linear_regression_metrics.csv", index=False, encoding="utf-8-sig")
coef_df.to_csv("linear_regression_coefficients.csv", index=False, encoding="utf-8-sig")


# 12. 年龄与医疗保险费用关系图
plt.figure(figsize=(7, 5))
plt.scatter(data["age"], data["charges"], alpha=0.6)

z = np.polyfit(data["age"], data["charges"], 1)
p = np.poly1d(z)
x_line = np.linspace(data["age"].min(), data["age"].max(), 100)

plt.plot(x_line, p(x_line), linewidth=2)

plt.xlabel("Age")
plt.ylabel("Charges")
plt.title("Age vs Insurance Charges")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("insurance_age_charges.png", dpi=300)
plt.show()


# 13. BMI 与医疗保险费用关系图
plt.figure(figsize=(7, 5))
plt.scatter(data["bmi"], data["charges"], alpha=0.6)

z = np.polyfit(data["bmi"], data["charges"], 1)
p = np.poly1d(z)
x_line = np.linspace(data["bmi"].min(), data["bmi"].max(), 100)

plt.plot(x_line, p(x_line), linewidth=2)

plt.xlabel("BMI")
plt.ylabel("Charges")
plt.title("BMI vs Insurance Charges")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("insurance_bmi_charges.png", dpi=300)
plt.show()


# 14. 是否吸烟与医疗保险费用关系图
groups = [
    data.loc[data["smoker"] == "no", "charges"],
    data.loc[data["smoker"] == "yes", "charges"]
]

plt.figure(figsize=(7, 5))
plt.boxplot(groups, labels=["Non-smoker", "Smoker"])

plt.xlabel("Smoking Status")
plt.ylabel("Charges")
plt.title("Insurance Charges by Smoking Status")
plt.grid(True, axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig("insurance_smoker_charges.png", dpi=300)
plt.show()


# 15. 特征系数可视化
plot_coef = coef_df.sort_values("AbsCoefficient", ascending=True)

plt.figure(figsize=(8, 5))
plt.barh(plot_coef["Feature"], plot_coef["Coefficient"])

plt.xlabel("Linear Regression Coefficient")
plt.ylabel("Feature")
plt.title("Feature Coefficients of Linear Regression Model")
plt.grid(True, axis="x", alpha=0.3)
plt.tight_layout()
plt.savefig("insurance_feature_coefficients.png", dpi=300)
plt.show()


# 16. 真实值与预测值对比图
plt.figure(figsize=(6, 6))
plt.scatter(y_test, y_pred, alpha=0.7)

min_value = min(y_test.min(), y_pred.min())
max_value = max(y_test.max(), y_pred.max())

plt.plot([min_value, max_value], [min_value, max_value], linewidth=2)

plt.xlabel("True Charges")
plt.ylabel("Predicted Charges")
plt.title("True vs Predicted Insurance Charges")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("insurance_true_vs_predicted.png", dpi=300)
plt.show()