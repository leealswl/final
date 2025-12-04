import React, { useState, useRef } from "react";
import { NodeViewWrapper } from "@tiptap/react";
import {
  Box,
  Button,
  Divider,
  Menu,
  MenuItem,
  Typography,
} from "@mui/material";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  RadialLinearScale,
  Filler,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { Line, Bar, Pie, Doughnut, Radar } from "react-chartjs-2";

// Chart.js 등록
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  RadialLinearScale,
  Filler,
  Title,
  Tooltip,
  Legend
);

export default function ChartNodeView({ node, updateAttributes, deleteNode, getPos, editor, selected }) {
  const [menuState, setMenuState] = useState(null);
  const chartRef = useRef(null);

  const { chartType, title, data, options } = node.attrs;

  const openContextMenu = (event) => {
    event.preventDefault();
    event.stopPropagation();
    const position = { mouseX: event.clientX + 2, mouseY: event.clientY - 6 };
    setMenuState(position);
    const pos = getPos?.();
    if (typeof pos === "number") {
      editor?.chain().setNodeSelection(pos).run();
    }
  };

  const closeContextMenu = () => setMenuState(null);

  const handleDelete = () => {
    deleteNode();
    closeContextMenu();
  };

  // 차트 컴포넌트 렌더링
  const renderChart = () => {
    if (!data || !chartType) {
      return (
        <Box sx={{ p: 2, textAlign: "center", color: "#999" }}>
          차트 데이터가 없습니다.
        </Box>
      );
    }

    const chartOptions = {
      ...options,
      maintainAspectRatio: false,
      responsive: true,
    };

    const chartData = {
      labels: data.labels || [],
      datasets: data.datasets || [],
    };

    switch (chartType) {
      case "line":
        return <Line data={chartData} options={chartOptions} />;
      case "bar":
        return <Bar data={chartData} options={chartOptions} />;
      case "pie":
        return <Pie data={chartData} options={chartOptions} />;
      case "doughnut":
        return <Doughnut data={chartData} options={chartOptions} />;
      case "radar":
        return <Radar data={chartData} options={chartOptions} />;
      default:
        return (
          <Box sx={{ p: 2, textAlign: "center", color: "#999" }}>
            지원하지 않는 차트 타입: {chartType}
          </Box>
        );
    }
  };

  return (
    <NodeViewWrapper
      className={`paladoc-chart-wrapper${selected ? " selected" : ""}`}
      data-drag-handle
    >
      <div className="paladoc-chart-inner" onContextMenu={openContextMenu}>
        {title && (
          <Typography
            variant="h6"
            sx={{
              mb: 1,
              fontSize: "1rem",
              fontWeight: 600,
              textAlign: "center",
            }}
          >
            {title}
          </Typography>
        )}
        <Box
          sx={{
            position: "relative",
            width: "100%",
            height: "300px",
            minHeight: "200px",
          }}
        >
          {renderChart()}
        </Box>
        {selected ? (
          <>
            <span className="paladoc-chart-handle handle-tl" />
            <span className="paladoc-chart-handle handle-tr" />
            <span className="paladoc-chart-handle handle-bl" />
            <span className="paladoc-chart-handle handle-br" />
          </>
        ) : null}
      </div>

      <Menu
        open={Boolean(menuState)}
        onClose={closeContextMenu}
        anchorReference="anchorPosition"
        anchorPosition={
          menuState
            ? { top: menuState.mouseY, left: menuState.mouseX }
            : undefined
        }
      >
        <MenuItem onClick={handleDelete}>
          <DeleteOutlineIcon fontSize="small" sx={{ mr: 1 }} /> 삭제
        </MenuItem>
      </Menu>
    </NodeViewWrapper>
  );
}

