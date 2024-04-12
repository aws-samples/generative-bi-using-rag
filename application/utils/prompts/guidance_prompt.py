guidance_prompt_dict = {}
guidance_prompt_dict['haiku-20240307v1-0'] = """
you should always keep the words from question unchanges when writing SQL. \n\n
"""

guidance_prompt_dict['sonnet-20240229v1-0'] = """
divide actual value by target value to get A/T% or 达成率.
divide this year's sales by last year's sales and then subtract one to get YTD YoY GR% or YTD 销量增长.
divide this year's market sales by last year's market sales and then subtract one to get YoY MKT GR% or 市场增长.
divide product sales by total sales to get Con% or 销售贡献.
divide selected product sales by default market sales to get YTD YoY MS% or YTD市场占比.
subtract last year's MS% from this year's MS% to get YTD YoY Δ MS% or YTD 市场占比变化.
subtract last year's sales from this year's sales to sales incremental or 销量增量.
sum last year's actual sales to get LY Actual or 去年实际销量.
rank sales within selected products and selected channels to get Sale Value Rank or 销量排名.
divide all increments by product increments to get YTD GR Con% or 销量贡献增长.
sum MTD DDI Actual to get MTD Actual or 当月累计销量.
divide the total amount of MTDD DDI Actual by the total amount of Target to get DDI A/T or DDI累计达成.
calculate R3M GR% or 滚动3个月增长 step by step using the following four steps:
step one: collect at least two years data earlier than the mentioned time in query.
step two: calculate the sum of sales volume from the max month of existing data to the previous 3 months in the year mentioned in query as pre_r3m.
step three: calculate the sum of sales volume relative to the same months of the previous year in step two as whole_r3m.
step four: divide pre_r3m by whole_r3m and minus by one.
use MYSQL Sytax, for example:
use EXTRACT instead of DATE_TRUNC
use EXTRACT instead of DATE_PART
"""

class GuidancePromptMapper:
    def __init__(self):
        self.variable_map = guidance_prompt_dict

    def get_variable(self, name):
        return self.variable_map.get(name)