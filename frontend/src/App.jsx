import { useState } from "react";
import PhoneEntry from "./components/PhoneEntry";
import ChatWindow from "./components/ChatWindow";
import { startSession } from "./api";
import "./App.css";

function App() {
  const [view, setView] = useState("phone");
  const [sessionId, setSessionId] = useState(null);
  const [greeting, setGreeting] = useState("");
  const [pharmacy, setPharmacy] = useState(null);

  const handleStart = async (phone) => {
    const data = await startSession(phone);
    setSessionId(data.session_id);
    setGreeting(data.greeting);
    setPharmacy(data.pharmacy);
    setView("chat");
  };

  const handleEndCall = () => {
    setSessionId(null);
    setGreeting("");
    setPharmacy(null);
    setView("phone");
  };

  return (
    <div className="app">
      {view === "phone" && <PhoneEntry onStart={handleStart} />}
      {view === "chat" && (
        <ChatWindow
          sessionId={sessionId}
          greeting={greeting}
          pharmacy={pharmacy}
          onEndCall={handleEndCall}
        />
      )}
    </div>
  );
}

export default App;
