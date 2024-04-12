table_prompt_dict = {}
table_prompt_dict['haiku-20240307v1-0']="""
Event：存储的是一家药企的举办市场活动/会议的信息
- name: trty_name, datatype: VARCHAR, comment: 岗位名称
  annotataion:
- name: event_name, datatype: VARCHAR, comment: 活动名称
  annotataion:
- name: event_date, datatype: DATE, comment: 活动时间
  annotataion:
- name: brand, datatype: VARCHAR, comment: 产品
  annotataion: 示例数据，Forxiga 中文名称是安达唐, Tagrisso,Breztri Aero
- name: event_city, datatype: VARCHAR, comment: 活动城市
  annotataion:
- name: event_type, datatype: VARCHAR, comment: 活动类型
  annotataion:
- name: event_status, datatype: VARCHAR, comment: 活动状态
  annotataion: 示例数据，Event Approved for Closing,Event Blocked,Event Cancelled,Event Rejected,Under Rework for Closing,Available for Closing,New,Under Rework,Event Submitted for Closing,Event Submitted
 
internal_sales: 是内部销量表(药品在内部代理和销售大区的销售数据), 存储销售岗位名称、产品、部门、买方所在省、买方所在区域、销售金额等信息, 如果涉及销售区域和买家可以在这里查询。
- name: sales_date, datatype: DATE, comment: 销售日期
  annotataion:
- name: trty_name, datatype: VARCHAR, comment: 销售岗位名称
  annotataion:
- name: brand, datatype: VARCHAR, comment: 产品
  annotataion: 示例数据为,Forxiga(中文名称安达唐)，Tagrisso(中文名称泰瑞沙)，Breztri Aero(中文名称倍择瑞)
- name: bu, datatype: VARCHAR, comment: 销售部门
  annotataion: 示例数据为,RI&B, RGI,OBU,EC,Eagle,CVRM,CHC,BBU_County
- name: sub_bu, datatype: VARCHAR, comment: 销售子部门
  annotataion: 示例数据为,LC,CHC,BBU_County,IPT,GNR,OBU_County,EC
- name: province_name, datatype: VARCHAR, comment: 买方所在省, 值是中国所有省份,如广东
  annotataion:
- name: area_name, datatype: VARCHAR, comment: 买方所在区
  annotataion: 示例数据为,东部地区,中部地区,北部地区,南部地区,西部地区
- name: region_name, datatype: VARCHAR, comment: 销售大区
  annotataion:
- name: region_center_name, datatype: VARCHAR, comment: 销售大区中心
  annotataion:
- name: inst_name, datatype: VARCHAR, comment: 买方名称,值大多是各类购买药品的医院/诊所名称
  annotataion:
- name: sales_val, datatype: DECIMAL, comment: 销售金额
  annotataion:
- name: target_val, datatype: DECIMAL, comment: 目标销售金额
  annotataion:
 
external_sales: 是外部销量表(药品在市场上销售的数据), 存储销量来源、市场、产品、销售日期、销售金额等字段, 如果涉及市场排名可以在这里查询。存储的是多家药企的外部销售数据, 一个药企可能销售多种药, 每种药每段时间在市场上销量为一行数据。
 
- name: source, datatype: VARCHAR, comment: 数据来源, 只有'aia','ims'两种值
  annotataion:
- name: market, datatype: VARCHAR, comment: 市场
  annotataion:
- name: manufacturer, datatype: VARCHAR, comment:
  annotataion:
- name: brand, datatype: VARCHAR, comment: 产品
  annotataion:
- name: is_az, datatype: VARCHAR, comment: 是否是AZ的产品
  annotataion: 数值只有:Y或者N
- name: sales_date, datatype: DATE, comment: 销售日期
  annotataion: 日期的格式是2023-01-01
- name: sales_val, datatype: DECIMAL, comment: 销售金额, 数据类型是(numeric)
  annotataion:
 
listed_brand: 存储的是药企的客户每次来采购药品的数据
 
- name: inst_name, datatype: VARCHAR, comment: 买方名称
  annotataion:
- name: list_date, datatype: DATE, comment: 采购时间
  annotataion: 示例时间是，2023-02-01
- name: brand, datatype: VARCHAR, comment: 产品
  annotataion: 示例数据包括Forxiga,Tagrisso,Breztri Aerok
"""

table_prompt_dict['sonnet-20240229v1-0']="""
Event：存储的是一家药企的举办市场活动/会议的信息
- name: trty_name, datatype: VARCHAR, comment: 岗位名称
  annotataion:
- name: event_name, datatype: VARCHAR, comment: 活动名称
  annotataion:
- name: event_date, datatype: DATE, comment: 活动时间
  annotataion:
- name: brand, datatype: VARCHAR, comment: 产品
  annotataion: 示例数据，Forxiga 中文名称是安达唐, Tagrisso,Breztri Aero
- name: event_city, datatype: VARCHAR, comment: 活动城市
  annotataion:
- name: event_type, datatype: VARCHAR, comment: 活动类型
  annotataion:
- name: event_status, datatype: VARCHAR, comment: 活动状态
  annotataion: 示例数据，Event Approved for Closing,Event Blocked,Event Cancelled,Event Rejected,Under Rework for Closing,Available for Closing,New,Under Rework,Event Submitted for Closing,Event Submitted
 
internal_sales: 是内部销量表(药品在内部代理和销售大区的销售数据), 存储销售岗位名称、产品、部门、买方所在省、买方所在区域、销售金额等信息, 如果涉及销售区域和买家可以在这里查询。
- name: sales_date, datatype: DATE, comment: 销售日期
  annotataion:
- name: trty_name, datatype: VARCHAR, comment: 销售岗位名称
  annotataion:
- name: brand, datatype: VARCHAR, comment: 产品
  annotataion: 示例数据为,Forxiga(中文名称安达唐)，Tagrisso(中文名称泰瑞沙)，Breztri Aero(中文名称倍择瑞)
- name: bu, datatype: VARCHAR, comment: 销售部门
  annotataion: 示例数据为,RI&B, RGI,OBU,EC,Eagle,CVRM,CHC,BBU_County
- name: sub_bu, datatype: VARCHAR, comment: 销售子部门
  annotataion: 示例数据为,LC,CHC,BBU_County,IPT,GNR,OBU_County,EC
- name: province_name, datatype: VARCHAR, comment: 买方所在省, 值是中国所有省份,如广东
  annotataion:
- name: area_name, datatype: VARCHAR, comment: 买方所在区
  annotataion: 示例数据为,东部地区,中部地区,北部地区,南部地区,西部地区
- name: region_name, datatype: VARCHAR, comment: 销售大区
  annotataion:
- name: region_center_name, datatype: VARCHAR, comment: 销售大区中心
  annotataion:
- name: inst_name, datatype: VARCHAR, comment: 买方名称,值大多是各类购买药品的医院/诊所名称
  annotataion:
- name: sales_val, datatype: DECIMAL, comment: 销售金额
  annotataion:
- name: target_val, datatype: DECIMAL, comment: 目标销售金额
  annotataion:
 
external_sales: 是外部销量表(药品在市场上销售的数据), 存储销量来源、市场、产品、销售日期、销售金额等字段, 如果涉及市场排名可以在这里查询。存储的是多家药企的外部销售数据, 一个药企可能销售多种药, 每种药每段时间在市场上销量为一行数据。
 
- name: source, datatype: VARCHAR, comment: 数据来源, 只有'aia','ims'两种值
  annotataion:
- name: market, datatype: VARCHAR, comment: 市场
  annotataion:
- name: manufacturer, datatype: VARCHAR, comment:
  annotataion:
- name: brand, datatype: VARCHAR, comment: 产品
  annotataion:
- name: is_az, datatype: VARCHAR, comment: 是否是AZ的产品
  annotataion: 数值只有:Y或者N
- name: sales_date, datatype: DATE, comment: 销售日期
  annotataion: 日期的格式是2023-01-01
- name: sales_val, datatype: DECIMAL, comment: 销售金额, 数据类型是(numeric)
  annotataion:
 
listed_brand: 存储的是药企的客户每次来采购药品的数据
 
- name: inst_name, datatype: VARCHAR, comment: 买方名称
  annotataion:
- name: list_date, datatype: DATE, comment: 采购时间
  annotataion: 示例时间是，2023-02-01
- name: brand, datatype: VARCHAR, comment: 产品
  annotataion: 示例数据包括Forxiga,Tagrisso,Breztri Aerok
"""

class TablePromptMapper:
    def __init__(self):
        self.variable_map = table_prompt_dict

    def get_variable(self, name):
        return self.variable_map.get(name)