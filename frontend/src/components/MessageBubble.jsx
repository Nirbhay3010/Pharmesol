export default function MessageBubble({ role, text }) {
  const isAgent = role === "agent";

  return (
    <div className={`message-row ${isAgent ? "agent" : "user"}`}>
      {isAgent && <div className="avatar agent-avatar">P</div>}
      <div className={`bubble ${isAgent ? "agent-bubble" : "user-bubble"}`}>
        {text}
      </div>
      {!isAgent && <div className="avatar user-avatar">You</div>}
    </div>
  );
}
