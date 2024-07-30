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

    try {
      const response = await fetch("https://opulent-guide-9rg9pw64v9x3wwj-8000.app.github.dev", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ prompt: input, session_id: sessionId })
      });

      if (!response.ok) {
        // Log error message if response is not ok
        const errorText = await response.text();
        console.error('Error:', errorText);
        return;
      }

      const data = await response.json();
      if (data.response) {
        setMessages([...messages, { text: input, user: true }, { text: data.response, user: false }]);
      } else {
        console.error('Unexpected response format:', data);
      }
      setInput("");
    } catch (error) {
      console.error('Error:', error);
    }
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
