const TOOL_LABELS = {
  send_follow_up_email: "Email Sent",
  schedule_callback: "Callback Scheduled",
};

export default function ActionBanner({ actions }) {
  const visible = actions.filter((a) => TOOL_LABELS[a.tool]);

  if (visible.length === 0) return null;

  return (
    <div className="action-banners">
      {visible.map((action, i) => {
        const label = TOOL_LABELS[action.tool];
        let detail = "";
        if (action.tool === "send_follow_up_email") {
          detail = `to ${action.arguments?.email || "pharmacy"}`;
        } else if (action.tool === "schedule_callback") {
          detail = `for ${action.arguments?.date_time || "TBD"}`;
        }

        return (
          <div key={i} className="action-banner">
            <span className="action-icon">✓</span>
            <span>
              {label} {detail}
            </span>
          </div>
        );
      })}
    </div>
  );
}
