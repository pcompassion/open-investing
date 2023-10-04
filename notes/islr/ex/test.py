import pandas as pd
pd.set_option('display.width', 220)

pd.DataFrame({"a": [1, 2], "b": [3, 4]})

adult  = pd.read_csv("https://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.data",
names = ['age','workclass','fnlwgt', 'education',    'education_num','marital_status','occupation','relationship','race','sex','capital_gain','capital_loss', 'hours_per_week', 'native_country','label'], index_col = False)
print("Shape of data{}".format(adult.shape))
adult.head()

import sys
print(sys.path)

import os
print(os.environ)



df = adult.sample(10000, random_state = 100).sort_index(axis=0)
df.head()

df.index.name = 'index_adult'
df.index
# df.columns

df.columns

df.loc[6, ['age']]

cols = ['age', 'education', 'marital_status', 'occupation', 'race', 'sex', 'native_country', 'label']
df = df[cols]
df.head()

df.groupby('native_country').groups.keys()

ind = df[df.native_country == " India"]
ind.head()

df.reset_index().head()

cross = pd.crosstab(ind.sex, ind.label)
cross
