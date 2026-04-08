import { useState } from "react";

const DEFAULT_PHONE = "+1-555-123-4567";

export default function PhoneEntry({ onStart }) {
  const [phone, setPhone] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await onStart(phone || DEFAULT_PHONE);
    } catch (err) {
      setError("Failed to connect. Make sure the backend is running.");
      setLoading(false);
    }
  };

  return (
    <div className="phone-entry">
      <div className="phone-entry-card">
        <div className="logo">
          <h1>Pharmesol</h1>
          <p className="tagline">AI Pharmacy Assistant</p>
        </div>
        <h2>Inbound Sales Agent</h2>
        <p className="description">
          Enter a caller phone number to simulate an inbound sales call.
        </p>
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder={`Phone number (default: ${DEFAULT_PHONE})`}
            disabled={loading}
          />
          <button type="submit" disabled={loading}>
            {loading ? "Connecting..." : "Start Call"}
          </button>
        </form>
        {error && <p className="error">{error}</p>}
        <div className="sample-phones">
          <p><strong>Sample numbers:</strong></p>
          <span onClick={() => setPhone("+1-555-123-4567")}>HealthFirst (NY)</span>
          <span onClick={() => setPhone("+1-555-987-6543")}>QuickMeds Rx (LA)</span>
          <span onClick={() => setPhone("+1-555-666-7777")}>MediCare Plus (IL)</span>
          <span onClick={() => setPhone("+1-800-000-0000")}>Unknown caller</span>
        </div>
      </div>
    </div>
  );
}
