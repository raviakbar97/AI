import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState("");

  useEffect(() => {
    const storedSessionId = localStorage.getItem("session_id");
    if (storedSessionId) {
      setSessionId(storedSessionId);
    } else {
      const newSessionId = generateSessionId();
      setSessionId(newSessionId);
      localStorage.setItem("session_id", newSessionId);
    }
  }, []);

  const generateSessionId = () => {
    return '_' + Math.random().toString(36).substr(2, 9);
  };

  const sendMessage = async () => {
    if (input.trim() === "") return;

    const response = await fetch("http://localhost:8000/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ prompt: input, session_id: sessionId })
    });
    const data = await response.json();
    setMessages([...messages, { text: input, user: true }, { text: data.response, user: false }]);
    setInput("");
  };

  return (
    <div className="App">
      <div className="chat-window">
        {messages.map((msg, index) => (
          <div key={index} className={msg.user ? "user-message" : "ai-message"}>
            {msg.text}
          </div>
        ))}
      </div>
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
        placeholder="Type your message here..."
      />
      <button onClick={sendMessage}>Send</button>
    </div>
  );
}

export default App;
