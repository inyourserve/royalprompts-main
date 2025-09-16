"use client";
import { ApexOptions } from "apexcharts";
import dynamic from "next/dynamic";
import { MoreDotIcon } from "@/icons";
import { DropdownItem } from "../ui/dropdown/DropdownItem";
import { useState, useEffect } from "react";
import { Dropdown } from "../ui/dropdown/Dropdown";
import { useTheme } from "@/context/ThemeContext";
import { dashboardApi } from "@/services";

// Dynamically import the ReactApexChart component
const ReactApexChart = dynamic(() => import("react-apexcharts"), {
  ssr: false,
});

export default function PromptsChart() {
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const options: ApexOptions = {
    colors: ["#3b82f6", "#10b981"],
    chart: {
      fontFamily: "Outfit, sans-serif",
      type: "area",
      height: 350,
      toolbar: {
        show: false,
      },
      background: "transparent",
    },
    plotOptions: {
      bar: {
        horizontal: false,
        columnWidth: "39%",
        borderRadius: 5,
        borderRadiusApplication: "end",
      },
    },
    dataLabels: {
      enabled: false,
    },
    stroke: {
      show: true,
      width: 4,
      colors: ["#3b82f6", "#10b981"],
      curve: "smooth",
    },
    markers: {
      size: 6,
      colors: ["#3b82f6", "#10b981"],
      strokeColors: "#ffffff",
      strokeWidth: 2,
      hover: {
        size: 8,
      },
    },
    fill: {
      type: "gradient",
      gradient: {
        shadeIntensity: 1,
        opacityFrom: 0.6,
        opacityTo: 0.1,
        stops: [0, 100],
        colorStops: [
          {
            offset: 0,
            color: "#3b82f6",
            opacity: 0.6
          },
          {
            offset: 100,
            color: "#3b82f6",
            opacity: 0.1
          }
        ]
      },
    },
    xaxis: {
      categories: [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
      ],
      axisBorder: {
        show: false,
      },
      axisTicks: {
        show: false,
      },
      labels: {
        style: {
          colors: isDark ? "#9ca3af" : "#6b7280",
          fontSize: "12px",
          fontFamily: "Outfit, sans-serif",
        },
      },
    },
    legend: {
      show: true,
      position: "top",
      horizontalAlign: "left",
      fontFamily: "Outfit",
      fontSize: "14px",
    },
    yaxis: {
      title: {
        text: "Number of Prompts",
        style: {
          color: isDark ? "#9ca3af" : "#6b7280",
          fontSize: "14px",
          fontFamily: "Outfit, sans-serif",
        },
      },
      labels: {
        style: {
          colors: isDark ? "#9ca3af" : "#6b7280",
          fontSize: "12px",
          fontFamily: "Outfit, sans-serif",
        },
      },
    },
    grid: {
      borderColor: isDark ? "#374151" : "#e5e7eb",
      strokeDashArray: 3,
      xaxis: {
        lines: {
          show: true,
        },
      },
      yaxis: {
        lines: {
          show: true,
        },
      },
    },
    tooltip: {
      theme: isDark ? "dark" : "light",
      style: {
        fontSize: "12px",
        fontFamily: "Outfit, sans-serif",
      },
      x: {
        show: false,
      },
      y: {
        formatter: (val: number) => `${val} prompts`,
      },
      marker: {
        show: true,
      },
    },
  };

  const [chartData, setChartData] = useState({
    prompts_added: [45, 52, 38, 67, 58, 72, 89, 76, 85, 92, 78, 95],
    trending_prompts: [12, 18, 15, 25, 22, 28, 35, 30, 32, 38, 29, 42],
    totals: { total_prompts_added: 892, total_trending: 327 }
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchChartData = async () => {
      try {
        const data = await dashboardApi.getChartData();
        setChartData(data);
      } catch (error) {
        console.error("Failed to fetch chart data:", error);
        // Keep default data if API fails
      } finally {
        setLoading(false);
      }
    };

    fetchChartData();
  }, []);

  const series = [
    {
      name: "Prompts Added",
      data: chartData.prompts_added,
    },
    {
      name: "Trending Prompts",
      data: chartData.trending_prompts,
    },
  ];

  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-white/[0.03]">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-semibold text-gray-800 dark:text-white/90">
            Prompts Growth
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Track the growth of prompts over the last 12 months
          </p>
        </div>

        <div className="relative">
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="dropdown-toggle flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 hover:text-gray-800 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-white/[0.03] dark:hover:text-gray-200"
          >
            <MoreDotIcon className="w-4 h-4" />
          </button>

          <Dropdown
            isOpen={isOpen}
            onClose={() => setIsOpen(false)}
            className="w-48"
          >
            <DropdownItem onClick={() => setIsOpen(false)}>
              Download Report
            </DropdownItem>
            <DropdownItem onClick={() => setIsOpen(false)}>
              Share Chart
            </DropdownItem>
            <DropdownItem onClick={() => setIsOpen(false)}>
              Export Data
            </DropdownItem>
          </Dropdown>
        </div>
      </div>

      <div className={`h-[350px] ${
        isDark 
          ? "[&_.apexcharts-tooltip]:!bg-gray-800 [&_.apexcharts-tooltip]:!border-gray-600 [&_.apexcharts-tooltip]:!text-gray-100 [&_.apexcharts-tooltip]:!shadow-xl" 
          : "[&_.apexcharts-tooltip]:!bg-white [&_.apexcharts-tooltip]:!border-gray-300 [&_.apexcharts-tooltip]:!text-gray-800 [&_.apexcharts-tooltip]:!shadow-lg"
      }`}>
        <ReactApexChart
          options={options}
          series={series}
          type="area"
          height={350}
        />
      </div>
      
      <div className="mt-6 grid grid-cols-2 gap-4 pt-4 border-t border-gray-200 dark:border-gray-800">
        <div className="text-center">
          <div className="text-2xl font-bold text-gray-800 dark:text-white/90">
            {loading ? (
              <div className="animate-pulse h-8 bg-gray-200 rounded dark:bg-gray-700"></div>
            ) : (
              chartData.totals.total_prompts_added.toLocaleString()
            )}
          </div>
          <div className="text-sm text-gray-500 dark:text-gray-400">
            Total Prompts Added
          </div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-gray-800 dark:text-white/90">
            {loading ? (
              <div className="animate-pulse h-8 bg-gray-200 rounded dark:bg-gray-700"></div>
            ) : (
              chartData.totals.total_trending.toLocaleString()
            )}
          </div>
          <div className="text-sm text-gray-500 dark:text-gray-400">
            Trending Prompts
          </div>
        </div>
      </div>
    </div>
  );
}
