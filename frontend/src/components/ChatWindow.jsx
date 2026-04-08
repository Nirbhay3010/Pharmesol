import { useState, useRef, useEffect } from "react";
import { streamMessage } from "../api";
import MessageBubble from "./MessageBubble";
import ActionBanner from "./ActionBanner";

export default function ChatWindow({ sessionId, greeting, pharmacy, onEndCall }) {
  const [messages, setMessages] = useState([
    { role: "agent", text: greeting, actions: [] },
  ]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || streaming) return;

    setInput("");
    setStreaming(true);

    setMessages((prev) => [
      ...prev,
      { role: "user", text },
      { role: "agent", text: "", actions: [] },
    ]);

    try {
      await streamMessage(
        sessionId,
        text,
        (token) => {
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            updated[updated.length - 1] = {
              ...last,
              text: last.text + token,
            };
            return updated;
          });
        },
        (actions) => {
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            updated[updated.length - 1] = { ...last, actions };
            return updated;
          });
          setStreaming(false);
        },
        (replacement) => {
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              role: "agent",
              text: replacement,
              actions: [],
            };
            return updated;
          });
        }
      );
    } catch (err) {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "agent",
          text: "Sorry, something went wrong. Please try again.",
          actions: [],
        };
        return updated;
      });
      setStreaming(false);
    }
  };

  return (
    <div className="chat-window">
      <div className="chat-header">
        <h2>Pharmesol Sales Call</h2>
        {pharmacy && (
          <span className="pharmacy-badge">
            {pharmacy.name} — {pharmacy.city}, {pharmacy.state} | ~
            {pharmacy.rx_volume} Rx/mo
          </span>
        )}
        {!pharmacy && (
          <span className="pharmacy-badge new-lead">New Lead</span>
        )}
        <button className="end-call-btn" onClick={onEndCall}>
          End Call
        </button>
      </div>

      <div className="messages-area">
        {messages.map((msg, i) => (
          <div key={i}>
            <MessageBubble role={msg.role} text={msg.text} />
            {msg.actions && msg.actions.length > 0 && (
              <ActionBanner actions={msg.actions} />
            )}
          </div>
        ))}
        {streaming && messages[messages.length - 1]?.text === "" && (
          <div className="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form className="chat-input" onSubmit={handleSend}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={
            streaming ? "Agent is responding..." : "Type your message..."
          }
          disabled={streaming}
          autoFocus
        />
        <button type="submit" disabled={streaming || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}
