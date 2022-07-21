# 拟合函数
# 适用于csv_file中为 全部原始数据 或 原始数据+预测数据行共存（预测数据行即 补充的 文章未给出的天数对应的Albumin为空的行）
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import csv
import xgboost as xgb
from sklearn.preprocessing import StandardScaler

csv_file = open('evaluation.csv', encoding='ISO-8859-1')
data = pd.read_csv(csv_file)

label_name = 'Albumin'
feature_name = ['Day', 'Cell Type', 'Cell Seeding', 'Scaffold Type', 'Modification', 'Concentration', 'Pore Size', 'Thick',
                'Diameter', 'Porosity', 'Static/dynamic']
x_label = data[feature_name]
y_label = pd.DataFrame(data[label_name])
# 新建预测变量dataframe 用于从原始数据中drop有原始数据的行
x_label_pred = x_label.copy()
y_label_pred = y_label.copy()

# 当原始数据中包含混杂的原始数据（文章给出）和预测数据（模型预测）时，下面的函数用于提取真实数据；否则只保留真实数据
# 遍历dataframe的每一行
for index in range(0, len(y_label)):
    # 判断某行对应的Albumin是否为空 为空则为预测数据
    # .loc为按标签提取， .iloc为按位置索引提取 (第一个参数为行 第二个参数为列) 有 data.loc[:, 'Albumin'] = data.iloc[:, 0]
    if pd.isnull(y_label.loc[index, 'Albumin']):
        y_label.drop(index=index, inplace=True)
        # 自变量标签同样drop掉 预测数据行 即可
        x_label.drop(index=index, inplace=True)
    # 提取预测数据行
    else:
        y_label_pred.drop(index=index, inplace=True)
        x_label_pred.drop(index=index, inplace=True)


# fillna中 pad为利用前面的数据填充 df.mode()/median()/mean()为众数、中位数、平均值填充
# x_label = x_label.interpolate(method='pad')
# x_label = x_label.fillna(x_label.median())
# 数据归一化处理
scaler = StandardScaler()
columns = x_label.columns
x_label_norm = pd.DataFrame(scaler.fit_transform(x_label), columns=columns)
x_label_pred_norm = pd.DataFrame(scaler.fit_transform(x_label_pred), columns=columns)
# 此处可更换具体的拟合模型 xgb库可直接绘制feature_importance图像
# 通过控制n_estimator来控制F_score的范围
clf = xgb.XGBRegressor(max_depth=10, learning_rate=0.1, n_estimators=1000, reg_alpha=0.005, subsample=0.8,
                       gamma=0, colsample_bylevel=0.8)

# 习惯将数据转化为 float 格式
x = np.array(x_label).astype(np.float64)
y = np.array(y_label).astype(np.float64)

clf.fit(x_label_norm, y_label)
pred_list = clf.predict(x_label_pred_norm)
print(pred_list)

# 填入预测的数据值
for index, row in y_label_pred.iterrows():
    for idb in range(pred_list.__len__()):
        # pred_list的列表索引从0开始 y_label_pred的索引随机(从原始表格中删除获得) 但两者数量相同且一一对应 可用不同索引进行赋值
        y_label_pred.loc[index, 'Albumin'] = pred_list[idb]

# 拼接自变量和因变量 形成完整的原始数据（预测数据）行
raw_data = pd.concat([y_label, x_label], axis=1)
raw_data.insert(loc=0, column='Source', value='true')  # 备注数据来源于原始值
pred_data = pd.concat([y_label_pred, x_label_pred], axis=1)
pred_data.insert(loc=0, column='Source', value='predicted')  # 备注数据来源于预测值
# 将预测后的数据拼接到原始数据 形成补点后的dataframe
final = pd.concat([raw_data, pred_data], axis=0)

# final.to_csv('final.csv')