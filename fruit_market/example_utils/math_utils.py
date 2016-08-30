import pandas as pd
class math_utils():
    def linearFit(fit_to,fit_column,on_columns,df,group_on_column):
        data = pd.DataFrame({},index = df[group_on_column].unique())
        for col in on_columns:
            topDf = df[[fit_column,group_on_column]][(df[fit_column]>=fit_to)].groupby(group_on_column, as_index=False).min()
            topDf = topDf.merge(df, left_on=[group_on_column,fit_column], right_on=[group_on_column,fit_column], how='inner')
            botDf = df[[fit_column,group_on_column]][(df[fit_column]<fit_to)].groupby(group_on_column, as_index=False).max()
            botDf = botDf.merge(df, left_on=[group_on_column,fit_column], right_on=[group_on_column,fit_column], how='inner')
            bothDf = topDf.append(botDf)
            bothDf.sort_values(by=[group_on_column,fit_column],inplace=True)
            dfct = bothDf.groupby(group_on_column).count()
            t = dfct[dfct[col]>1].index
            t = [x in t for x in bothDf[group_on_column]]
            bothDf=bothDf[t]
            def F(x,y):
                m2n =(fit_to-x.iloc[0])
                m2d =(x.iloc[1]-x.iloc[0])
                m2=m2n/m2d
                m1=1-m2 
                return (y.iloc[0]*m1)+(y.iloc[1]*m2)
            def g(x):     
                return F(x[fit_column], x[col])
            kk = bothDf.groupby(group_on_column).apply(g)
            data = pd.concat([data, kk],axis=1,join='inner')
        data.columns = on_columns
        return data