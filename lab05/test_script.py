import pandas as pd
import statsmodels.api as sm
from statsmodels.formula.api import ols
import os

df = pd.read_csv(os.path.abspath(os.getcwd()) + f"/results.csv")

model = ols('size ~ C(api) + C(attribute_qtt) + C(pagination) + C(api):C(attribute_qtt) + C(api):C(pagination) + '
			'C(api):C(attribute_qtt):C(pagination)', data=df).fit()

sm.stats.anova_lm(model, typ=3).to_csv(os.path.abspath(os.getcwd()) + f'/size_test.csv', index=False, header=True)
