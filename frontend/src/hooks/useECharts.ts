"use client";
import { useEffect, useRef } from "react";
import * as echarts from "echarts";

export function useECharts() {
  const chartRef = useRef<HTMLDivElement>(null);
  const instanceRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!chartRef.current) return;

    const instance = echarts.init(chartRef.current);
    instanceRef.current = instance;

    const handleResize = () => instance.resize();
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      instance.dispose();
    };
  }, []);

  const setOption = (option: echarts.EChartsOption) => {
    instanceRef.current?.setOption(option, true);
  };

  return { chartRef, setOption };
}
