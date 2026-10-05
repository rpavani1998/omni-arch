export const NODE_TYPE_STYLES = {
  header: {
    shape: "round_rectangle",
    fillColor: "#f8fafc",
    borderColor: "#cbd5e1",
    badgeBg: "rgba(203, 213, 225, 0.12)",
    badgeText: "#64748b",
    label: "Tier",
  },
  frontend: {
    shape: "round_rectangle",
    fillColor: "#e0f2fe",
    borderColor: "#0284c7",
    badgeBg: "rgba(2, 132, 199, 0.12)",
    badgeText: "#0284c7",
    label: "Client / UI",
  },
  gateway: {
    shape: "round_rectangle",
    fillColor: "#f3e8ff",
    borderColor: "#9333ea",
    badgeBg: "rgba(147, 51, 234, 0.12)",
    badgeText: "#9333ea",
    label: "Gateway",
  },
  service: {
    shape: "round_rectangle",
    fillColor: "#ecfdf5",
    borderColor: "#059669",
    badgeBg: "rgba(5, 150, 105, 0.12)",
    badgeText: "#059669",
    label: "Service",
  },
  database: {
    shape: "round_rectangle",
    fillColor: "#fef3c7",
    borderColor: "#d97706",
    badgeBg: "rgba(217, 119, 6, 0.12)",
    badgeText: "#d97706",
    label: "Database",
  },
  cache: {
    shape: "round_rectangle",
    fillColor: "#ffe4e6",
    borderColor: "#e11d48",
    badgeBg: "rgba(225, 29, 72, 0.12)",
    badgeText: "#e11d48",
    label: "Cache",
  },
  queue: {
    shape: "round_rectangle",
    fillColor: "#e0e7ff",
    borderColor: "#4f46e5",
    badgeBg: "rgba(79, 70, 229, 0.12)",
    badgeText: "#4f46e5",
    label: "Event Queue",
  },
  external: {
    shape: "round_rectangle",
    fillColor: "#f1f5f9",
    borderColor: "#64748b",
    badgeBg: "rgba(100, 116, 139, 0.12)",
    badgeText: "#64748b",
    label: "External API",
  },
};

export function getStyle(nodeType) {
  return NODE_TYPE_STYLES[nodeType] || NODE_TYPE_STYLES.service;
}