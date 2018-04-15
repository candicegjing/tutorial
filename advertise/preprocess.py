# coding: utf-8
import pandas as pd
import time


def convdate(t):
    return time.strftime('%Y-%m-%d', time.localtime(t))

def build_date_buf(date_pivot,  left, right):
    """
    span < 0 : lag
    span > 0 : ahead
    :param date_pivot:
    :param move:
    :return:
    """

    date_buf = []
    buf = range(left, right)
    for i in buf:
        date = date_pivot  + pd.Timedelta(i ,  unit = 'd')
        date_buf.append(date.strftime('%Y-%m-%d'))

    return date_buf



def augment_convrate(df):
    """
    历史转化率特征
    :param df:
    :return:
    """
    datebuf = df['date'].unique()
    collist =  [ ( ['item_id'],  'item_posrate') , (['user_age_level','item_id'], 'age_item_posrate') ]


    buf = []
    for day in datebuf:
        date_pivot = pd.to_datetime(day)
        lag_days = build_date_buf(date_pivot, -3, 0 )
        print day, lag_days

        lag_df = df[df['date'].isin(lag_days)]
        target_df = df[df['date'].isin([day])]

        if lag_df.shape[0] == 0  or target_df.shape[0] == 0 : continue
        for cols, colname in collist:
            lag_g = lag_df.groupby(cols).is_trade.mean().reset_index()
            lagcols = [] + cols
            lagcols += [ colname ]

            lag_g.columns = lagcols
            target_df = pd.merge(target_df, lag_g, on=cols, how='left').fillna(0)
            print target_df.head()
        buf.append(target_df)


    conv_df = pd.concat(buf, axis = 0)
    conv_df.to_csv('conv.csv',sep=' ', index=False)
    return conv_df
def make_instant(df):
    prev = -1
    buf = []
    for row in df.itertuples():
        cur = row.context_timestamp
        instance_id = row.instance_id
        if prev == -1:
            buf.append( 1 )
        else:

            if cur - prev <= 15 * 60:
                buf.append( buf[-1] + 1)
            else:
                buf.append( 1 )

        prev = cur
    df['recent_15minutes']=  buf

    return df[['instance_id' , 'recent_15minutes']]

def augment_instant_feature(df):
    """
    实时特征  user_item  user_brand
    :param df:
    :return:
    """
    df = df #type:pd.DataFrame
    sorted_df = df.sort_values('context_timestamp')
    ins_recent_df = sorted_df.groupby( ['user_id','item_id'])[['instance_id','context_timestamp']].apply(make_instant).reset_index(drop=True)

    aug_df = pd.merge(df, ins_recent_df, on='instance_id')
    return aug_df



if __name__ == '__main__':
    """
    实现了历史转化率特征和实时特征

    next: make string sample and feature.
    """
    df = pd.read_csv('round1_ijcai_18_train_20180301.txt',sep=' ',header=0)

    df['date'] = df['context_timestamp'].apply(lambda x : convdate(x))

    conv_df = augment_convrate(df)

    conv_instant_df = augment_instant_feature(conv_df)
    conv_instant_df.to_csv('conv_ins.csv',index=False,sep=' ')





