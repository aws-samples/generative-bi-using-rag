import { BarChart, LineChart, PieChart } from "@cloudscape-design/components";

interface ChartTypeProps {
  data_show_type: string;
  sql_data: any[][];
}

export default function ChartPanel(props: ChartTypeProps) {
  const sql_data = props.sql_data;
  if (props.data_show_type === "bar") {
    // convert data to bar chart data
    const header = sql_data[0];
    const items = sql_data.slice(1, sql_data.length);
    const key = ["x", "y"];
    const content = items.map((item) => {
      const map: any = new Map(
        item.map((value, index) => {
          return [key[index], value];
        })
      );
      return Object.fromEntries(map);
    });
    const seriesValue: any = [
      {
        title: header[1],
        type: "bar",
        data: content,
      },
    ];
    return (
      <BarChart
        series={seriesValue}
        height={300}
        hideFilter
        xTitle={header[0]}
        yTitle={header[1]}
      />
    );
  } else if (props.data_show_type === "line") {
    // convert data to line chart data
    const lineHeader = sql_data[0];
    const lineItems = sql_data.slice(1, sql_data.length);
    const lineKey = ["x", "y"];
    const lineContent = lineItems.map((item) => {
      const map: any = new Map(
        item.map((value, index) => {
          return [lineKey[index], value];
        })
      );
      return Object.fromEntries(map);
    });
    const lineSeriesValue: any = [
      {
        title: lineHeader[1],
        type: "line",
        data: lineContent,
      },
    ];
    return (
      <LineChart
        series={lineSeriesValue}
        height={300}
        hideFilter
        xScaleType="categorical"
        xTitle={lineHeader[0]}
        yTitle={lineHeader[1]}
      />
    );
  } else if (props.data_show_type === "pie") {
    // convert data to pie data
    const pieHeader = sql_data[0];
    const pieItems = sql_data.slice(1, sql_data.length);
    const pieKeys = ["title", "value"];
    const pieContent: any = pieItems.map((item) => {
      const map: any = new Map(
        item.map((value, index) => {
          return [pieKeys[index], value];
        })
      );
      return Object.fromEntries(map);
    });
    return (
      <PieChart
        data={pieContent}
        detailPopoverContent={(datum) => [
          { key: pieHeader[1], value: datum.value },
        ]}
        fitHeight={true}
        hideFilter
        hideLegend
      />
    );
  } else {
    return null;
  }
}
